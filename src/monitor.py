#!/usr/bin/env python3

# Copyright © 2014  Mattias Andrée (maandree@member.fsf.org)
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import sys
from subprocess import Popen, PIPE

from curve import *

# /usr/lib
LIBDIR = 'bin'
sys.path.append(LIBDIR)

# /usr/libexec
LIBEXECDIR = 'bin'

randr_opened = None
vidmode_opened = None


def translate_to_integers():
    '''
    Translate the curves from float to integer
    
    @param  :(list<int>, list<int>, list<int>)  The red curve, the green curve and,
                                                the blue curve mapped to integers
    '''
    R_curve, G_curve, B_curve = [0] * i_size, [0] * i_size, [0] * i_size
    for i_curve, o_curve in ((r_curve, R_curve), (g_curve, G_curve), (b_curve, B_curve)):
        for i in range(i_size):
            o_curve[i] = int(i_curve[i] * (o_size - 1) + 0.5)
            if clip_result:
                o_curve[i] = min(max(0, o_curve[i]), (o_size - 1))
    return (R_curve, G_curve, B_curve)    


def close_c_bindings():
    '''
    Close all C bindings and let them free resources and close connections
    '''
    global randr_opened, vidmode_opened
    if randr_opened is not None:
        from blueshift_randr import randr_close
        randr_opened = None
        randr_close()
    if vidmode_opened is not None:
        from blueshift_vidmode import vidmode_close
        vidmode_opened = None
        vidmode_close()


def randr_get(crtc = 0, screen = 0):
    '''
    Gets the current colour curves using the X11 extension RandR
    
    @param   crtc:int    The CRTC of the monitor to read from
    @param   screen:int  The screen that the monitor belong to
    @return  :()→void    Function to invoke to apply the curves that was used when this function was invoked
    '''
    from blueshift_randr import randr_open, randr_read, randr_close
    global randr_opened
    if (randr_opened is None) or not (randr_opened == screen):
        if randr_opened is not None:
            randr_close()
        if randr_open(screen) == 0:
            randr_opened = screen
        else:
            sys.exit(1)
    (r, g, b) = randr_read(crtc)
    r = [y / 65535 for y in r]
    g = [y / 65535 for y in g]
    b = [y / 65535 for y in b]
    def fcurve(R_curve, G_curve, B_curve):
        for curve, cur in curves(R_curve, G_curve, B_curve):
            for i in range(i_size):
                y = int(curve[i] * (len(cur) - 1) + 0.5)
                y = min(max(0, y), len(cur) - 1)
                curve[i] = cur[y]
    return lambda : fcurve(r, g, b)


def vidmode_get(crtc = 0, screen = 0):
    '''
    Gets the current colour curves using the X11 extension VidMode
    
    @param   crtc:int    The CRTC of the monitor to read from
    @param   screen:int  The screen that the monitor belong to
    @return  :()→void    Function to invoke to apply the curves that was used when this function was invoked
    '''
    from blueshift_vidmode import vidmode_open, vidmode_read, vidmode_close
    global vidmode_opened
    if (vidmode_opened is None) or not (vidmode_opened == screen):
        if vidmode_opened is not None:
            vidmode_close()
        if vidmode_open(screen) == 0:
            vidmode_opened = screen
        else:
            sys.exit(1)
    (r, g, b) = vidmode_read(crtc)
    r = [y / 65535 for y in r]
    g = [y / 65535 for y in g]
    b = [y / 65535 for y in b]
    def fcurve(R_curve, G_curve, B_curve):
        for curve, cur in curves(R_curve, G_curve, B_curve):
            for i in range(i_size):
                y = int(curve[i] * (len(cur) - 1) + 0.5)
                y = min(max(0, y), len(cur) - 1)
                curve[i] = cur[y]
    return lambda : fcurve(r, g, b)


def randr(*crtcs, screen = 0):
    '''
    Applies colour curves using the X11 extension RandR
    
    @param  crtcs:*int  The CRT controllers to use, all are used if none are specified
    @param  screen:int  The screen that the monitors belong to
    '''
    from blueshift_randr import randr_open, randr_apply, randr_close
    global randr_opened
    crtcs = sum([1 << i for i in list(crtcs)])
    if crtcs == 0:
        crtcs = (1 << 64) - 1
    
    (R_curve, G_curve, B_curve) = translate_to_integers()
    if (randr_opened is None) or not (randr_opened == screen):
        if randr_opened is not None:
            randr_close()
        if randr_open(screen) == 0:
            randr_opened = screen
        else:
            sys.exit(1)
    try:
        if not randr_apply(crtcs, R_curve, G_curve, B_curve) == 0:
            sys.exit(1)
    except OverflowError:
        pass # Happens on exit by TERM signal


def vidmode(*crtcs, screen = 0):
    '''
    Applies colour curves using the X11 extension VidMode
    
    @param  crtcs:*int  The CRT controllers to use, all are used if none are specified
    @param  screen:int  The screen that the monitors belong to
    '''
    from blueshift_vidmode import vidmode_open, vidmode_apply, vidmode_close
    global vidmode_opened
    crtcs = sum([1 << i for i in list(crtcs)])
    if crtcs == 0:
        crtcs = (1 << 64) - 1
    
    (R_curve, G_curve, B_curve) = translate_to_integers()
    if (vidmode_opened is None) or not (vidmode_opened == screen):
        if vidmode_opened is not None:
            vidmode_close()
        if vidmode_open(screen) == 0:
            vidmode_opened = screen
        else:
            sys.exit(1)
    try:
        if not vidmode_apply(crtcs, R_curve, G_curve, B_curve) == 0:
            sys.exit(1)
    except OverflowError:
        pass # Happens on exit by TERM signal


def print_curves(*crtcs, screen = 0, compact = False):
    '''
    Prints the curves to stdout
    
    @param  crtcs:*int    Dummy parameter
    @param  screen:int    Dummy parameter
    @param  compact:bool  Whether to print in compact form
    '''
    (R_curve, G_curve, B_curve) = translate_to_integers()
    if compact:
        for curve in (R_curve, G_curve, B_curve):
            print('[', end = '')
            last = None
            count = 0
            for i in range(i_size):
                if curve[i] == last:
                    count += 1
                else:
                    if last is not None:
                        print('%i {%i}, ' % (last, count), end = '')
                    last = curve[i]
                    count = 1
            print('%i {%i}]' % (last, count))
    else:
        print(R_curve)
        print(G_curve)
        print(B_curve)



class Screens:
    '''
    Information about all screens
    '''
    def __init__(self):
        '''
        Constructor
        '''
        self.screens = None
    
    def find_by_crtc(self, index):
        '''
        Find output by CRTC index
        
        @param   index:int?     The CRTC index
        @return  :list<Output>  Matching outputs
        '''
        rc = []
        for screen in self.screens:
            rc += screen.find_by_crtc(index)
        return rc
    
    def find_by_name(self, name):
        '''
        Find output by name
        
        @param   name:str       The name of the output
        @return  :list<Output>  Matching outputs
        '''
        rc = []
        for screen in self.screens:
            rc += screen.find_by_name(name)
        return rc
    
    def find_by_size(self, widthmm, heigthmm):
        '''
        Find output by physical size
        
        @param   widthmm:int?   The physical width, measured in millimetres, of the monitor
        @param   heightmm:int?  The physical height, measured in millimetres, of the monitor
        @return  :list<Output>  Matching outputs
        '''
        rc = []
        for screen in self.screens:
            rc += screen.find_by_size(widthmm, heigthmm)
        return rc
    
    def find_by_connected(self, status):
        '''
        Find output by connection status
        
        @param   status:bool    Whether the output should be connected or not
        @return  :list<Output>  Matching outputs
        '''
        rc = []
        for screen in self.screens:
            rc += screen.find_by_connected(status)
        return rc
    
    def find_by_edid(self, edid):
        '''
        Find output by extended display identification data
        
        @param   edid:str?      The extended display identification data of the monitor
        @return  :list<Output>  Matching outputs
        '''
        rc = []
        for screen in self.screens:
            rc += screen.find_by_edid(edid)
        return rc
    
    def __contains__(self, other):
        return other in self.screens
    def __getitem__(self, index):
        return self.screens[index]
    def __iter__(self):
        return iter(self.screens)
    def __len__(self):
        return len(self.screens)
    def __reversed__(self):
        return reversed(self.screens)
    def __setitem__(self, index, item):
        self.screens[index] = item
    def __repr__(self):
        return repr(self.screens)

class Screen:
    '''
    Screen information
    
    @variable  crtc_count:int       The number of CRTC:s
    @variable  output:list<Output>  List of outputs
    '''
    def __init__(self):
        '''
        Constructor
        '''
        self.crtc_count = 0
        self.outputs = []
    
    def find_by_crtc(self, index):
        '''
        Find output by CRTC index
        
        @param   index:int?     The CRTC index
        @return  :list<Output>  Matching outputs
        '''
        rc = []
        for i in range(len(self.outputs)):
            if self.outputs[i].crtc == index:
                rc.append(self.outputs[i])
        return rc
    
    def find_by_name(self, name):
        '''
        Find output by name
        
        @param   name:str       The name of the output
        @return  :list<Output>  Matching outputs
        '''
        rc = []
        for i in range(len(self.outputs)):
            if self.outputs[i].name == name:
                rc.append(self.outputs[i])
        return rc
    
    def find_by_size(self, widthmm, heightmm):
        '''
        Find output by physical size
        
        @param   widthmm:int?   The physical width, measured in millimetres, of the monitor
        @param   heightmm:int?  The physical height, measured in millimetres, of the monitor
        @return  :list<Output>  Matching outputs
        '''
        rc = []
        for i in range(len(self.outputs)):
            if self.outputs[i].widthmm == widthmm:
                if self.outputs[i].heightmm == heightmm:
                    rc.append(self.outputs[i])
        return rc
    
    def find_by_connected(self, status):
        '''
        Find output by connection status
        
        @param   status:bool    Whether the output should be connected or not
        @return  :list<Output>  Matching outputs
        '''
        rc = []
        for i in range(len(self.outputs)):
            if self.outputs[i].connected == status:
                rc.append(self.outputs[i])
        return rc
    
    def find_by_edid(self, edid):
        '''
        Find output by extended display identification data
        
        @param   edid:str?      The extended display identification data of the monitor
        @return  :list<Output>  Matching outputs
        '''
        rc = []
        for i in range(len(self.outputs)):
            if self.outputs[i].edid == edid:
                rc.append(self.outputs[i])
        return rc
    
    def __repr__(self):
        '''
        Return a string representation of the instance
        '''
        return '[CRTC count: %i, Outputs: %s]' % (self.crtc_count, repr(self.outputs))

class Output:
    '''
    Output information
    
    @variable  name:str        The name of the output
    @variable  connected:bool  Whether the outout is known to be connected
    @variable  widthmm:int?    The physical width of the monitor, measured in millimetres, `None` if unknown or not connected
    @variable  heigthmm:int?   The physical height of the monitor, measured in millimetres, `None` if unknown or not connected
    @variable  crtc:int?       The CRTC index, `None` if not connected
    @variable  screen:int?     The screen index, `None` if none
    @variable  edid:str?       Extended display identification data, `None` if none
    '''
    def __init__(self):
        '''
        Constructor
        '''
        self.name = None
        self.connected = False
        self.widthmm = None
        self.heightmm = None
        self.crtc = None
        self.screen = None
        self.edid = None
    
    def __repr__(self):
        '''
        Return a string representation of the instance
        '''
        rc = [self.name, self.connected, self.widthmm, self.heightmm, self.crtc, self.screen, self.edid]
        rc = tuple(rc[:1] + list(map(lambda x : repr(x), rc[1 : -1])) + [str(rc[-1])])
        rc = '[Name: %s, Connected: %s, Width: %s, Height: %s, CRTC: %s, Screen: %s, EDID: %s]' % rc
        return rc

def list_screens():
    '''
    Retrieve informantion about all screens, outputs and CRTC:s
    
    @return  :Screens  An instance of a datastructure with the relevant information
    '''
    process = Popen([LIBEXECDIR + "/blueshift_idcrtc"], stdout = PIPE)
    lines = process.communicate()[0].decode('utf-8', 'error').split('\n')
    lines = [line.strip() for line in lines]
    screens, screen_i, screen, output = None, None, None, None
    for line in lines:
        if line.startswith('Screen count: '):
            screens = [None] * int(line[len('Screen count: '):])
        elif line.startswith('Screen: '):
            screen_i = int(line[len('Screen: '):])
            screen = Screen()
            screens[screen_i] = screen
        elif line.startswith('CRTC count: '):
            screen.crtc_count = int(line[len('CRTC count: '):])
        elif line.startswith('Output count: '):
            screen.outputs = [None] * int(line[len('Output count: '):])
        elif line.startswith('Output: '):
            output_i = int(line[len('Output: '):])
            output = Output()
            output.screen = screen_i
            screen.outputs[output_i] = output
        elif line.startswith('Name: '):
            output.name = line[len('Name: '):]
        elif line.startswith('Connection: '):
            output.connected = line[len('Connection: '):] == 'connected'
        elif line.startswith('Size: '):
            output.widthmm, output.heightmm = [int(x) for x in line[len('Size: '):].split(' ')]
            if (output.widthmm <= 0) or (output.heightmm <= 0):
                output.widthmm, output.heightmm = None, None
        elif line.startswith('CRTC: '):
            output.crtc = int(line[len('CRTC: '):])
        elif line.startswith('EDID: '):
            output.edid = line[len('EDID: '):]
    rc = Screens()
    rc.screens = screens
    return rc

