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

from blueshift_randr import *
randr_opened = False


def translate_to_integers():
    '''
    Translate the curves from float to integer
    
    @param  :(int, int, int)  The red curve, the green curve and the blue curve, mapped to integers
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
    global randr_opened
    if randr_opened:
        randr_opened = False
        randr_close()


def randr(*crtcs):
    '''
    Applies colour curves using the X11 extension randr
    
    @param  *crtcs  The CRT controllers to use, all are used if none are specified
    '''
    global randr_opened
    crtcs = sum([1 << i for i in list(crtcs)])
    if crtcs == 0:
        crtcs = -1;
    
    (R_curve, G_curve, B_curve) = translate_to_integers()
    if not randr_opened:
        if randr_open(0) == 0: ## TODO support specifying screen
            randr_opened = True
        else:
            sys.exit(1)
    try:
        if not randr_apply(crtcs, R_curve, G_curve, B_curve) == 0:
            sys.exit(1)
    except OverflowError:
        pass # Happens on exit by TERM signal


def print_curves(*crtcs):
    '''
    Prints the curves to stdout
    '''
    (R_curve, G_curve, B_curve) = translate_to_integers()
    print(R_curve)
    print(G_curve)
    print(B_curve)

