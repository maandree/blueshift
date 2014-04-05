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

# This module contains the colour curve definitions and functions for
# manipulating the colour curves

import math

from colour import *
from blackbody import *



# Mapping input and output maximum values + 1
i_size = 2 ** 8
o_size = 2 ** 16

# Red, green and blue curves
r_curve = [i / (i_size - 1) for i in range(i_size)]
g_curve = [i / (i_size - 1) for i in range(i_size)]
b_curve = [i / (i_size - 1) for i in range(i_size)]



clip_result = True
'''
Set to `False` if you want to allow value overflow rather than clipping,
doing so can create visual artifacts
'''


def curves(r, g, b):
    '''
    Generate a tuple of curve–parameter pairs
    
    @param   r  The red parameter
    @param   g  The green parameter
    @param   b  The blue parameter
    @return     `((r_curve, r), (g_curve, g), (b_curve, b))`
    '''
    return ((r_curve, r), (g_curve, g), (b_curve, b))


def temperature(temperature, algorithm):
    '''
    Change colour temperature according to the CIE illuminant series D using CIE sRBG
    
    @param  temperature:float|str                    The blackbody temperature in kelvins, or a name
    @param  algorithm:(float)→(float, float, float)  Algorithm for calculating a white point, for example `cmf_10deg`
    '''
    rgb_temperature(temperature, algorithm)


def rgb_temperature(temperature, algorithm):
    '''
    Change colour temperature according to the CIE illuminant series D using CIE sRBG
    
    @param  temperature:float|str                    The blackbody temperature in kelvins, or a name
    @param  algorithm:(float)→(float, float, float)  Algorithm for calculating a white point, for example `cmf_10deg`
    '''
    # Resolve colour temperature name
    temperature = kelvins(temperature) # TODO demo this and add to textconf and lisp-esque
    # Do nothing if the temperature is neutral
    if temperature == 6500:  return
    # Otherwise manipulate the colour curves
    rgb_brightness(*(algorithm(temperature)))


def cie_temperature(temperature, algorithm):
    '''
    Change colour temperature according to the CIE illuminant series D using CIE xyY
    
    @param  temperature:float|str                    The blackbody temperature in kelvins, or a name
    @param  algorithm:(float)→(float, float, float)  Algorithm for calculating a white point, for example `cmf_10deg`
    '''
    # Resolve colour temperature name
    temperature = kelvins(temperature)
    # Do nothing if the temperature is neutral
    if temperature == 6500:  return
    # Otherwise manipulate the colour curves
    cie_brightness(*(algorithm(temperature)))


def rgb_contrast(r, g = ..., b = ...):
    '''
    Apply contrast correction on the colour curves using sRGB
    
    In this context, contrast is a measure of difference between the whitepoint and blackpoint,
    if the difference is 0 than they are both grey
    
    @param  r:float      The contrast parameter for the red curve
    @param  g:float|...  The contrast parameter for the green curve, defaults to `r` if `...`
    @param  b:float|...  The contrast parameter for the blue curve, defaults to `g` if `...`
    '''
    # Handle overloading
    if g is ...:  g = r
    if b is ...:  b = g
    # Manipulate the colour curves
    for (curve, level) in curves(r, g, b):
        # But not for the curves with neutral adjustment
        if not level == 1.0:
            curve[:] = [(y - 0.5) * level + 0.5 for y in curve]


def cie_contrast(r, g = ..., b = ...):
    '''
    Apply contrast correction on the colour curves using CIE xyY
    
    In this context, contrast is a measure of difference between the whitepoint and blackpoint,
    if the difference is 0 than they are both grey
    
    @param  r:float      The contrast parameter for the red curve
    @param  g:float|...  The contrast parameter for the green curve, defaults to `r` if `...`
    @param  b:float|...  The contrast parameter for the blue curve, defaults to `g` if `...`
    '''
    # Handle overloading
    if g is ...:  g = r
    if b is ...:  b = g
    # Check if we can reduce the overhead, we can if the adjustments are identical
    same = r == g == b
    # Check we need to do any adjustment
    if (not same) or (not r == 1.0):
        if same:
            # Manipulate all curves in one step if their adjustments are identical
            for i in range(i_size):
                # Convert to CIE xyY
                (x, y, Y) = srgb_to_ciexyy(r_curve[i], g_curve[i], b_curve[i])
                # Manipulate illumination and convert back to sRGB
                (r_curve[i], g_curve[i], b_curve[i]) = ciexyy_to_srgb(x, y, (Y - 0.5) * r + 0.5)
        else:
            # Manipulate all curves individually if their adjustments are not identical
            for i in range(i_size):
                # Convert to CIE xyY
                (x, y, Y) = srgb_to_ciexyy(r_curve[i], g_curve[i], b_curve[i])
                # Manipulate illumination and convert back to sRGB
                (r_curve[i], _g, _b) = ciexyy_to_srgb(x, y, (Y - 0.5) * r + 0.5)
                (_r, g_curve[i], _b) = ciexyy_to_srgb(x, y, (Y - 0.5) * g + 0.5)
                (_r, _g, b_curve[i]) = ciexyy_to_srgb(x, y, (Y - 0.5) * b + 0.5)


def rgb_brightness(r, g = ..., b = ...):
    '''
    Apply brightness correction on the colour curves using sRGB
    
    In this context, brightness is a measure of the whiteness of the whitepoint
    
    @param  r:float      The brightness parameter for the red curve
    @param  g:float|...  The brightness parameter for the green curve, defaults to `r` if `...`
    @param  b:float|...  The brightness parameter for the blue curve, defaults to `g` if `...`
    '''
    # Handle overloading
    if g is ...:  g = r
    if b is ...:  b = r
    # Maniumate the colour curves
    for (curve, level) in curves(r, g, b):
        # But not if the adjustment is neutral
        if not level == 1.0:
            curve[:] = [y * level for y in curve]


def cie_brightness(r, g = ..., b = ...):
    '''
    Apply brightness correction on the colour curves using CIE xyY
    
    In this context, brightness is a measure of the whiteness of the whitepoint
    
    @param  r:float      The brightness parameter for the red curve
    @param  g:float|...  The brightness parameter for the green curve, defaults to `r` if `...`
    @param  b:float|...  The brightness parameter for the blue curve, defaults to `g` if `...`
    '''
    # Handle overloading
    if g is ...:  g = r
    if b is ...:  b = g
    # Check if we can reduce the overhead, we can if the adjustments are identical
    same = r == g == b
    # Check we need to do any adjustment
    if (not same) or (not r == 1.0):
        if same:
            # Manipulate all curves in one step if their adjustments are identical
            for i in range(i_size):
                # Convert to CIE xyY
                (x, y, Y) = srgb_to_ciexyy(r_curve[i], g_curve[i], b_curve[i])
                (r_curve[i], g_curve[i], b_curve[i]) = ciexyy_to_srgb(x, y, Y * r)
        else:
            # Manipulate all curves individually if their adjustments are not identical
            for i in range(i_size):
                # Convert to CIE xyY
                (x, y, Y) = srgb_to_ciexyy(r_curve[i], g_curve[i], b_curve[i])
                # Manipulate illumination and convert back to sRGB
                (r_curve[i], _g, _b) = ciexyy_to_srgb(x, y, Y * r)
                (_r, g_curve[i], _b) = ciexyy_to_srgb(x, y, Y * g)
                (_r, _g, b_curve[i]) = ciexyy_to_srgb(x, y, Y * b)


def linearise(r = True, g = ..., b = ...):
    '''
    Convert the curves from formatted in standard RGB to linear RGB
    
    @param  r:bool      Whether to convert the red colour curve
    @param  g:bool|...  Whether to convert the green colour curve, defaults to `r` if `...`
    @param  b:bool|...  Whether to convert the blue colour curve, defaults to `g` if `...`
    '''
    # Handle overloading
    if g is ...:  g = r
    if b is ...:  b = g
    # Convert colour space
    for i in range(i_size):
        # Get values in sRGB
        sr, sg, sb = r_curve[i], g_curve[i], b_curve[i]
        # Get values in linear RGB
        (lr, lg, lb) = standard_to_linear(sr, sg, sb)
        # Convert selected components
        r_curve[i], g_curve[i], b_curve[i] = (lr if r else sr), (lg if g else sg), (lb if b else sb)


def standardise(r = True, g = ..., b = ...):
    '''
    Convert the curves from formatted in linear RGB to standard RGB
    
    @param  r:bool      Whether to convert the red colour curve
    @param  g:bool|...  Whether to convert the green colour curve, defaults to `r` if `...`
    @param  b:bool|...  Whether to convert the blue colour curve, defaults to `g` if `...`
    '''
    # Handle overloading
    if g is ...:  g = r
    if b is ...:  b = g
    # Convert colour space
    for i in range(i_size):
        # Get values in linear RGB
        lr, lg, lb = r_curve[i], g_curve[i], b_curve[i]
        # Get values in sRGB
        (sr, sg, sb) = linear_to_standard(lr, lg, lb)
        # Convert selected components
        r_curve[i], g_curve[i], b_curve[i] = (sr if r else lr), (sg if g else lg), (sb if b else lb)


def gamma(r, g = ..., b = ...):
    '''
    Apply gamma correction on the colour curves
    
    @param  r:float      The gamma parameter for the red curve
    @param  g:float|...  The gamma parameter for the green curve, defaults to `r` if `...`
    @param  b:float|...  The gamma parameter for the blue curve, defaults to `g` if `...`
    '''
    # Handle overloading
    if g is ...:  g = r
    if b is ...:  b = g
    # Manipulate the colour curves
    for (curve, level) in curves(r, g, b):
        # But not if the adjustment is neutral
        if not level == 1.0:
            curve[:] = [y ** (1 / level) for y in curve]

    
def negative(r = True, g = ..., b = ...):
    '''
    Revese the colour curves (negative image with gamma preservation)
    
    @param  r:bool      Whether to invert the red curve
    @param  g:bool|...  Whether to invert the green curve, defaults to `r` if `...`
    @param  b:bool|...  Whether to invert the blue curve, defaults to `g` if `...`
    '''
    # Handle overloading
    if g is ...:  g = r
    if b is ...:  b = g
    # Manipulate the colour curves
    for (curve, setting) in curves(r, g, b):
        # But not if the adjustment is neutral
        if setting:
            curve[:] = reversed(curve)


def rgb_invert(r = True, g = ..., b = ...):
    '''
    Invert the colour curves (negative image with gamma invertion), using sRGB
    
    @param  r:bool      Whether to invert the red curve
    @param  g:bool|...  Whether to invert the green curve, defaults to `r` if `...`
    @param  b:bool|...  Whether to invert the blue curve, defaults to `g` if `...`
    '''
    # Handle overloading
    if g is ...:  g = r
    if b is ...:  b = g
    # Manipulate the colour curves
    for (curve, setting) in curves(r, g, b):
        # But not if the adjustment is neutral
        if setting:
            curve[:] = [1 - y for y in curve]


def cie_invert(r = True, g = ..., b = ...):
    '''
    Invert the colour curves (negative image with gamma invertion), using CIE xyY
    
    @param  r:bool      Whether to invert the red curve
    @param  g:bool|...  Whether to invert the green curve, defaults to `r` if `...`
    @param  b:bool|...  Whether to invert the blue curve, defaults to `g` if `...`
    '''
    # Handle overloading
    if g is ...:  g = r
    if b is ...:  b = g
    # Manipulate the colour curves if any curve should be manipulated
    if r or g or b:
        for i in range(i_size):
            # Convert to CIE xyY
            (x, y, Y) = srgb_to_ciexyy(r_curve[i], g_curve[i], b_curve[i])
            # Invert illumination and convert to back sRGB
            (r_, g_, b_) = ciexyy_to_srgb(x, y, 1 - Y)
            # Apply the new values on the selected channels
            if r:  r_curve[i] = r_
            if g:  g_curve[i] = g_
            if b:  b_curve[i] = b_

    
def sigmoid(r, g = ..., b = ...):
    '''
    Apply S-curve correction on the colour curves.
    This is intended for fine tuning LCD monitors,
    4.5 is good value start start testing at.
    You would probably like to use rgb_limits before
    this to adjust the black point as that is the
    only why to adjust the black point on many LCD
    monitors.
    
    @param  r:float?      The sigmoid parameter for the red curve
    @param  g:float|...?  The sigmoid parameter for the green curve, defaults to `r` if `...`
    @param  b:float|...?  The sigmoid parameter for the blue curve, defaults to `g` if `...`
    '''
    # Handle overloading
    if g is ...:  g = r
    if b is ...:  b = g
    # Manipulate the colour curves
    for (curve, level) in curves(r, g, b):
        # But only on selected channels
        if level is not None:
            for i in range(i_size):
                try:
                    curve[i] = 0.5 - math.log(1 / curve[i] - 1) / level
                except:
                    # Corner cases:
                    #   curve[i] = 0 → 0 -- Division by zero
                    #   curve[i] = 1 → 1 -- Logarithm of zero
                    pass


def rgb_limits(r_min, r_max, g_min = ..., g_max = ..., b_min = ..., b_max = ...):
    '''
    Changes the black point and the white point, using sRGB
    
    @param  r_min:float      The red component value of the black point
    @param  r_max:float      The red component value of the white point
    @param  g_min:float|...  The green component value of the black point, defaults to `r_min`
    @param  g_max:float|...  The green component value of the white point, defaults to `r_max`
    @param  b_min:float|...  The blue component value of the black point, defaults to `g_min`
    @param  b_max:float|...  The blue component value of the white point, defaults to `g_max`
    '''
    # Handle overloading
    if g_min is ...:  g_min = r_min
    if g_max is ...:  g_max = r_max
    if b_min is ...:  b_min = g_min
    if b_max is ...:  b_max = g_max
    # Manipulate the colour curves
    for (curve, (level_min, level_max)) in curves((r_min, r_max), (g_min, g_max), (b_min, b_max)):
        # But not if the adjustments are neutral
        if (level_min != 0) or (level_max != 1):
            curve[:] = [y * (level_max - level_min) + level_min for y in curve]


def cie_limits(r_min, r_max, g_min = ..., g_max = ..., b_min = ..., b_max = ...):
    '''
    Changes the black point and the white point, using CIE xyY
    
    @param  r_min:float      The red component value of the black point
    @param  r_max:float      The red component value of the white point
    @param  g_min:float|...  The green component value of the black point, defaults to `r_min`
    @param  g_max:float|...  The green component value of the white point, defaults to `r_max`
    @param  b_min:float|...  The blue component value of the black point, defaults to `g_min`
    @param  b_max:float|...  The blue component value of the white point, defaults to `g_max`
    '''
    # Handle overloading
    if g_min is ...:  g_min = r_min
    if g_max is ...:  g_max = r_max
    if b_min is ...:  b_min = g_min
    if b_max is ...:  b_max = g_max
    # Check if we can reduce the overhead, we can if the adjustments are identical
    same = (r_min == g_min == b_min) and (r_max == g_max == b_max)
    # Check we need to do any adjustment
    if (not same) or (not r_min == 0) or (not r_max == 0):
        if same:
            # Manipulate all curves in one step if their adjustments are identical
            for i in range(i_size):
                # Convert to CIE xyY
                (x, y, Y) = srgb_to_ciexyy(r_curve[i], g_curve[i], b_curve[i])
                # Manipulate illumination
                Y = Y * (r_max - r_min) + r_min
                # Convert back to sRGB
                (r_curve[i], g_curve[i], b_curve[i]) = ciexyy_to_srgb(x, y, Y)
        else:
            # Manipulate all curves individually if their adjustments are not identical
            for i in range(i_size):
                # Convert to CIE xyY
                (x, y, Y) = srgb_to_ciexyy(r_curve[i], g_curve[i], b_curve[i])
                # Manipulate illumination and convert back to sRGB
                (r_curve[i], _g, _b) = ciexyy_to_srgb(x, y, Y * (r_max - r_min) + r_min)
                (_r, g_curve[i], _b) = ciexyy_to_srgb(x, y, Y * (g_max - g_min) + g_min)
                (_r, _g, b_curve[i]) = ciexyy_to_srgb(x, y, Y * (b_max - b_min) + b_min)


def manipulate(r, g = ..., b = ...):
    '''
    Manipulate the colour curves using a (lambda) function
    
    @param  r:(float)?→float      Function to manipulate the red colour curve
    @param  g:(float)?→float|...  Function to manipulate the green colour curve, defaults to `r` if `...`
    @param  b:(float)?→float|...  Function to manipulate the blue colour curve, defaults to `g` if `...`
    
    `None` means that nothing is done for that subpixel
    
    The lambda functions thats a colour value and maps it to a new colour value.
    For example, if the red value 0.5 is already mapped to 0.25, then if the function
    maps 0.25 to 0.5, the red value 0.5 will revert back to being mapped to 0.5.
    '''
    # Handle overloading
    if g is ...:  g = r
    if b is ...:  b = g
    # Manipulate colour curves
    for (curve, f) in curves(r, g, b):
        # But only for selected channels
        if f is not None:
            curve[:] = [f(y) for y in curve]


def cie_manipulate(r, g = ..., b = ...):
    '''
    Manipulate the colour curves using a (lambda) function on the CIE xyY colour space
    
    @param  r:(float)?→float      Function to manipulate the red colour curve
    @param  g:(float)?→float|...  Function to manipulate the green colour curve, defaults to `r` if `...`
    @param  b:(float)?→float|...  Function to manipulate the blue colour curve, defaults to `g` if `...`
    
    `None` means that nothing is done for that subpixel
    
    The lambda functions thats a colour value and maps it to a new illumination value.
    For example, if the value 0.5 is already mapped to 0.25, then if the function
    maps 0.25 to 0.5, the value 0.5 will revert back to being mapped to 0.5.
    '''
    # Handle overloading
    if g is ...:  g = r
    if b is ...:  b = g
    # Check if we can reduce the overhead, we can if the adjustments are identical
    same = (r is g) and (g is b)
    if same:
        # Manipulate all curves in one step if their adjustments are identical
        if r is not None:
            # But not if the we are not given a function
            for i in range(i_size):
                # Convert to CIE xyY
                (x, y, Y) = srgb_to_ciexyy(r_curve[i], g_curve[i], b_curve[i])
                # Manipulate and convert by to sRGB
                (r_curve[i], g_curve[i], b_curve[i]) = ciexyy_to_srgb(x, y, r(Y))
    elif any(f is not None for f in (r, g, b)):
        # Manipulate all curves individually if their adjustments are not identical
        # if we are given a function for any curve
        for i in range(i_size):
            # Convert to CIE xyY
            (x, y, Y) = srgb_to_ciexyy(r_curve[i], g_curve[i], b_curve[i])
            # Manipulate and convert by to sRGB for selected channels individually
            if r is not None:  (r_curve[i], _g, _b) = ciexyy_to_srgb(x, y, r(Y))
            if g is not None:  (_r, g_curve[i], _b) = ciexyy_to_srgb(x, y, g(Y))
            if b is not None:  (_r, _g, b_curve[i]) = ciexyy_to_srgb(x, y, b(Y))


def lower_resolution(rx_colours = None, ry_colours = None, gx_colours = ..., gy_colours = ..., bx_colours = ..., by_colours = ...):
    '''
    Emulates low colour resolution
    
    @param  rx_colours:int?      The number of colours to emulate on the red encoding axis
    @param  ry_colours:int?      The number of colours to emulate on the red output axis
    @param  gx_colours:int|...?  The number of colours to emulate on the green encoding axis, `rx_colours` if `...`
    @param  gy_colours:int|...?  The number of colours to emulate on the green output axis, `ry_colours` if `...`
    @param  bx_colours:int|...?  The number of colours to emulate on the blue encoding axis, `gx_colours` if `...`
    @param  by_colours:int|...?  The number of colours to emulate on the blue output axis, `gy_colours` if `...`
    
    Where `None` is used the default value will be used, for *x_colours:es that is `i_size`,
    and for *y_colours:es that is `o_size`
    '''
    # Handle overloading
    if gx_colours is ...:  gx_colours = rx_colours
    if gy_colours is ...:  gy_colours = ry_colours
    if bx_colours is ...:  bx_colours = gx_colours
    if by_colours is ...:  by_colours = gy_colours
    # Select default values where default is requested
    if rx_colours is None:  rx_colours = i_size
    if ry_colours is None:  ry_colours = o_size
    if gx_colours is None:  gx_colours = i_size
    if gy_colours is None:  gy_colours = o_size
    if bx_colours is None:  bx_colours = i_size
    if by_colours is None:  by_colours = o_size
    # Combine pair X and Y parameters for each channel
    r_colours = (rx_colours, ry_colours)
    g_colours = (gx_colours, gy_colours)
    b_colours = (bx_colours, by_colours)
    # Manipulate colour curves
    for i_curve, (x_colours, y_colours) in curves(r_colours, g_colours, b_colours):
        # But not if adjustment is neutral
        if (x_colours == i_size) and (y_colours == o_size):
            continue
        o_curve = [0] * i_size
        x_, y_, i_ = x_colours - 1, y_colours - 1, i_size - 1
        for i in range(i_size):
            # Scale encoding
            x = int(i * x_colours / i_size)
            x = int(x * i_ / x_)
            # Scale output
            y = int(i_curve[x] * y_ + 0.5)
            o_curve[i] = y / y_
        i_curve[:] = o_curve


def start_over():
    '''
    Reverts all colours curves to identity mappings.
    This intended for multi-monitor setups with different curves on each monitor.
    If you have a multi-monitor setups without different curves then you have not
    calibrated the monitors or you have awesome monitors that support hardware
    gamma correction.
    '''
    # Reset colour curves
    for i in range(i_size):
        r_curve[i] = g_curve[i] = b_curve[i] = i / (i_size - 1)


def clip(r = True, g = ..., b = ...):
    '''
    Clip all values below the actual minimum and above actual maximums
    
    @param  r:bool      Whether to clip the red colour curve
    @param  g:bool|...  Whether to clip the green colour curve, defaults to `r` if `...`
    @param  b:bool|...  Whether to clip the blue colour curve, defaults to `g` if `...`
    '''
    # Handle overloading
    if g is ...:  g = r
    if b is ...:  b = g
    # Manipulation colour curves
    for curve, action in curves(r, g, b):
        # But only for selected channels
        if action:
            curve[:] = [min(max(0.0, y), 1.0) for y in curve]

