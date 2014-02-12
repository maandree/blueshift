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
import math


r_curve = [i / 255 for i in range(256)]
g_curve = [i / 255 for i in range(256)]
b_curve = [i / 255 for i in range(256)]


def curves(r, g, b):
    '''
    Generate a tuple of curve–parameter pairs
    
    @param   r  The red parameter
    @param   g  The green parameter
    @param   b  The blue parameter
    @return     ((r_curve, r), (g_curve, g), (b_curve, b))
    '''
    return ((r_curve, r), (g_curve, g), (b_curve, b))


def sigmoid(r, g, b):
    '''
    Apply S-curve correction on the colour curves
    
    @param  r:float  The sigmoid parameter for the red curve
    @param  g:float  The sigmoid parameter for the green curve
    @param  b:float  The sigmoid parameter for the blue curve
    '''
    for (curve, level) in curves(r, g, b):
        if not level == 1.0:
            for i in range(256):
                try:
                    curve[i] = 0.5 - math.log(1 / curve[i] - 1) / level
                except:
                    curve[i] = 0;


def contrast(r, g, b):
    '''
    Apply contrast correction on the colour curves
    
    @param  r:float  The contrast parameter for the red curve
    @param  g:float  The contrast parameter for the green curve
    @param  b:float  The contrast parameter for the blue curve
    '''
    for (curve, level) in curves(r, g, b):
        if not level == 1.0:
            for i in range(256):
                curve[i] = (curve[i] - 0.5) * level + 0.5

def brightness(r, g, b):
    '''
    Apply brightness correction on the colour curves
    
    @param  r:float  The brightness parameter for the red curve
    @param  g:float  The brightness parameter for the green curve
    @param  b:float  The brightness parameter for the blue curve
    '''
    for (curve, level) in curves(r, g, b):
        if not level == 1.0:
            for i in range(256):
                curve[i] *= level

def gamma(r, g, b):
    '''
    Apply gamma correction on the colour curves
    
    @param  r:float  The gamma parameter for the red curve
    @param  g:float  The gamma parameter for the green curve
    @param  b:float  The gamma parameter for the blue curve
    '''
    for (curve, level) in curves(r, g, b):
        if not level == 1.0:
            for i in range(256):
                curve[i] **= level

def clip():
    '''
    Clip all values belowed the actual minimum and above actual maximums
    '''
    for curve in (r_curve, g_curve, b_curve):
        for i in range(256):
            curve[i] = min(max(0.0, curve[i]), 1.0)


sigmoid(1.0, 1.0, 1.0)
clip()
contrast(1.0, 1.0, 1.0)
brightness(1.0, 1.0, 1.0)
gamma(1.0, 1.0, 1.0)
clip()


for curve in (r_curve, g_curve, b_curve):
    for i in range(256):
        curve[i] = int(curve[i] * 65535 + 0.5)
print(r_curve)
print(g_curve)
print(b_curve)
print(Math.e)

