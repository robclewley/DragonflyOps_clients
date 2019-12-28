from __future__ import print_function
import json
import socket
import subprocess
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

MOVE_CMD = 'move ' # trailing space important
SCAN_CMD = 'scan'
STATUS_CMD = 'status'

status_keys = ['unit', 'sector', 'name', 'visuals', 'achievements']

class Client(object):
    MAX_PACKET_SIZE = 50000 # assumption, bad for larger files

    def __init__(self):
        self.sectors = set()
        self.mapdata = {} # maps pos to 'unit', 'sector', 'name', 'access level', 'visuals'
        self.graph = {} # pos connecting to pos (symmetric)
        self.graph_simple = {}
        self.ever_seen = set()
        self.current_loc = None
        self.sock = self.host = self.port = None

    def connect(self, host="127.0.0.1", port=5555):
        """Connect to game server
        """
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.host = host
        self.port = port
        self.sock.connect((host,port))
        discard_data = self.sock.recv(self.MAX_PACKET_SIZE).decode()

    def tx(self, msg):
        """Transmit request to server
        """
        self.sock.send((msg+"\n").encode())
        data = self.sock.recv(self.MAX_PACKET_SIZE).decode()
        rx = data.split('\n')
        for i, rstr in enumerate(rx):
            try:
                r = json.loads(rstr)
            except ValueError:
                pass
            else:
                rx = r
        return copy(rx)

def run_command(com, **kwargs):
    """
    Wrap this in your own functions, especially if you need to use curl
    """
    try:
        use_curl = kwargs.pop('use_curl')
    except:
        use_curl = False

    if use_curl:
        full_com = com.replace(" ", "%20")
        try:
            host = kwargs.pop('host')
        except KeyError:
            host = "localhost"
        try:
            port = kwargs.pop('port')
        except KeyError:
            # use 5000 for localhost HTML port
            port = 5000
        if port is None:
            port_str = ""
        else:
            port_str = ":"+str(port)
        url = "{}{}/{}".format(host,port_str,full_com)
        res = json.loads(subprocess.check_output(["curl", url]))
        check = 0
    else:
        if c.sock is None:
            try:
                host = kwargs.pop('host')
            except KeyError:
                host = "localhost"
            try:
                port = kwargs.pop('port')
            except KeyError:
                port = 5555
            c.connect(host, port)
        res = c.tx(com)
        check = -1
    
    try:
        check_ack = kwargs.pop("check_ack")
    except KeyError:
        pass
    else:
        if check_ack:
            check = list(res.keys())[0] == "ACK"
    try:
        check_err = kwargs.pop("check_err")
    except KeyError:
        pass
    else:
        if check_err:
            check = list(res.keys())[0] == "ERROR"
    if check == 0:
        return str(res)
    elif check == -1:
        return list(res.values())[0]
    else:
        return list(res.values())[0], check
    
# Utility function for your own REPL
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
