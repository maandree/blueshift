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

# This module contains auxiliary functions.

from curve import *


def translate_to_integers():
    '''
    Translate the curves from float to integer
    
    @return  :(r:list<int>, g:list<int>, b:list<int>)  The red curve, the green curve and,
                                                       the blue curve mapped to integers
    '''
    R_curve, G_curve, B_curve = [0] * i_size, [0] * i_size, [0] * i_size
    for i_curve, o_curve in ((r_curve, R_curve), (g_curve, G_curve), (b_curve, B_curve)):
        for i in range(i_size):
            o_curve[i] = int(i_curve[i] * (o_size - 1) + 0.5)
            if clip_result:
                o_curve[i] = min(max(0, o_curve[i]), (o_size - 1))
    return (R_curve, G_curve, B_curve)


def ramps_to_function(r, g, b):
    '''
    Convert a three colour curves to a function that applies those adjustments
    
    @param   r:list<int>  The red colour curves as [0, 65535] integers
    @param   g:list<int>  The green colour curves as [0, 65535] integers
    @param   b:list<int>  The blue colour curves as [0, 65535] integers
    @return  :()→void     Function to invoke to apply the curves that the parameters [r, g and b] represents
    '''
    fp = lambda c : [y / 65535 for y in c]
    return functionise((fp(r), fp(g), fp(b)))


def functionise(rgb):
    '''
    Convert a three colour curves to a function that applies those adjustments
    
    @param   rgb:(r:list<float>, g:list<float>, b:list<float>)  The colour curves as [0, 1] values
    @return  :()→void                                           Function to invoke to apply the curves
                                                                that the parameters [r, g and b] represents
    '''
    def fcurve(R_curve, G_curve, B_curve):
        for curve, cur in curves(R_curve, G_curve, B_curve):
            for i in range(i_size):
                # Nearest neighbour
                y = int(curve[i] * (len(cur) - 1) + 0.5)
                # Truncation to actual neighbour 
                y = min(max(0, y), len(cur) - 1)
                # Remapping
                curve[i] = cur[y]
    return lambda : fcurve(*rgb)


def store():
    '''
    Store the current adjustments
    
    @return  :(r:list<float>, g:list<float>, b:list<float>)  The colour curves
    '''
    return (r_curve[:], g_curve[:], b_curve[:])


def restore(rgb):
    '''
    Discard any currently applied adjustments and apply stored adjustments
    
    @param  rgb:(r:list<float>, g:list<float>, b:list<float>)  The colour curves to restore
    '''
    (r_curve[:], g_curve[:], b_curve[:]) = rgb

