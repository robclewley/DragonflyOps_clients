"""
ISSUE: Doesn't work if there are locked doors!
"""

from client_base import *

class WalkerBase(object):
    """The parent of all walkers"""

    def __init__(self, maze, position):
        """Takes a cell object from the maze in question
        NOTE: default must not be object if you want a map of any kind.
        """
        self._isDone = False
        self._maze = maze
        self._cell = position   # This is a cell object

    def step(self):
        """
        """
        raise NotImplementedError()

    def paint(self, cell, color):
        """Paint the current cell the indicated color"""
        self._maze.paint(cell, color)

    # The next three are depracated
    def mark_current(self, mark):
        """Mark the location with whatever data the child class needs.
        mark() should be a function that operates on the cell."""
        self.mark_this(self._cell, mark)

    def mark_this(self, cell, mark):
        """Mark the cell indicated. Cell must be a cell object."""
        x, y = cell.get_position()
        mark(self._map[x][y])

    def read_current(self):
        """Get the map data for the current cell."""
        return self.read_map(self._cell)

    def read_map(self, cell):
        """Return the info about the current cell"""
        x, y = cell.get_position()
        return self._map[x][y]


class Tremaux(WalkerBase):

    class Node(object):
        __slots__ = 'passages'

        def __init__(self):
            self.passages = set()

    def __init__(self, maze):
        super(Tremaux, self).__init__(maze, maze.start(), self.Node())
        #self._maze.clean()
        self._last = None # default

    def _is_junction(self, cell):
        return cell.count_halls() > 2

    def _is_visited(self, cell):
        return len(self.read_map(cell).passages) > 0

    def _backtracking(self, cell, last):
        return last in self.read_map(cell).passages

    def step(self):
        # This is so profoundly ugly

        if self._cell is self._maze.finish():
            self._isDone = True
            self.paint(self._cell, FOUND_COLOR)
            return

        # print self._cell.get_position()
        paths = self._cell.get_paths(last=self._last)
        # print paths
        random.shuffle(paths)

        if self._is_visited(self._cell):
            # We've been here before
            if self._backtracking(self._cell, self._last):
                # We are backtracking; see if there are any unvisited paths
                unvisited = filter(lambda c: not self._is_visited(c), paths)
                if len(unvisited) > 0:
                    self._last = self._cell
                    self._cell = unvisited.pop()
                else:
                    # There are no unvisited paths, continue backtracking
                    self.paint(self._cell, VISITED_COLOR)
                    # Find the path back
                    passages = self.read_map(self._cell).passages
                    unvisited = set(self._cell.get_paths()).difference(passages)
                    self._last = self._cell
                    self._cell = unvisited.pop()
            else:
                # We've looped to a previously visited cell; turn around
                self._cell, self._last = self._last, self._cell
        else:
            # New cell; move randomly
            if len(paths) > 0:
                # Not a deadend
                self.paint(self._cell, FOUND_COLOR)
                self._last = self._cell
                self._cell = paths.pop()
            else:
                # Is a deadend; backtrack
                self.paint(self._cell, VISITED_COLOR)
                self._cell, self._last = self._last, self._cell

        self.read_map(self._last).passages.add(self._cell)

def DFS(G, p, history=None):
    """
    depth first search: recursive
    """
    if history is None:
        history = set() # initialize history
    history.add(p) # visited p
    for u in G[p]:
        # explore neighbors
        if u not in history:
            DFS(G, u, history)
        # else skip already visited
    return history


# show objective
target_name = None
crit_objectives = tx('*O')['objectives']['critical']
for obj_text, state in crit_objectives.items():
    if 'Enter service room' in obj_text:
        target_name = obj_text[-4:]
        target_sector = target_name[0]
if target_name is None:
    raise ValueError("Failed to find definition of objective")


c = Client()
# alias this
tx = c.tx
mapdata = c.mapdata
sectors = c.sectors
graph = c.graph

def test_walk(backtrack_prob=0.9):
    pos = (0, 0)
    rx = tx(SCAN_CMD)
    #rx = tx(STATUS_CMD)
    path = [pos]
    last_dirn = None
    i = 0 # start not included as a step
    max_i = 10000
    # Tremaux's algorithm: depth-first search and the remaining path with
    # units having a count of 1 is the direct path
    while i < max_i:
        mapdata[pos] = rx
        print(rx['unit'])
        sector = rx['sector']
        auth_level = rx['access level']
        exits = rx['visuals']['exits']
        graph[rx['unit']] = copy(exits)
        dirns = list(exits.keys())
        for d in dirns:
            # if target available, go now!
            if target_name in exits[d][0]:
                path.append(new_pos_cands[d](pos[0], pos[1]))
                rx = tx(MOVE_CMD+d)
                rx = tx(SCAN_CMD)
                return path, i
        moved = False
        for d in dirns:
            new_sector = exits[d][0][0]
            if sector != new_sector and new_sector == target_name[0]:
                # move into correct sector
                path.append(new_pos_cands[d](pos[0], pos[1]))
                rx = tx(MOVE_CMD+d)
                rx = tx(SCAN_CMD)
                moved = True
                break
        is_second_pass = False # allow second pass in case MUST backtrack
        while not moved:
            candidates = []
            for d in dirns:
                # prefer candidate directions that lead to target sector
                unit_name = exits[d][0]
                if unit_name[0] == target_sector:
                    candidates.append(d)
            if len(candidates) == 0:
                candidates = dirns
            random.shuffle(candidates)
            for d in candidates:
                cand_pos = new_pos_cands[d](pos[0], pos[1])
                if last_dirn == opposite_dirn[d] and not is_second_pass:
                    # would be back-tracking
                    accept = len(candidates) == 1 or random.uniform(0,1) < backtrack_prob
                elif cand_pos in mapdata:
                    # prioritize unseen directions
                    accept = is_second_pass
                else:
                    accept = True
                if accept:
                    last_dirn = d
                    pos = cand_pos
                    path.append(pos)
                    new_name = exits[d][0]
                    rx = tx(MOVE_CMD+d)
                    rx = tx(SCAN_CMD)
                    moved = True
                    i += 1
                    break # for
                # else reject move, continue looking at neighbors
            if not moved:
                if is_second_pass:
                    raise ValueError("Failed to find neighbor to move to")
                else:
                    is_second_pass = True
    if i >= max_i:
        raise SystemError("Max random walk iterations reached without success")
    return path, i

path, num_steps = test_walk()
print(path)

##if not walker.is_done:
##    walker.step()