from __future__ import print_function #, unicode_literals
from collections import defaultdict
from matplotlib import pyplot as plt
from copy import copy
import pprint
#import curses
import sys
import client_base as cb

pp = pprint.PrettyPrinter(indent=2)

global fig
fig = plt.figure(1)
ax = plt.gca()

class GClient(cb.Client):
    """
    Always runs scan on arrival if room not new
    """
    def __init__(self):
        self.loc_markers = defaultdict(bool) # default value is False
        self.loc_reds = defaultdict(bool)
        super(GClient, self).__init__()

    def visit(self, rx):
        self.graph[rx['unit']] = copy(rx['visuals']['exits'])
        self.mapdata[rx['unit']] = rx

    def tx(self, msg):
        res = super(GClient, self).tx(msg)
        if msg.startswith(cb.MOVE_CMD) and 'ERROR' not in res:
            if 'unit' not in res:
                return res
            else:
                if res['unit'] not in self.ever_seen:
                    res = super(GClient, self).tx(cb.SCAN_CMD)
                    try:
                        self.ever_seen.add(res['unit'])
                    except KeyError:
                        return res
                    else:
                        self.visit(res)
                else:
                    # reuse old visuals assuming nothing has changed!
                    res = self.mapdata[res['unit']]
            self.graph_it(res['unit'])
        return res

    def graph_it(self, unit_highlight):
        ax.cla()

        seen = set()
        visited = set()
        q = [(self.graph.keys()[0], (0,0))]
#        print(self.graph[self.graph.keys()[0]])

        while len(q) > 0:
            unit_name, (x,y) = q.pop(0)
            try:
                exit_data = self.graph[unit_name]
            except:
                # no graph available for this location yet
                continue
            else:
                visited.add(unit_name)
            if unit_name not in seen:
                seen.add(unit_name)
                if self.loc_reds[unit_name]:
                    col = 'r'
                else:
                    col = 'k'
                ax.plot(x, y, col+'o', markersize=9)
                if unit_highlight == unit_name:
                    ax.plot(x, y, 'go', markersize=5)
                if self.loc_markers[unit_name]:
                    ax.plot(x, y, 'yx', markersize=9)
            for dirn, (u_name, desc) in exit_data.items():
                dx, dy = cb.dirn_lookup[dirn]
                if u_name in visited:
                    continue
                else:
                    q.append((u_name, (x+dx, y+dy)))
                    ax.plot( (x, x+dx), (y, y+dy), 'k-', lw=0.1 )

        assert len(visited) == len(self.mapdata)
        plt.draw()
        plt.show()

# ==================================

def run(c, res):
    while True:
        #print("Direction? ", end='')
        #key = pad.getch()
        #key = getch()
        response = raw_input('Direction? (or enter full command or ^D to break) ')
        if response.upper() in ('N', 'S', 'E', 'W'):
            res = c.tx('!M'+response.upper())
            pp.pprint(res)
            sys.stdout.flush()
        elif response.upper() == 'X':
            # toggle X marker at location
            c.loc_markers[res['unit']] = not c.loc_markers[res['unit']]
            c.graph_it(res['unit'])
        elif response.upper() == 'R':
            c.loc_reds[res['unit']] = not c.loc_reds[res['unit']]
            c.graph_it(res['unit'])
        elif response != "":
            # assume a full, regular command
            pp.pprint(c.tx(response))
            sys.stdout.flush()


if __name__ == '__main__':
    #curses.initscr()
    c = GClient()
    c.connect()
    res = c.tx('!S') # must scan to ensure the door name data is stored in graph
    pp.pprint(res)
    c.visit(res)
    c.graph_it(res['unit'])
    #pad = curses.newpad(200,200)
    #pad.timeout(0)
    run(c, res)

