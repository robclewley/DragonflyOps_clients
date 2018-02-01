from __future__ import print_function #, unicode_literals
from collections import defaultdict
from matplotlib import pyplot as plt
from copy import copy
#import pprint
#import curses
import pyaml
import sys
import client_base as cb

#pp = pprint.PrettyPrinter(indent=2)

global fig
fig = plt.figure(1)
plt.suptitle("Map of facility (dots are locations)", size=14)
plt.autoscale(enable=False, tight=False)
ax = plt.gca()

def sign(x):
    if x < 0:
        return -1
    else:
        return 1

class Extents(object):
    """Utility class to auto-calculate extended limits to the growing map.
    """
    def __init__(self, extra_fac=0.1):
        self.x0 = self.x1 = 0
        self.y0 = self.y1 = 0
        self.extra_fac = extra_fac

    def __call__(self, x, y):
        """Update extents from an (x,y) point.
        """
        if x < self.x0:
            self.x0 = x
        elif x > self.x1:
            self.x1 = x
        if y < self.y0:
            self.y0 = y
        elif y > self.y1:
            self.y1 = y

    def get(self):
        return [(self.x0-self.extra_fac,
                 self.x1+self.extra_fac),
                (self.y0-self.extra_fac,
                 self.y1+self.extra_fac)
                ]

class GClient(cb.Client):
    """
    Always runs scan on arrival if room not new
    """
    def __init__(self):
        self.loc_markers = defaultdict(bool) # default value is False
        self.loc_reds = defaultdict(bool)
        self.plot_data = {}
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
                        self.current_loc = res['unit']
                else:
                    # reuse old visuals assuming nothing has changed!
                    res = self.mapdata[res['unit']]
                    self.current_loc = res['unit']
            self.graph_it(res['unit'])
        return res

    def graph_it(self, unit_highlight):
        ax.cla()
        ax.axis('off')
        ax.get_xaxis().set_ticks([])
        ax.get_yaxis().set_ticks([])

        extents = Extents()

        seen = set()
        visited = set()
        q = [(self.graph.keys()[0], (0,0))]
        self.plot_data = pd = {}

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
                    pd[unit_name] = ax.plot(x, y, col+'o', markersize=10)[0]
                    annot = ax.annotate(unit_name, xy=(x+0.15,y+0.15), xytext=(x+0.4,y+0.4), textcoords="offset points",
                                                    bbox=dict(boxstyle="round", fc="w"),
                                                    arrowprops=dict(arrowstyle="->"))
                    annot.set_visible(True)
                if unit_highlight == unit_name:
                    ax.plot(x, y, 'go', markersize=8)
                if self.loc_markers[unit_name]:
                    ax.plot(x, y, 'yx', markersize=11)
                extents(x,y)
                extents(x+0.4, y+0.4)
            for dirn, (u_name, desc) in exit_data.items():
                dx, dy = cb.dirn_lookup[dirn]
                if u_name in visited:
                    continue
                else:
                    q.append((u_name, (x+dx, y+dy)))
                    ax.plot( (x, x+dx), (y, y+dy), 'k-', lw=0.2 )
                    extents(x+dx, y+dy)
        assert len(visited) == len(self.mapdata)
        x_limits, y_limits = extents.get()
        ax.set_xlim(x_limits)
        ax.set_ylim(y_limits)
        ax.set_aspect('equal')
        plt.draw()
        plt.show()

# ==================================

def run(c, res):
    while True:
        print("Use 'x' and 'r' local commands to toggle markers (cross or red color) at current map location\n")
        #print("Direction? ", end='')
        #key = pad.getch()
        #key = getch()
        try:
            response = raw_input('Direction? (or enter a full command, or ^D to quit) ')
        except EOFError:
            print("\n\n***** Quitting interface")
            return
        if response.upper() in ('N', 'S', 'E', 'W'):
            res = c.tx('!M'+response.upper())
            #pp.pprint(res)
            print(pyaml.dump(res))
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
            #pp.pprint(c.tx(response))
            print(pyaml.dump(c.tx(response)))
            sys.stdout.flush()


if __name__ == '__main__':
    #curses.initscr()
    c = GClient()
    try:
        c.connect()
    except:
        print("No drone to activate? Did you deploy?")
    else:
        print(" ***** All movement commands 'n', 's','e', 'w' to unvisited locations will")
        print("                automatically be followed by a scan")

        res = c.tx('!S') # must scan to ensure the door name data is stored in graph
        #pp.pprint(res)
        print(pyaml.dump(res))
        c.visit(res)
        c.graph_it(res['unit'])
        #pad = curses.newpad(200,200)
        #pad.timeout(0)
        run(c, res)

