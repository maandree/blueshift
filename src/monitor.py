#!/usr/bin/env python3

# Copyright © 2014, 2015, 2016, 2017  Mattias Andrée (m@maandree.se)
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

# This module is deprecated!

import sys

from aux import *
from curve import *
from output import EDID



cached_displays = {}


def get_gamma(crtc = 0, screen = 0, display = None, *, method = None):
    '''
    Gets the current colour curves
    
    @param   crtc:int      The CRTC of the monitor to read from
    @param   screen:int    The screen to which the monitors belong
    @param   display:str?  The display to which to connect, `None` for current display
    @param   method:str?   The adjustment method
    @return  :()→void      Function to invoke to apply the curves that was used when this function was invoked
    '''
    import output
    if not get_gamma.warned:
        get_gamma.warned = True
        print('get_gamma() is deprecated', file = sys.stderr)
    if (method, display) not in cached_displays:
        cached_displays[(method, display)] = output.get_outputs(method = method, display = display)
    crtc = cached_displays[(method, display)].screens[screen].crtcs[crtc]
    ramps = crtc.get_gamma()
    return ramps_to_function(ramps.red, ramps.green, ramps.blue)
get_gamma.warned = False


def set_gamma(*crtcs, screen = 0, display = None, method = None):
    '''
    Applies colour curves
    
    @param  crtcs:*int    The CRT controllers to use, all are used if none are specified
    @param  screen:int    The screen to which the monitors belong
    @param  display:str?  The display to which to connect, `None` for current display
    @param  method:str?   The adjustment method
    '''
    import output
    if not set_gamma.warned:
        set_gamma.warned = True
        print('set_gamma() is deprecated', file = sys.stderr)
    if (method, display) not in cached_displays:
        cached_displays[(method, display)] = output.get_outputs(method = method, display = display)
    screen = cached_displays[(method, display)].screens[screen]
    ramps = output.Ramps(None, depth = -1, size = i_size)
    ramps.red[:]   = r_curve
    ramps.green[:] = g_curve
    ramps.blue[:]  = b_curve
    for crtc in range(len(screen.crtcs)) if len(crtcs) == 0 else crtcs:
        crtc = screen.crtcs[crtc]
        size = (crtc.red_gamma_size, crtc.green_gamma_size, crtc.blue_gamma_size)
        crtc.set_gamma(ramps.copy(depth = crtc.gamma_depth, size = size))
set_gamma.warned = False


def randr_get(crtc = 0, screen = 0, display = None):
    '''
    Gets the current colour curves using the X11 extension RandR
    
    @param   crtc:int      The CRTC of the monitor to read from
    @param   screen:int    The screen to which the monitors belong
    @param   display:str?  The display to which to connect, `None` for current display
    @return  :()→void      Function to invoke to apply the curves that was used when this function was invoked
    '''
    if not randr_get.warned:
        randr_get.warned = True
        print('randr_get() is deprecated', file = sys.stderr)
    return get_gamma(crtc, screen, display, method = 'randr')
randr_get.warned = False

def vidmode_get(crtc = 0, screen = 0, display = None):
    '''
    Gets the current colour curves using the X11 extension VidMode
    
    @param   crtc:int      The CRTC of the monitor to read from, dummy parameter
    @param   screen:int    The screen to which the monitors belong
    @param   display:str?  The display to which to connect, `None` for current display
    @return  :()→void      Function to invoke to apply the curves that was used when this function was invoked
    '''
    if not vidmode_get.warned:
        vidmode_get.warned = True
        print('vidmode_get() is deprecated', file = sys.stderr)
    return get_gamma(crtc, screen, display, method = 'vidmode')
vidmode_get.warned = False

def drm_get(crtc = 0, screen = 0, display = None):
    '''
    Gets the current colour curves using DRM
    
    @param   crtc:int      The CRTC of the monitor to read from
    @param   screen:int    The graphics card to which the monitors belong, named `screen` for compatibility with `randr_get` and `vidmode_get`
    @param   display:str?  Dummy parameter for compatibility with `randr_get` and `vidmode_get`
    @return  :()→void      Function to invoke to apply the curves that was used when this function was invoked
    '''
    if not drm_get.warned:
        drm_get.warned = True
        print('drm_get() is deprecated', file = sys.stderr)
    return get_gamma(crtc, screen, display, method = 'drm')
drm_get.warned = False

def w32gdi_get(crtc = 0, screen = 0, display = None):
    '''
    Gets the current colour curves using W32 GDI
    
    @param   crtc:int      The CRTC of the monitor to read from
    @param   screen:int    Dummy parameter for compatibility with `randr_get`, `vidmode_get` and `drm_get`
    @param   display:str?  Dummy parameter for compatibility with `randr_get` and `vidmode_get`
    @return  :()→void      Function to invoke to apply the curves that was used when this function was invoked
    '''
    if not w32gdi_get.warned:
        w32gdi_get.warned = True
        print('w32gdi_get() is deprecated', file = sys.stderr)
    return get_gamma(crtc, screen, display, method = 'w32gdi')
w32gdi_get.warned = False

def quartz_get(crtc = 0, screen = 0, display = None):
    '''
    Gets the current colour curves using Quartz
    
    @param   crtc:int      The CRTC of the monitor to read from
    @param   screen:int    Dummy parameter for compatibility with `randr_get`, `vidmode_get` and `drm_get`
    @param   display:str?  Dummy parameter for compatibility with `randr_get` and `vidmode_get`
    @return  :()→void      Function to invoke to apply the curves that was used when this function was invoked
    '''
    if not quartz_get.warned:
        quartz_get.warned = True
        print('quartz_get() is deprecated', file = sys.stderr)
    return get_gamma(crtc, screen, display, method = 'quartz')
quartz_get.warned = False


def randr(*crtcs, screen = 0, display = None):
    '''
    Applies colour curves using the X11 extension RandR
    
    @param  crtcs:*int    The CRT controllers to use, all are used if none are specified
    @param  screen:int    The screen to which the monitors belong
    @param  display:str?  The display to which to connect, `None` for current display
    '''
    if not randr.warned:
        randr.warned = True
        print('randr() is deprecated', file = sys.stderr)
    set_gamma(*crtcs, screen = screen, display = display, method = 'randr')
randr.warned = False

def vidmode(*crtcs, screen = 0, display = None):
    '''
    Applies colour curves using the X11 extension VidMode
    
    @param  crtcs:*int    The CRT controllers to use, all are used if none are specified, dummy parameter
    @param  screen:int    The screen to which the monitors belong
    @param  display:str?  The display to which to connect, `None` for current display
    '''
    if not vidmode.warned:
        vidmode.warned = True
        print('vidmode() is deprecated', file = sys.stderr)
    set_gamma(*crtcs, screen = screen, display = display, method = 'vidmode')
vidmode.warned = False

def drm(*crtcs, screen = 0, display = None):
    '''
    Applies colour curves using DRM
    
    @param  crtcs:*int    The CRT controllers to use, all are used if none are specified
    @param  screen:int    The graphics card to which the monitors belong,
                          named `screen` for compatibility with `randr` and `vidmode`
    @param  display:str?  Dummy parameter for compatibility with `randr` and `vidmode`
    '''
    if not drm.warned:
        drm.warned = True
        print('drm() is deprecated', file = sys.stderr)
    set_gamma(*crtcs, screen = screen, display = display, method = 'drm')
drm.warned = False

def w32gdi(*crtcs, screen = 0, display = None):
    '''
    Applies colour curves using W32 GDI
    
    @param  crtcs:*int    The CRT controllers to use, all are used if none are specified
    @param  screen:int    Dummy parameter for compatibility with `randr`, `vidmode` and `drm`
    @param  display:str?  Dummy parameter for compatibility with `randr` and `vidmode`
    '''
    if not w32gdi.warned:
        w32gdi.warned = True
        print('w32gdi() is deprecated', file = sys.stderr)
    set_gamma(*crtcs, screen = screen, display = display, method = 'w32gdi')
w32gdi.warned = False

def quartz(*crtcs, screen = 0, display = None):
    '''
    Applies colour curves using Quartz
    
    @param  crtcs:*int    The CRT controllers to use, all are used if none are specified
    @param  screen:int    Dummy parameter for compatibility with `randr`, `vidmode` and `drm`
    @param  display:str?  Dummy parameter for compatibility with `randr` and `vidmode`
    '''
    if not quartz.warned:
        quartz.warned = True
        print('quartz() is deprecated', file = sys.stderr)
    set_gamma(*crtcs, screen = screen, display = display, method = 'quartz')
quartz.warned = False


def print_curves(*crtcs, screen = 0, display = None, compact = False):
    '''
    Prints the curves to stdout
    
    @param  crtcs:*int    Dummy parameter
    @param  screen:int    Dummy parameter
    @param  display:str?  Dummy parameter
    @param  compact:bool  Whether to print in compact form
    '''
    if not print_curves.warned:
        print_curves.warned = True
        print('print_curves() is deprecated', file = sys.stderr)
    # Convert curves to [0, 0xFFFF] integer lists
    (R_curve, G_curve, B_curve) = translate_to_integers()
    if compact:
        # Print each colour curve with run-length encoding
        for curve in (R_curve, G_curve, B_curve):
            # Print beginning
            print('[', end = '')
            last, count = None, 0
            for i in range(i_size):
                if curve[i] == last:
                    # Count repetition
                    count += 1
                else:
                    # Print value
                    if last is not None:
                        print('%i {%i}, ' % (last, count), end = '')
                    # Store new value
                    last = curve[i]
                    # Restart counter
                    count = 1
            # Print last value and ending
            print('%i {%i}]' % (last, count))
    else:
        # Print the red colour curve
        print(R_curve)
        # Print the green colour curve
        print(G_curve)
        # Print the blue colour curve
        print(B_curve)
print_curves.warned = False



class Screens:
    '''
    Information about all screens
    '''
    def __init__(self):
        '''
        Constructor
        '''
        self.screens = None

    
    def __find(self, f):
        '''
        Find monitors in each screen
        
        @param   f:(Screen)→list<Output>  Function that for one screen find all desired monitors in it
        @return  :list<Output>            All desired monitors
        '''
        rc = []
        for screen in self.screens:
            rc += f(screen)
        return rc
    
    def find_by_crtc(self, index):
        '''
        Find output by CRTC index
        
        @param   index:int?     The CRTC index
        @return  :list<Output>  Matching outputs
        '''
        return self.__find(lambda screen : screen.find_by_crtc(index))
    
    def find_by_name(self, name):
        '''
        Find output by name
        
        @param   name:str       The name of the output
        @return  :list<Output>  Matching outputs
        '''
        return self.__find(lambda screen : screen.find_by_name(name))
    
    def find_by_size(self, widthmm, heigthmm):
        '''
        Find output by physical size
        
        @param   widthmm:int?   The physical width, measured in millimetres, of the monitor
        @param   heightmm:int?  The physical height, measured in millimetres, of the monitor
        @return  :list<Output>  Matching outputs
        '''
        return self.__find(lambda screen : screen.find_by_size(widthmm, heigthmm))
    
    def find_by_connected(self, status):
        '''
        Find output by connection status
        
        @param   status:bool    Whether the output should be connected or not
        @return  :list<Output>  Matching outputs
        '''
        return self.__find(lambda screen : screen.find_by_connected(status))
    
    def find_by_edid(self, edid):
        '''
        Find output by extended display identification data
        
        @param   edid:str?      The extended display identification data of the monitor
        @return  :list<Output>  Matching outputs
        '''
        return self.__find(lambda screen : screen.find_by_edid(edid))

    
    def __contains__(self, screen):
        '''
        Check if a screen is listed
        
        @param   screen:Screen  The screen
        @return  :bool          Whether the screen is listed
        '''
        return screen in self.screens
    
    def __getitem__(self, index):
        '''
        Get a screen by its index
        
        @param   :int     The screen's index
        @return  :Screen  The screen
        '''
        return self.screens[index]
    
    def __iter__(self):
        '''
        Create an interator of the screens
        
        @return  :itr<Screen>  An interator of the screens
        '''
        return iter(self.screens)
    
    def __len__(self):
        '''
        Get the number of screens
        
        @return  :int  The number of screens
        '''
        return len(self.screens)
    
    def __reversed__(self):
        '''
        Get a reversed iterator of the screens
    
        @return  :itr<Screen>  An interator of the screens in reversed order
        '''
        return reversed(self.screens)
    
    def __setitem__(self, index, item):
        '''
        Replace a screen
        
        @param  index:int    The index of the screen
        @param  item:Screen  The screen
        '''
        self.screens[index] = item
    
    def __repr__(self):
        '''
        Get a string representation of the screens
        
        @return  :str  String representation of the screens
        '''
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
        return [output for output in self.outputs if output.crtc == index]
    
    def find_by_name(self, name):
        '''
        Find output by name
        
        @param   name:str       The name of the output
        @return  :list<Output>  Matching outputs
        '''
        return [output for output in self.outputs if output.name == name]
    
    def find_by_size(self, widthmm, heightmm):
        '''
        Find output by physical size
        
        @param   widthmm:int?   The physical width, measured in millimetres, of the monitor
        @param   heightmm:int?  The physical height, measured in millimetres, of the monitor
        @return  :list<Output>  Matching outputs
        '''
        return [out for out in self.outputs if (out.widthmm == widthmm) and (out.heightmm == heightmm)]
    
    def find_by_connected(self, status):
        '''
        Find output by connection status
        
        @param   status:bool    Whether the output should be connected or not
        @return  :list<Output>  Matching outputs
        '''
        return [output for output in self.outputs if output.connected == status]
    
    def find_by_edid(self, edid):
        '''
        Find output by extended display identification data
        
        @param   edid:str?      The extended display identification data of the monitor
        @return  :list<Output>  Matching outputs
        '''
        return [output for output in self.outputs if output.edid == edid]
    
    def __repr__(self):
        '''
        Return a string representation of the instance
        
        @return  :str  String representation of the instance
        '''
        return '[CRTC count: %i, Outputs: %s]' % (self.crtc_count, repr(self.outputs))


class Output:
    '''
    Output information
    
    @variable  name:str        The name of the output
    @variable  connected:bool  Whether the outout is known to be connected
    @variable  widthmm:int?    The physical width of the monitor, measured in millimetres, `None` if unknown, not defined or not connected
    @variable  heigthmm:int?   The physical height of the monitor, measured in millimetres, `None` if unknown, not defined or not connected
    @variable  crtc:int?       The CRTC index, `None` if not connected
    @variable  screen:int?     The screen index, `None` if none
    @variable  edid:str?       Extended display identification data, `None` if none
    '''
    def __init__(self):
        '''
        Constructor
        '''
        self.connected = False
        self.name, self.widthmm, self.heightmm, self.crtc, self.screen, self.edid = [None] * 6
    
    def __repr__(self):
        '''
        Return a string representation of the instance
        '''
        # Select the order of the values
        rc = [self.name, self.connected, self.widthmm, self.heightmm, self.crtc, self.screen, self.edid]
        # Convert the values to strings
        rc = tuple(rc[:1] + [repr(x) for x in rc[1 : -1]] + [str(rc[-1])])
        # Combine the values
        return '[Name: %s, Connected: %s, Width: %s, Height: %s, CRTC: %s, Screen: %s, EDID: %s]' % rc


def list_screens(method = None, display = None):
    '''
    Retrieve informantion about all screens, outputs and CRTC:s
    
    @param   method:str?   The listing method: 'randr' for RandR (under X),
                                               'drm' for DRM (under TTY)
                                               `None` for automatic
    @param   display:str?  The display to use, `None` for the current one
    @return  :Screens      An instance of a datastructure with the relevant information
    '''
    import output
    if not list_screens.warned:
        list_screens.warned = True
        print('list_screens() is deprecated', file = sys.stderr)
    if (method, display) not in cached_displays:
        cached_displays[(method, display)] = output.get_outputs(method = method, display = display)
    rc = Screens()
    rc.screens = cached_displays[(method, display)].screens
    for screen_i, screen in enumerate(rc.screens):
        screen.crtc_count = len(screen.crtcs)
        screen.outputs = [None] * screen.crtc_count
        for crtc_i in range(screen.crtc_count):
            screen.outputs[crtc_i] = output = Output()
            output.screen = screen_i
            output.crtc = crtc_i
            crtc = screen.crtcs[crtc_i]
            output.name = crtc.connector_name
            output.connected = crtc.active
            output.widthmm = crtc.width_mm
            output.heightmm = crtc.height_mm
            output.edid = crtc.edid
    return rc
list_screens.warned = False


def list_screens_randr(display = None):
    '''
    Retrieve informantion about all screens, outputs and CRTC:s, using RandR
    
    @param   display:str?  The display to use, `None` for the current one
    @return  :Screens      An instance of a datastructure with the relevant information
    '''
    if not list_screens_randr.warned:
        list_screens_randr.warned = True
        print('list_screens_randr() is deprecated', file = sys.stderr)
    return list_screens('randr', display)
list_screens_randr.warned = False

def list_screens_drm():
    '''
    Retrieve informantion about all screens, outputs and CRTC:s, using DRM
    
    @return  :Screens  An instance of a datastructure with the relevant information
    '''
    if not list_screens_drm.warned:
        list_screens_drm.warned = True
        print('list_screens_drm() is deprecated', file = sys.stderr)
    return list_screens('drm', None)
list_screens_drm.warned = False

def list_screens_quartz():
    '''
    Retrieve informantion about all screens, outputs and CRTC:s, using Quartz
    
    @return  :Screens  An instance of a datastructure with the relevant information
    '''
    if not list_screens_quartz.warned:
        list_screens_quartz.warned = True
        print('list_screens_quartz() is deprecated', file = sys.stderr)
    return list_screens('quartz', None)
list_screens_quartz.warned = False

def list_screens_w32gdi():
    '''
    Retrieve informantion about all screens, outputs and CRTC:s, using Windows GDI
    
    @return  :Screens  An instance of a datastructure with the relevant information
    '''
    if not list_screens_w32gdi.warned:
        list_screens_w32gdi.warned = True
        print('list_screens_w32gdi() is deprecated', file = sys.stderr)
    return list_screens('w32gdi', None)
list_screens_w32gdi.warned = False


def quartz_restore():
    '''
    Restore all CRTC:s' gamma ramps the settings in ColorSync
    '''
    import output
    if not quartz_restore.warned:
        quartz_restore.warned = True
        print('quartz_restore() is deprecated', file = sys.stderr)
    if ('quartz', None) not in cached_displays:
        cached_displays[('quartz', None)] = output.get_outputs(method = 'quartz')
    cached_displays[('quartz', None)].restore()
quartz_restore.warned = False

