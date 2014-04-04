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

import os
import sys
from subprocess import Popen, PIPE

from aux import *
from curve import *


LIBDIR = 'bin'
'''
:str  Path to libraries, '/usr/lib' is standard
'''

LIBEXECDIR = 'bin'
'''
:str  Path to executable libraries, '/usr/libexec' is standard
'''


## Add the path to libraries to the list of paths to Python modules
sys.path.append(LIBDIR)


## Load DRM module
try:
    from blueshift_drm import *
except:
    # Not compiled with DRM support
    pass


randr_opened = None
'''
:(int, str)?  The index of the, with RandR, opened X screen and X display, if any
'''

vidmode_opened = None
'''
:(int, str)?  The index of the, with vidmode, opened X screen and X display, if any
'''


def close_c_bindings():
    '''
    Close all C bindings and let them free resources and close connections
    '''
    global randr_opened, vidmode_opened
    if randr_opened is not None:
        # Close RandR connection if open
        from blueshift_randr import randr_close
        randr_opened = None
        randr_close()
    if vidmode_opened is not None:
        # Close vidmode connection if open
        from blueshift_vidmode import vidmode_close
        vidmode_opened = None
        vidmode_close()
    # Close DRM connection if open
    drm_manager.close()


def randr_get(crtc = 0, screen = 0, display = None):
    '''
    Gets the current colour curves using the X11 extension RandR
    
    @param   crtc:int      The CRTC of the monitor to read from
    @param   screen:int    The screen to which the monitors belong
    @param   display:str?  The display to which to connect, `None` for current display
    @return  :()→void      Function to invoke to apply the curves that was used when this function was invoked
    '''
    from blueshift_randr import randr_open, randr_read, randr_close
    global randr_opened
    # Open new RandR connection if non is open or one is open to the wrong screen or display
    if (randr_opened is None) or not (randr_opened == (screen, display)):
        # Close RandR connection, if any, because its is connected to the wrong screen or display
        if randr_opened is not None:
            randr_close()
        # Open RandR connection
        if randr_open(screen, display if display is None else display.encode('utf-8')) == 0:
            randr_opened = (screen, display)
        else:
            raise Exception('Cannot open RandR connection')
    # Read current curves and create function
    return ramps_to_function(*(randr_read(crtc)))


def vidmode_get(crtc = 0, screen = 0, display = None):
    '''
    Gets the current colour curves using the X11 extension VidMode
    
    @param   crtc:int      The CRTC of the monitor to read from
    @param   screen:int    The screen to which the monitors belong
    @param   display:str?  The display to which to connect, `None` for current display
    @return  :()→void      Function to invoke to apply the curves that was used when this function was invoked
    '''
    from blueshift_vidmode import vidmode_open, vidmode_read, vidmode_close
    global vidmode_opened
    # Open new vidmode connection if non is open or one is open to the wrong screen or display
    if (vidmode_opened is None) or not (vidmode_opened == (screen, display)):
        # Close vidmode connection, if any, because its is connected to the wrong screen or display
        if vidmode_opened is not None:
            vidmode_close()
        # Open vidmode connection
        if vidmode_open(screen, display if display is None else display.encode('utf-8')):
            vidmode_opened = (screen, display)
        else:
            raise Exception('Cannot open vidmode connection')
    # Read current curves and create function
    return ramps_to_function(*(vidmode_read(crtc)))


def drm_get(crtc = 0, screen = 0, display = None):
    '''
    Gets the current colour curves using DRM
    
    @param   crtc:int      The CRTC of the monitor to read from
    @param   screen:int    The graphics card to which the monitors belong, named `screen` for compatibility with `randr_get` and `vidmode_get`
    @param   display:str?  Dummy parameter for compatibility with `randr_get` and `vidmode_get`
    @return  :()→void      Function to invoke to apply the curves that was used when this function was invoked
    '''
    # Get DRM connection, open if necessary
    connection = drm_manager.open_card(screen)
    # Read current curves and create function
    return ramps_to_function(*(drm_get_gamma_ramps(connection, crtc, i_size)))


def randr(*crtcs, screen = 0, display = None):
    '''
    Applies colour curves using the X11 extension RandR
    
    @param  crtcs:*int    The CRT controllers to use, all are used if none are specified
    @param  screen:int    The screen to which the monitors belong
    @param  display:str?  The display to which to connect, `None` for current display
    '''
    from blueshift_randr import randr_open, randr_apply, randr_close
    global randr_opened
    # Select CRTC:s
    crtcs = sum([1 << i for i in crtcs]) if len(crtcs) > 0 else ((1 << 64) - 1)
    
    # Convert curves to [0, 0xFFFF] integer lists
    (R_curve, G_curve, B_curve) = translate_to_integers()
    # Open new RandR connection if non is open or one is open to the wrong screen or display
    if (randr_opened is None) or not (randr_opened == (screen, display)):
        # Close RandR connection, if any, because its is connected to the wrong screen or display
        if randr_opened is not None:
            randr_close()
        # Open RandR connection
        if randr_open(screen, display if display is None else display.encode('utf-8')) == 0:
            randr_opened = (screen, display)
        else:
            raise Exception('Cannot open RandR connection')
    try:
        # Apply adjustments
        if not randr_apply(crtcs, R_curve, G_curve, B_curve) == 0:
            raise Exception('Cannot use RandR to apply colour adjustments')
    except OverflowError:
        pass # Happens on exit by TERM signal


def vidmode(*crtcs, screen = 0, display = None):
    '''
    Applies colour curves using the X11 extension VidMode
    
    @param  crtcs:*int    The CRT controllers to use, all are used if none are specified
    @param  screen:int    The screen to which the monitors belong
    @param  display:str?  The display to which to connect, `None` for current display
    '''
    from blueshift_vidmode import vidmode_open, vidmode_apply, vidmode_close
    global vidmode_opened
    # Select CRTC:s
    crtcs = sum([1 << i for i in crtcs]) if len(crtcs) > 0 else ((1 << 64) - 1)
    
    # Convert curves to [0, 0xFFFF] integer lists
    (R_curve, G_curve, B_curve) = translate_to_integers()
    # Open new vidmode connection if non is open or one is open to the wrong screen or display
    if (vidmode_opened is None) or not (vidmode_opened == (screen, display)):
        # Close vidmode connection, if any, because its is connected to the wrong screen or display
        if vidmode_opened is not None:
            vidmode_close()
        # Open vidmode connection
        if vidmode_open(screen, display if display is None else display.encode('utf-8')):
            vidmode_opened = (screen, display)
        else:
            raise Exception('Cannot open vidmode connection')
    try:
        # Apply adjustments
        if not vidmode_apply(crtcs, R_curve, G_curve, B_curve) == 0:
            raise Exception('Cannot use vidmode to apply colour adjustments')
    except OverflowError:
        pass # Happens on exit by TERM signal


def drm(*crtcs, screen = 0, display = None):
    '''
    Applies colour curves using DRM
    
    @param  crtcs:*int    The CRT controllers to use, all are used if none are specified
    @param  screen:int    The graphics card to which the monitors belong,
                          named `screen` for compatibility with `randr` and `vidmode`
    @param  display:str?  Dummy parameter for compatibility with `randr` and `vidmode`
    '''
    # Get DRM connection, open if necessary
    connection = drm_manager.open_card(screen)
    # Convert curves to [0, 0xFFFF] integer lists
    (R_curve, G_curve, B_curve) = translate_to_integers()
    try:
        # Select all CRTC:s if none have been selected
        if len(crtcs) == 0:
            crtcs = range(drm_crtc_count(connection))
        # Apply adjustments
        drm_set_gamma_ramps(connection, list(crtcs), i_size, R_curve, G_curve, B_curve)
    except OverflowError:
        pass # Happens on exit by TERM signal


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


def list_screens(method = 'randr', display = None):
    '''
    Retrieve informantion about all screens, outputs and CRTC:s
    
    @param   method:str    The listing method: 'randr' for RandR (under X),
                                             'drm' for DRM (under TTY)
    @param   display:str?  The display to use, `None` for the current one
    @return  :Screens      An instance of a datastructure with the relevant information
    '''
    if method == 'randr':  return list_screens_randr(display = display)
    if method == 'drm':    return list_screens_drm()
    raise Exception('Invalid method: %s' % method)


def list_screens_randr(display = None):
    '''
    Retrieve informantion about all screens, outputs and CRTC:s, using RandR
    
    @param   display:str?  The display to use, `None` for the current one
    @return  :Screens      An instance of a datastructure with the relevant information
    '''
    # Generate command line arguments to execute
    command = [LIBEXECDIR + os.sep + 'blueshift_idcrtc']
    if display is not None:
        command.append(display)
    # Spawn the executable library blueshift_idcrtc
    process = Popen(command, stdout = PIPE)
    # Wait for the child process to exit and gather its output to stdout
    lines = process.communicate()[0].decode('utf-8', 'error').split('\n')
    # Ensure that the child process has exited
    while process.returncode is None:
        process.wait()
    # Raise an exception if the child process failed
    if process.returncode != 0:
        raise Exception('blueshift_idcrtc exited with value %i' % process.returncode)
    # Trim the beginning of each line, that is, remove the
    # indention added for human readablility
    lines = [line.strip() for line in lines]
    screens, screen_i, screen, output = None, None, None, None
    for line in lines:
        if line.startswith('Screen count: '):
            # Prepare the screen table when we know how many screens there are
            screens = [None] * int(line[len('Screen count: '):])
        elif line.startswith('Screen: '):
            # Get the index of the next screen
            screen_i = int(line[len('Screen: '):])
            # And add it to the table
            screens[screen_i] = screen = Screen()
        elif line.startswith('CRTC count: '):
            # Store the number of CRTC:s
            screen.crtc_count = int(line[len('CRTC count: '):])
        elif line.startswith('Output count: '):
            # Prepare the current screens output table when we know how many outputs it has
            screen.outputs = [None] * int(line[len('Output count: '):])
        elif line.startswith('Output: '):
            # Get the index of the next output
            output_i = int(line[len('Output: '):])
            # Create structure for the output
            output = Output()
            # Store the screen index for the output so that it is easy
            # to look it up when iterating over outputs
            output.screen = screen_i
            # Store the output in the table
            screen.outputs[output_i] = output
        elif line.startswith('Name: '):
            # Store the name of the output
            output.name = line[len('Name: '):]
        elif line.startswith('Connection: '):
            # Store the connection status of the output's connector
            output.connected = line[len('Connection: '):] == 'connected'
        elif line.startswith('Size: '):
            # Store the physical dimensions of the monitor
            output.widthmm, output.heightmm = [int(x) for x in line[len('Size: '):].split(' ')]
            # But if it is zero or less it is unknown
            if (output.widthmm <= 0) or (output.heightmm <= 0):
                output.widthmm, output.heightmm = None, None
        elif line.startswith('CRTC: '):
            # Store the CRTC index of the output
            output.crtc = int(line[len('CRTC: '):])
        elif line.startswith('EDID: '):
            # Store the output's extended dislay identification data
            output.edid = line[len('EDID: '):]
    # Store all screens in a special class that
    # makes it easier to use them collectively
    rc = Screens()
    rc.screens = screens
    return rc


def list_screens_drm():
    '''
    Retrieve informantion about all screens, outputs and CRTC:s, using DRM
    
    @return  :Screens  An instance of a datastructure with the relevant information
    '''
    ## This method should not use `drm_manager` because we want to be able to find updates
    # Create instance of class with all the graphics cards so that it is easy
    # to use them collectively,
    screens = Screens()
    # and create the list to fill with graphics cards.
    screens.screens = []
    ## When using DRM we will often call graphics cards ‘screens’ as
    ## to keep consisitence with X extension. In real world use, it is
    ## usally equivalent, except for the order of the CRTC:s.
    # For each graphics card, by index:
    for card in range(drm_card_count()):
        # Create an instance which makes it easy to use the
        # graphics cards, such as searching for monitors,
        screen = Screen()
        # and append it to the list of graphics cards.
        screens.screens.append(screen)
        # Acquire resources for the graphics card,
        connection = drm_open_card(card)
        # but just ignore the card on failure.
        if connection == -1:
            continue # TODO could this fail if the card is already used by Blueshift?
        # As our DRM module's API dictates, update the resources
        drm_update_card(connection)
        # Store the number of CRTC:s, so that it can
        # be easily accessed; all connectors do not have a CRTCs,
        # because they need to have a monitor connected an unused
        # connectors are also listed.
        screen.crtc_count = drm_crtc_count(connection)
        # Create a graphics card local str → int map from the
        # connector type name of the number of used such connectors
        # so that we can name the outputs uniquely within the
        # scope of the card with reason names. These will not be
        # the same as the named given by RandR or `/sys/class/drm`.
        used_names = {}
        # For each connector of the graphics card:
        for connector in range(drm_connector_count(connection)):
            # Open a connection to the connector
            drm_open_connector(connection, connector)
            # Create an instance of a data structure to store output information inside,
            output = Output()
            # and add it to the list of outputs for the graphics card.
            screen.outputs.append(output)
            # The connector type name
            output.name = drm_get_connector_type_name(connection, connector)
            # and append an index to it and use that as the name of the output.
            if output.name not in used_names:
                # Start at zero,
                used_names[output.name] = 0
            # and count upwards as the type of connector reoccurs.
            count = used_names[output.name]
            used_names[output.name] += 1
            output.name = '%s-%i' % (output.name, count)
            # Store the connection status of the connector,
            # but assume it is disconnected if it is unknown.
            output.connected = drm_is_connected(connection, connector) == 1
            if output.connected:
                # Store the physical dimensions of the monitor
                output.widthmm = drm_get_width(connection, connector)
                output.heightmm = drm_get_height(connection, connector)
                # But if it is zero or less it is unknown
                if (output.widthmm <= 0) or (output.heightmm <= 0):
                    output.widthmm, output.heightmm = None, None
                # Store the output's CRTC index
                output.crtc = drm_get_crtc(connection, connector)
                # Store the output's extended display identification data
                output.edid = drm_get_edid(connection, connector)
            # Store the graphics card index for the output so that
            # it is easy to look it up when iterating over outputs
            output.screen = card
            # Now that we are done with the connector, close its resources
            drm_close_connector(connection, connector)
        # Now that we are done with the graphics card, close its resources
        drm_close_card(connection)
    # Mark that the DRM module has been used so that
    # resource as properly freed. This is the only
    # time in this function `drm_manager` shall be used.
    drm_manager.is_open = True
    return screens


class DRMManager:
    '''
    Manager for DRM connections to avoid monitor flicker on unnecessary connections
    
    There should only be one instance of this class
    
    @variable  is_open:bool      Whether the DRM module has been used
    @variable  cards:list<int>?  Map from card index to connection file descriptors, -1 if not connected
    '''
    
    def __init__(self):
        '''
        Constructor
        '''
        self.is_open, self.cards, self.connectors = False, None, None
    
    def open_card(self, card):
        '''
        Make sure there is a connection to a specific card
        
        @param   card:int  The index of the card
        @return  :int      -1 on failure, otherwise the identifier for the connection
        '''
        # Mark that the DRM module has been used
        self.is_open = True
        # Initialise connection map if not already initialised,
        if self.cards is None:
            self.cards = [-1] * drm_card_count()
            # and the graphics card layer of the connector map.
            self.connectors = [None] * drm_card_count()
        # If we are not connected to the desired graphics card
        if self.cards[card] == -1:
            # connect to it
            self.cards[card] = drm_open_card(card)
            # and acquire resources.
            drm_update_card(self.cards[card])
        return self.cards[card]
    
    def open_connector(self, card, connector):
        '''
        Make sure there is a connection to a specific connector
        
        @param  card:int       The index of the card with the connector, must already be opened
        @param  connector:int  The index of the connector
        '''
        # The file descriptor of the connection to the graphics card,
        connection = self.open_card(card)
        # and initialise the connector map if not alreadt initialised.
        if self.connectors[card] is None:
            self.connectors[card] = [False] * drm_connector_count()
        # Then, if the connector is not already opened,
        if not self.connectors[card][connector]:
            # mark it as opened,
            self.connectors[card][connector] = True
            # and open it.
            drm_open_connector(connection, connector)
    
    def close_connector(self, card, connector):
        '''
        Make sure there is no connection to a specific connector
        
        @param  card:int       The index of the card with the connector
        @param  connector:int  The index of the connector
        '''
        # If no graphics card has been opened, do nothing
        if self.cards is None:  return
        # Otherwise get the connection to the graphics card,
        connection = self.cards[card]
        # but do nothing if is has not been opened.
        if connection == -1:  return
        # Neither do anything if no connector has been used.
        if self.connectors[card] is None:  return
        # If the connector has been used,
        if self.connectors[card][connector]:
            # mark it as unused,
            self.connectors[card][connector] = False
            # as close it.
            drm_close_connector(connection, connector)
    
    def close_card(self, card):
        '''
        Make sure there is no connection to a specific card
        
        @param  card:int  The index of the card
        '''
        # Do nothing is no graphics card has been used
        if self.cards is None:
            return
        # Otherwise get the file descriptor of the connection to the card.
        connection = self.cards[card]
        # If The graphics card has been used
        if not connection == -1:
            # Mark it as unused,
            self.cards[card] = -1
            # and close the connection to any opened connector
            if self.connectors[card] is not None:
                # by iterating over the connectors
                for i in range(len(self.connectors[card])):
                    # and close any opened connector
                    if self.connectors[card][i]:
                        drm_close_connector(connection, i)
                # and then mark all connectors as unused.
                self.connectors[card] = None
            # Close the connection to the graphics card
            drm_close_card(connection)
    
    def close(self):
        '''
        Close all connections
        '''
        # If the DRM module as been used
        if self.is_open:
            # Makr it as unused
            self.is_open = False
            # And close all connections to the graphics cards and their connectors
            if self.cards is not None:
                for card in range(len(self.cards)):
                    self.close_card(card)
                self.cards = None
            # And close finally close the connection to DRM
            drm_close()

drm_manager = DRMManager()
'''
:DRMManager  Manager for DRM connections to avoid monitor flicker on unnecessary connections
'''

