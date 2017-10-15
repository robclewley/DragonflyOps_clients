from __future__ import print_function
import json
import socket
from copy import copy
import random

# -----------------------------------

dirn_lookup = {'N': (0,1),
               'S': (0,-1),
               'W': (-1,0),
               'E': (1,0),
               'NW': (-1,1),
               'NE': (1,1),
               'SW': (-1,-1),
               'SE': (1,-1)}
dirn_lookup_inv = dict([(b,a) for (a,b) in dirn_lookup.items()])

opposite_dirn = {'W': 'E', 'N': 'S', 'E': 'W', 'S': 'N',
                 'NW': 'SE', 'SE': 'NW', 'NE': 'SW', 'SW': 'NE'}

perp_dirns = {'W': ('N', 'S'), 'E': ('N', 'S'), 'N': ('E', 'W'), 'S': ('E', 'W')}

# extra 4 diagonal directions only used for local density scanning
new_pos_cands = {'W': lambda x, y:(x-1, y), 'N': lambda x, y:(x, y+1),
                 'E': lambda x, y:(x+1, y), 'S': lambda x, y:(x, y-1),
                 'SW': lambda x, y:(x-1, y-1), 'SE': lambda x, y:(x+1, y-1),
                 'NW': lambda x, y:(x-1, y+1), 'NE': lambda x, y:(x+1, y+1)}
# use as x, y <-- new_pos_cands[dirn_str](x,y)


# =========================

MOVE_CMD = '!M'
SCAN_CMD = '!S'
STATUS_CMD = '!?'

status_keys = ['unit', 'sector', 'name', 'access level', 'visuals', 'achievements']

class Client(object):
    def __init__(self):
        self.sectors = set()
        self.mapdata = {} # maps pos to 'unit', 'sector', 'name', 'access level', 'visuals'
        self.graph = {} # pos connecting to pos (symmetric)
        self.ever_seen = set()

    def connect(self, host="127.0.0.1", port=5555):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.host = host
        self.port = port
        self.sock.connect((host,port))
        discard_data = self.sock.recv(1024).decode()
        # toggle prompt OFF
        self.tx('*P')

    def tx(self, msg):
        self.sock.send(msg.encode())
        data = self.sock.recv(1024).decode()
        rx = data.split('\n')
        for i, rstr in enumerate(rx):
            try:
                r = json.loads(rstr)
            except ValueError:
                pass
            else:
                rx = r
                #print(r)
        return copy(rx)

try:
    import msvcrt
except ImportError:
    # Unix and OS X
    import sys, tty, termios
    def getch():
        """Blocking call to get a single character from the prompt (without carriage return)
        ... without using curses (but use curses if you build something more sophisticated)
        """
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch
else:
    # Windows only
    def getch():
        """Blocking call to get a single character from the prompt (without carriage return)
        ... without using curses (but use curses if you build something more sophisticated)
        """
        return msvcrt.getch()
