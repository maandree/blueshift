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
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

# This module is responsible for access to the monitors.

import os
import sys
from subprocess import Popen, PIPE

from aux import *
from curve import *

import libgammaman
import libgamma



def close_c_bindings():
    '''
    Close all C bindings and let them free resources and close connections
    '''
    libgammaman.close()


def get_gamma(crtc = 0, screen = 0, display = None, *, method = None):
    '''
    Gets the current colour curves
    
    @param   crtc:int      The CRTC of the monitor to read from
    @param   screen:int    The screen to which the monitors belong
    @param   display:str?  The display to which to connect, `None` for current display
    @param   method:str?   The adjustment method
    @return  :()→void      Function to invoke to apply the curves that was used when this function was invoked
    '''
    # Get CRTC objet
    method = libgammaman.get_method(method)
    crtc = libgammaman.get_crtc(crtc, screen, display, method)
    # Create gamma ramps
    ramps = libgamma.GammaRamps(i_size, i_size, i_size)
    # Get gamma
    crtc.get_gamma(ramps)
    return ramps_to_function(ramps.red, ramps.green, ramps.blue)


def set_gamma(*crtcs, screen = 0, display = None, method = None):
    '''
    Applies colour curves
    
    @param  crtcs:*int    The CRT controllers to use, all are used if none are specified
    @param  screen:int    The screen to which the monitors belong
    @param  display:str?  The display to which to connect, `None` for current display
    @param  method:str?   The adjustment method
    '''
    for crtc in (0,) if len(crtcs) == 0 else crtcs:
        # Convert curves to [0, 0xFFFF] integer lists
        (R_curve, G_curve, B_curve) = translate_to_integers()
        # Get CRTC objet
        method = libgammaman.get_method(method)
        crtc = libgammaman.get_crtc(crtc, screen, display, method)
        # Create gamma ramps
        ramps = libgamma.GammaRamps(i_size, i_size, i_size)
        # Set gamma
        ramps.red[:] = R_curve
        ramps.green[:] = G_curve
        ramps.blue[:] = B_curve
        crtc.set_gamma(ramps)


def randr_get(crtc = 0, screen = 0, display = None):
    '''
    Gets the current colour curves using the X11 extension RandR
    
    @param   crtc:int      The CRTC of the monitor to read from
    @param   screen:int    The screen to which the monitors belong
    @param   display:str?  The display to which to connect, `None` for current display
    @return  :()→void      Function to invoke to apply the curves that was used when this function was invoked
    '''
    return get_gamma(crtc, screen, display, method = 'randr')

def vidmode_get(crtc = 0, screen = 0, display = None):
    '''
    Gets the current colour curves using the X11 extension VidMode
    
    @param   crtc:int      The CRTC of the monitor to read from, dummy parameter
    @param   screen:int    The screen to which the monitors belong
    @param   display:str?  The display to which to connect, `None` for current display
    @return  :()→void      Function to invoke to apply the curves that was used when this function was invoked
    '''
    return get_gamma(crtc, screen, display, method = 'vidmode')

def drm_get(crtc = 0, screen = 0, display = None):
    '''
    Gets the current colour curves using DRM
    
    @param   crtc:int      The CRTC of the monitor to read from
    @param   screen:int    The graphics card to which the monitors belong, named `screen` for compatibility with `randr_get` and `vidmode_get`
    @param   display:str?  Dummy parameter for compatibility with `randr_get` and `vidmode_get`
    @return  :()→void      Function to invoke to apply the curves that was used when this function was invoked
    '''
    return get_gamma(crtc, screen, display, method = 'drm')

def w32gdi_get(crtc = 0, screen = 0, display = None):
    '''
    Gets the current colour curves using W32 GDI
    
    @param   crtc:int      The CRTC of the monitor to read from
    @param   screen:int    Dummy parameter for compatibility with `randr_get`, `vidmode_get` and `drm_get`
    @param   display:str?  Dummy parameter for compatibility with `randr_get` and `vidmode_get`
    @return  :()→void      Function to invoke to apply the curves that was used when this function was invoked
    '''
    return get_gamma(crtc, screen, display, method = 'w32gdi')

def quartz_get(crtc = 0, screen = 0, display = None):
    '''
    Gets the current colour curves using Quartz
    
    @param   crtc:int      The CRTC of the monitor to read from
    @param   screen:int    Dummy parameter for compatibility with `randr_get`, `vidmode_get` and `drm_get`
    @param   display:str?  Dummy parameter for compatibility with `randr_get` and `vidmode_get`
    @return  :()→void      Function to invoke to apply the curves that was used when this function was invoked
    '''
    return get_gamma(crtc, screen, display, method = 'quartz')


def randr(*crtcs, screen = 0, display = None):
    '''
    Applies colour curves using the X11 extension RandR
    
    @param  crtcs:*int    The CRT controllers to use, all are used if none are specified
    @param  screen:int    The screen to which the monitors belong
    @param  display:str?  The display to which to connect, `None` for current display
    '''
    set_gamma(*crtcs, screen = screen, display = display, method = 'randr')

def vidmode(*crtcs, screen = 0, display = None):
    '''
    Applies colour curves using the X11 extension VidMode
    
    @param  crtcs:*int    The CRT controllers to use, all are used if none are specified, dummy parameter
    @param  screen:int    The screen to which the monitors belong
    @param  display:str?  The display to which to connect, `None` for current display
    '''
    set_gamma(*crtcs, screen = screen, display = display, method = 'vidmode')

def drm(*crtcs, screen = 0, display = None):
    '''
    Applies colour curves using DRM
    
    @param  crtcs:*int    The CRT controllers to use, all are used if none are specified
    @param  screen:int    The graphics card to which the monitors belong,
                          named `screen` for compatibility with `randr` and `vidmode`
    @param  display:str?  Dummy parameter for compatibility with `randr` and `vidmode`
    '''
    set_gamma(*crtcs, screen = screen, display = display, method = 'drm')

def w32gdi(*crtcs, screen = 0, display = None):
    '''
    Applies colour curves using W32 GDI
    
    @param  crtcs:*int    The CRT controllers to use, all are used if none are specified
    @param  screen:int    Dummy parameter for compatibility with `randr`, `vidmode` and `drm`
    @param  display:str?  Dummy parameter for compatibility with `randr` and `vidmode`
    '''
    set_gamma(*crtcs, screen = screen, display = display, method = 'w32gdi')

def quartz(*crtcs, screen = 0, display = None):
    '''
    Applies colour curves using Quartz
    
    @param  crtcs:*int    The CRT controllers to use, all are used if none are specified
    @param  screen:int    Dummy parameter for compatibility with `randr`, `vidmode` and `drm`
    @param  display:str?  Dummy parameter for compatibility with `randr` and `vidmode`
    '''
    set_gamma(*crtcs, screen = screen, display = display, method = 'quartz')


def print_curves(*crtcs, screen = 0, display = None, compact = False):
    '''
    Prints the curves to stdout
    
    @param  crtcs:*int    Dummy parameter
    @param  screen:int    Dummy parameter
    @param  display:str?  Dummy parameter
    @param  compact:bool  Whether to print in compact form
    '''
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


class EDID:
    '''
    Data structure for parsed EDID:s
    
    @var  widthmm:int?             The physical width of the monitor, measured in millimetres, `None` if not defined
    @var  heightmm:int?            The physical height of the monitor, measured in millimetres, `None` if not defined or not connected
    @var  gamma:float?             The monitor's estimated gamma characteristics, `None` if not specified
    @var  gamma_correction:float?  Gamma correction to use unless you know more exact values, calculated from `gamma`
    '''
    def __init__(self, edid):
        '''
        Constructor, parses an EDID
        
        @param      edid:str    The edid to parse, in hexadecimal representation
        @exception  :Exception  Raised when the EDID is not of a support format
        '''
        # Check the length of the EDID
        if not len(edid) == 256:
            raise Exception('EDID version not support, length mismatch')
        # Check the EDID:s magic number
        if not edid[:16].upper() == '00FFFFFFFFFFFF00':
            raise Exception('EDID version not support, magic number mismatch')
        # Convert to raw byte representation
        edid = [int(edid[i * 2 : i * 2 + 2], 16) for i in range(128)]
        # Check EDID structure version and revision
        if not edid[18] == 1:
            raise Exception('EDID version not support, version mismatch, only 1.3 supported')
        if not edid[19] == 3:
            raise Exception('EDID version not support, revision mismatch, only 1.3 supported')
        # Get the maximum displayable image dimension
        self.widthmm = edid[21] * 10
        self.heightmm = edid[22] * 10
        if (self.widthmm == 0) or (self.heightmm == 0):
            # If either is zero, it is undefined, e.g. a projector
            self.widthmm = None
            self.heightmm = None
        # Get the gamma characteristics
        if (edid[23] == 255):
            # Not specified if FFh
            self.gamma = None
            self.gamma_correction = None
        else:
            self.gamma = (edid[23] + 100) / 100
            self.gamma_correction = self.gamma / 2.2
        # Check the EDID checksum
        if not sum(edid) % 256 == 0:
            raise Exception('Incorrect EDID checksum')


def list_screens(method = None, display = None):
    '''
    Retrieve informantion about all screens, outputs and CRTC:s
    
    @param   method:str?   The listing method: 'randr' for RandR (under X),
                                               'drm' for DRM (under TTY)
                                               `None` for automatic
    @param   display:str?  The display to use, `None` for the current one
    @return  :Screens      An instance of a datastructure with the relevant information
    '''
    method = libgammaman.get_method(method)
    display_ = libgammaman.get_display(display, method)
    screen_n = display_.partitions_available
    rc = Screens()
    rc.screens = [None] * screen_n
    
    for screen_i in range(screen_n):
        screen = libgammaman.get_screen(screen_i, display, method)
        # And add it to the table
        rc.screens[screen_i] = s = Screen()
        # Store the number of CRTC:s
        s.crtc_count = crtc_n = screen.crtcs_available
        # Prepare the current screens output table when we know how many outputs it has
        s.outputs = [None] * crtc_n
        for crtc_i in range(crtc_n):
            crtc = libgamma.CRTC(screen, crtc_i)
            (info, _) = crtc.information(~0)
            s.outputs[crtc_i] = o = Output()
            # Store the screen index for the output so that it is easy
            # to look it up when iterating over outputs
            o.screen = screen_i
            # Store the name of the output
            o.name = info.connector_name if info.connector_name_error == 0 else None
            # Store the connection status of the output's connector
            o.connected = info.active if info.active_error == 0 else None
            # Store the physical dimensions of the monitor
            o.widthmm, o.heightmm = info.width_mm, info.height_mm
            # But if it is zero or less it is unknown
            if (o.widthmm <= 0) or (o.heightmm <= 0):
                o.widthmm, o.heightmm = None, None
            # Store the CRTC index of the output
            o.crtc = crtc_i
            # Store the output's extended dislay identification data
            o.edid = None if info.edid is None or not info.edid_error == 0 else libgamma.behex_edid(info.edid)
    
    return rc
    


def list_screens_randr(display = None):
    '''
    Retrieve informantion about all screens, outputs and CRTC:s, using RandR
    
    @param   display:str?  The display to use, `None` for the current one
    @return  :Screens      An instance of a datastructure with the relevant information
    '''
    return list_screens('randr', display)

def list_screens_drm():
    '''
    Retrieve informantion about all screens, outputs and CRTC:s, using DRM
    
    @return  :Screens  An instance of a datastructure with the relevant information
    '''
    return list_screens('drm', None)

def list_screens_quartz():
    '''
    Retrieve informantion about all screens, outputs and CRTC:s, using Quartz
    
    @return  :Screens  An instance of a datastructure with the relevant information
    '''
    return list_screens('quartz', None)

def list_screens_w32gdi():
    '''
    Retrieve informantion about all screens, outputs and CRTC:s, using Windows GDI
    
    @return  :Screens  An instance of a datastructure with the relevant information
    '''
    return list_screens('w32gdi', None)


def quartz_restore():
    '''
    Restore all CRTC:s' gamma ramps the settings in ColorSync
    '''
    method = libgammaman.get_method('quartz')
    libgammaman.get_display(None, method).restore()

