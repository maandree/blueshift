#!/usr/bin/env python3

# Copyright © 2014  Mattias Andrée (maandree@member.fsf.org)
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
# 
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import sys

from curve import *

# /usr/lib
LIBDIR = 'bin'
sys.path.append(LIBDIR)

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
    Gets the current colour curves using the X11 extension randr
    
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
    (r, g, b) = randr_read()
    def fcurve(R_curve, G_curve, B_curve):
        for curve, cur in curves(R_curve, G_curve, B_curve):
            for i in range(i_size):
                y = int(curve[i] * (len(cur) - 1) + 0.5)
                y = min(max(0, y), len(cur) - 1)
                curve[i] = cur[y]
    return lambda : fcurve


def vidmode_get(crtc = 0, screen = 0):
    '''
    Gets the current colour curves using the X11 extension vidmode
    
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
    (r, g, b) = vidmode_read()
    def fcurve(R_curve, G_curve, B_curve):
        for curve, cur in curves(R_curve, G_curve, B_curve):
            for i in range(i_size):
                y = int(curve[i] * (len(cur) - 1) + 0.5)
                y = min(max(0, y), len(cur) - 1)
                curve[i] = cur[y]
    return lambda : fcurve


def randr(*crtcs, screen = 0):
    '''
    Applies colour curves using the X11 extension randr
    
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
    Applies colour curves using the X11 extension vidmode
    
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


def print_curves(*crtcs, screen = 0):
    '''
    Prints the curves to stdout
    
    @param  crtcs:*int  Dummy parameter
    @param  screen:int  Dummy parameter
    '''
    (R_curve, G_curve, B_curve) = translate_to_integers()
    print(R_curve)
    print(G_curve)
    print(B_curve)

