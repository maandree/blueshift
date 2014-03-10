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

from colour import *



# /usr/share/blueshift
DATADIR = 'res'

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



def series_d(temperature):
    '''
    Calculate the colour for a blackbody temperature
    
    Using `lambda t : divide_by_maximum(series_d(t))` as the algorithm is better than just `series_d`
    
    @param   temperature:float       The blackbody temperature in kelvins, must be inside [4000, 7000]
    @return  :(float, float, float)  The red, green and blue components of the white point
    '''
    x = 0
    ks = ((0.244063, 0), (0.09911, 1), (2.9678, 2), (-4.6070, 3))
    if temperature > 7000:
        ks = ((0.237040, 0), (0.24748, 1), (1.9018, 2), (-2.0064, 3))
    for (k, d) in ks:
        x += k * 10 ** (d * 3) / temperature ** d
    y = 2.870 * x - 3.000 * x ** 2 - 0.275
    return ciexyy_to_srgb(x, y, 1.0)


def simple_whitepoint(temperature):
    '''
    Calculate the colour for a blackbody temperature using a simple algorithm
    
    @param   temperature:float       The blackbody temperature in kelvins, not guaranteed for values outside [1000, 40000]
    @return  :(float, float, float)  The red, green and blue components of the white point
    '''
    r, g, b = 1, 1, 1
    temp = temperature / 100
    if temp > 66:
        temp -= 60
        r = 1.292936186 * temp ** 0.1332047592
        g = 1.129890861 * temp ** -0.0755148492
    else:
        g = 0.390081579 * math.log(temp) - 0.631841444
        if temp <= 19:
            b = 0
        elif temp < 66:
            b = 0.543206789 * math.log(temp - 10) - 1.196254089
    return (r, g, b)


cmf_2deg_cache = None
def cmf_2deg(temperature):
    '''
    Calculate the colour for a blackbody temperature using raw CIE 1931 2 degree CMF data with interpolation
    
    Using `lambda t : divide_by_maximum(cmf_2deg(t))` as the algorithm is better than just `cmf_2deg`
    
    @param   temperature:float       The blackbody temperature in kelvins, clipped to [1000, 40000]
    @return  :(float, float, float)  The red, green and blue components of the white point
    '''
    global cmf_2deg_cache
    if cmf_2deg_cache is None:
        with open(DATADIR + '/2deg', 'rb') as file:
            cmf_2deg_cache = file.read()
        cmf_2deg_cache = cmf_2deg_cache.decode('utf-8', 'error').split('\n')
        cmf_2deg_cache = filter(lambda x : not x == '', cmf_2deg_cache)
        cmf_2deg_cache = [[float(x) for x in x_y.split(' ')] for x_y in cmf_2deg_cache]
    temp = min(max(1000, temperature), 40000)
    x, y = 0, 0
    if (temp % 100) == 0:
        (x, y) = cmf_2deg_cache[int((temp - 1000) // 100)]
    else:
        temp -= 1000
        (x1, y1) = cmf_2deg_cache[int(temp // 100)]
        (x2, y2) = cmf_2deg_cache[int(temp // 100 + 1)]
        temp = (temp % 100) / 100
        x = x1 * temp + x2 * (1 - temp)
        y = y1 * temp + y2 * (1 - temp)
    return ciexyy_to_srgb(x, y, 1.0)


cmf_10deg_cache = None
def cmf_10deg(temperature):
    '''
    Calculate the colour for a blackbody temperature using raw CIE 1964 10 degree CMF data with interpolation
    
    Using `lambda t : divide_by_maximum(cmf_10deg(t))` as the algorithm is better than just `cmf_10deg`
    
    @param   temperature:float       The blackbody temperature in kelvins, clipped to [1000, 40000]
    @return  :(float, float, float)  The red, green and blue components of the white point
    '''
    global cmf_10deg_cache
    if cmf_10deg_cache is None:
        with open(DATADIR + '/10deg', 'rb') as file:
            cmf_10deg_cache = file.read()
        cmf_10deg_cache = cmf_10deg_cache.decode('utf-8', 'error').split('\n')
        cmf_10deg_cache = filter(lambda x : not x == '', cmf_10deg_cache)
        cmf_10deg_cache = [[float(x) for x in x_y.split(' ')] for x_y in cmf_10deg_cache]
    temp = min(max(1000, temperature), 40000)
    x, y = 0, 0
    if (temp % 100) == 0:
        (x, y) = cmf_10deg_cache[int((temp - 1000) // 100)]
    else:
        temp -= 1000
        (x1, y1) = cmf_10deg_cache[int(temp // 100)]
        (x2, y2) = cmf_10deg_cache[int(temp // 100 + 1)]
        temp = (temp % 100) / 100
        x = x1 * temp + x2 * (1 - temp)
        y = y1 * temp + y2 * (1 - temp)
    return ciexyy_to_srgb(x, y, 1)


redshift_cache, redshift_old_cache = None, None
def redshift(temperature, old_version = False, linear_interpolation = False):
    '''
    Calculate the colour for a blackbody temperature using same data as in the program redshift
    
    @param   temperature:float          The blackbody temperature in kelvins, clipped to [1000, 25100] (100 more kelvins than in redshift)
    @param   old_version:bool           Whether to the method used in redshift<=1.8, in which case
                                        `temperature` is clipped to [1000, 10000] (1 more kelvin than in redshift)
    @param   linear_interpolation:bool  Whether to interpolate one linear RGB instead of sRGB
    @return  :(float, float, float)     The red, green and blue components of the white point
    '''
    global redshift_cache, redshift_old_cache
    cache = None
    if not old_version:
        if redshift_cache is None:
            with open(DATADIR + '/redshift', 'rb') as file:
                redshift_cache = file.read()
            redshift_cache = redshift_cache.decode('utf-8', 'error').split('\n')
            redshift_cache = filter(lambda x : not x == '', redshift_cache)
            redshift_cache = [[float(x) for x in r_g_b.split(' ')] for r_g_b in redshift_cache]
        cache = redshift_cache
    else:
        if redshift_old_cache is None:
            with open(DATADIR + '/redshift_old', 'rb') as file:
                redshift_old_cache = file.read()
            redshift_old_cache = redshift_old_cache.decode('utf-8', 'error').split('\n')
            redshift_old_cache = filter(lambda x : not x == '', redshift_old_cache)
            redshift_old_cache = [[float(x) for x in r_g_b.split(' ')] for r_g_b in redshift_old_cache]
        cache = redshift_old_cache
    temp = min(max(1000, temperature), 10000 if old_version else 25100)
    r, g, b = 1, 1, 1
    if (temp % 100) == 0:
        (r, g, b) = cache[int((temp - 1000) // 100)]
    else:
        temp -= 1000
        (r1, g1, b1) = cache[int(temp // 100)]
        (r2, g2, b2) = cache[int(temp // 100 + 1)]
        temp = (temp % 100) / 100
        if linear_interpolation:
            (r, g, b) = standard_to_linear(r, g, b)
        r = r1 * temp + r2 * (1 - temp)
        g = g1 * temp + g2 * (1 - temp)
        b = b1 * temp + b2 * (1 - temp)
        if linear_interpolation:
            (r, g, b) = linear_to_standard(r, g, b)
    return (r, g, b)



def temperature(temperature, algorithm):
    '''
    Change colour temperature according to the CIE illuminant series D
    
    @param  temperature:float                        The blackbody temperature in kelvins
    @param  algorithm:(float)→(float, float, float)  Algorithm for calculating a white point, for example `series_d` or `simple_whitepoint`
    '''
    if temperature == 6500:
        return
    (r, g, b) = algorithm(temperature)
    rgb_brightness(r, g, b)


def divide_by_maximum(rgb):
    '''
    Divide all colour components by the value of the most prominent colour component
    
    @param   rgb:[float, float, float]  The three colour components
    @return  :[float, float, float]     The three colour components divided by the maximum
    '''
    m = max([abs(x) for x in rgb])
    if m != 0:
        return [x / m for x in rgb]
    return rgb


def clip_whitepoint(rgb):
    '''
    Clip all colour components to fit inside [0, 1]
    
    @param   rgb:[float, float, float]  The three colour components
    @return  :[float, float, float]     The three colour components clipped
    '''
    return [min(max(0, x), 1) for x in rgb]


def rgb_contrast(r, g = None, b = None):
    '''
    Apply contrast correction on the colour curves using sRGB
    
    @param  r:float   The contrast parameter for the red curve
    @param  g:float?  The contrast parameter for the green curve, defaults to `r` if `None`
    @param  b:float?  The contrast parameter for the blue curve, defaults to `r` if `None`
    '''
    if g is None:  g = r
    if b is None:  b = r
    for (curve, level) in curves(r, g, b):
        if not level == 1.0:
            for i in range(i_size):
                curve[i] = (curve[i] - 0.5) * level + 0.5


def cie_contrast(level):
    '''
    Apply contrast correction on the colour curves using CIE xyY
    
    @param  level:float  The brightness parameter
    '''
    if not level == 1.0:
        for i in range(i_size):
            (x, y, Y) = srgb_to_ciexyy(r_curve[i], g_curve[i], b_curve[i])
            (r_curve[i], g_curve[i], b_curve[i]) = ciexyy_to_srgb(x, y, (Y - 0.5) * level + 0.5)


def rgb_brightness(r, g = None, b = None):
    '''
    Apply brightness correction on the colour curves using sRGB
    
    @param  r:float   The brightness parameter for the red curve
    @param  g:float?  The brightness parameter for the green curve, defaults to `r` if `None`
    @param  b:float?  The brightness parameter for the blue curve, defaults to `r` if `None`
    '''
    if g is None:  g = r
    if b is None:  b = r
    for (curve, level) in curves(r, g, b):
        if not level == 1.0:
            for i in range(i_size):
                curve[i] *= level


def cie_brightness(level):
    '''
    Apply brightness correction on the colour curves using CIE xyY
    
    @param  level:float  The brightness parameter
    '''
    if not level == 1.0:
        for i in range(i_size):
            (x, y, Y) = srgb_to_ciexyy(r_curve[i], g_curve[i], b_curve[i])
            (r_curve[i], g_curve[i], b_curve[i]) = ciexyy_to_srgb(x, y, Y * level)


def linearise(r = True, g = None, b = None):
    '''
    Convert the curves from formatted in standard RGB to linear RGB
    
    @param  r:bool   Whether to convert the red colour curve
    @param  g:bool?  Whether to convert the green colour curve, defaults to `r` if `None`
    @param  b:bool?  Whether to convert the blue colour curve, defaults to `r` if `None`
    '''
    if g is None:  g = r
    if b is None:  b = r
    for i in range(i_size):
        sr, sg, sb = r_curve[i], g_curve[i], b_curve[i]
        (lr, lg, lb) = standard_to_linear(sr, sg, sb)
        r_curve[i], g_curve[i], b_curve[i] = (lr if r else sr), (lg if g else sg), (lb if b else sb)


def standardise(r = True, g = None, b = None):
    '''
    Convert the curves from formatted in linear RGB to standard RGB
    
    @param  r:bool   Whether to convert the red colour curve
    @param  g:bool?  Whether to convert the green colour curve, defaults to `r` if `None`
    @param  b:bool?  Whether to convert the blue colour curve, defaults to `r` if `None`
    '''
    if g is None:  g = r
    if b is None:  b = r
    for i in range(i_size):
        lr, lg, lb = r_curve[i], g_curve[i], b_curve[i]
        (sr, sg, sb) = linear_to_standard(lr, lg, lb)
        r_curve[i], g_curve[i], b_curve[i] = (sr if r else lr), (sg if g else lg), (sb if b else lb)


def gamma(r, g = None, b = None):
    '''
    Apply gamma correction on the colour curves
    
    @param  r:float   The gamma parameter for the red curve
    @param  g:float?  The gamma parameter for the green curve, defaults to `r` if `None`
    @param  b:float?  The gamma parameter for the blue curve, defaults to `r` if `None`
    '''
    if g is None:  g = r
    if b is None:  b = r
    for (curve, level) in curves(r, g, b):
        if not level == 1.0:
            for i in range(i_size):
                curve[i] **= 1 / level

    
def negative(r = True, g = None, b = None):
    '''
    Revese the colour curves (negative image with gamma preservation)
    
    @param  r:bool   Whether to invert the red curve
    @param  g:bool?  Whether to invert the green curve, defaults to `r` if `None`
    @param  b:bool?  Whether to invert the blue curve, defaults to `r` if `None`
    '''
    if g is None:  g = r
    if b is None:  b = r
    for (curve, setting) in curves(r, g, b):
        if setting:
            for i in range(i_size // 2):
                j = i_size - 1 - i
                curve[i], curve[j] = curve[j], curve[i]


def rgb_invert(r = True, g = None, b = None):
    '''
    Invert the colour curves (negative image with gamma invertion), using sRGB
    
    @param  r:bool   Whether to invert the red curve
    @param  g:bool?  Whether to invert the green curve, defaults to `r` if `None`
    @param  b:bool?  Whether to invert the blue curve, defaults to `r` if `None`
    '''
    if g is None:  g = r
    if b is None:  b = r
    for (curve, setting) in curves(r, g, b):
        if setting:
            for i in range(i_size):
                curve[i] = 1 - curve[i]


def cie_invert(r = True, g = None, b = None):
    '''
    Invert the colour curves (negative image with gamma invertion), using CIE xyY
    
    @param  r:bool   Whether to invert the red curve
    @param  g:bool?  Whether to invert the green curve, defaults to `r` if `None`
    @param  b:bool?  Whether to invert the blue curve, defaults to `r` if `None`
    '''
    if g is None:  g = r
    if b is None:  b = r
    for (curve, setting) in curves(r, g, b):
        if setting:
            for i in range(i_size):
                (x, y, Y) = srgb_to_ciexyy(r_curve[i], g_curve[i], b_curve[i])
                (r_curve[i], g_curve[i], b_curve[i]) = ciexyy_to_srgb(x, y, 1 - Y)

    
def sigmoid(r, g, b):
    '''
    Apply S-curve correction on the colour curves.
    This is intended for fine tuning LCD monitors,
    4.5 is good value start start testing at.
    You would probably like to use rgb_limits before
    this to adjust the black point as that is the
    only why to adjust the black point on many LCD
    monitors.
    
    @param  r:float?  The sigmoid parameter for the red curve
    @param  g:float?  The sigmoid parameter for the green curve
    @param  b:float?  The sigmoid parameter for the blue curve
    '''
    for (curve, level) in curves(r, g, b):
        if level is not None:
            for i in range(i_size):
                try:
                    curve[i] = 0.5 - math.log(1 / curve[i] - 1) / level
                except:
                    curve[i] = curve[i];


def rgb_limits(r_min, r_max, g_min = None, g_max = None, b_min = None, b_max = None):
    '''
    Changes the black point and the white point, using sRGB
    
    @param  r_min:float   The red component value of the black point
    @param  r_max:float   The red component value of the white point
    @param  g_min:float?  The green component value of the black point, defaults to `r_min`
    @param  g_max:float?  The green component value of the white point, defaults to `r_max`
    @param  b_min:float?  The blue component value of the black point, defaults to `r_min`
    @param  b_max:float?  The blue component value of the white point, defaults to `r_max`
    '''
    if g_min is None:  g_min = r_min
    if g_max is None:  g_max = r_max
    if b_min is None:  b_min = r_min
    if b_max is None:  b_max = r_max
    for (curve, (level_min, level_max)) in curves((r_min, r_max), (g_min, g_max), (b_min, b_max)):
        if (level_min != 0) or (level_max != 1):
            for i in range(i_size):
                curve[i] = curve[i] * (level_max - level_min) + level_min


def cie_limits(level_min, level_max):
    '''
    Changes the black point and the white point, using CIE xyY
    
    @param  level_min:float   The brightness of the black point
    @param  level_max:float   The brightness of the white point
    '''
    if (level_min != 0) or (level_max != 1):
        for i in range(i_size):
            (x, y, Y) = srgb_to_ciexyy(r_curve[i], g_curve[i], b_curve[i])
            Y = Y * (level_max - level_min) + level_min
            (r_curve[i], g_curve[i], b_curve[i]) = ciexyy_to_srgb(x, y, Y)


def manipulate(r, g = None, b = None):
    '''
    Manipulate the colour curves using a lambda function
    
    @param  r:(float)→float   Lambda function to manipulate the red colour curve
    @param  g:(float)?→float  Lambda function to manipulate the green colour curve, defaults to `r` if `None`
    @param  b:(float)?→float  Lambda function to manipulate the blue colour curve, defaults to `r` if `None`
    
    The lambda functions thats a colour value and maps it to a new colour value.
    For example, if the red value 0.5 is already mapped to 0.25, then if the function
    maps 0.25 to 0.5, the red value 0.5 will revert back to being mapped to 0.5.
    '''
    if g is None:  g = r
    if b is None:  b = r
    for (curve, f) in curves(r, g, b):
        for i in range(i_size):
            curve[i] = f(curve[i])


def lower_resolution(rx_colours = None, ry_colours = None, gx_colours = None, gy_colours = None, bx_colours = None, by_colours = None):
    '''
    Emulates low colour resolution
    
    @param  rx_colours:int?  The number of colours to emulate on the red encoding axis, `i_size` if `None`
    @param  ry_colours:int?  The number of colours to emulate on the red output axis, `o_size` if `None`
    @param  gx_colours:int?  The number of colours to emulate on the green encoding axis, `rx_colours` of `None`
    @param  gy_colours:int?  The number of colours to emulate on the green output axis, `ry_colours` if `None`
    @param  bx_colours:int?  The number of colours to emulate on the blue encoding axis, `rx_colours` if `None`
    @param  by_colours:int?  The number of colours to emulate on the blue output axis, `rg_colours` if `None`
    '''
    if rx_colours is None:  rx_colours = i_size
    if ry_colours is None:  ry_colours = o_size
    if gx_colours is None:  gx_colours = rx_colours
    if gy_colours is None:  gy_colours = ry_colours
    if bx_colours is None:  bx_colours = rx_colours
    if by_colours is None:  by_colours = ry_colours
    r_colours = (rx_colours, ry_colours)
    g_colours = (gx_colours, gy_colours)
    b_colours = (bx_colours, by_colours)
    for i_curve, (x_colours, y_colours) in curves(r_colours, g_colours, b_colours):
        if (x_colours == i_size) and (y_colours == o_size):
            continue
        o_curve = [0] * i_size
        x_, y_, i_ = x_colours - 1, y_colours - 1, i_size - 1
        for i in range(i_size):
            x = int(i * x_colours / i_size)
            x = int(x * i_ / x_)
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
    for i in range(i_size):
        v = i / (i_size - 1)
        r_curve[i] = v
        g_curve[i] = v
        b_curve[i] = v


def clip(r = True, g = None, b = None):
    '''
    Clip all values below the actual minimum and above actual maximums
    
    @param  r:bool   Whether to clip the red colour curve
    @param  g:bool?  Whether to clip the green colour curve, defaults to `r` if `None`
    @param  b:bool?  Whether to clip the blue colour curve, defaults to `r` if `None`
    '''
    for curve, action in curves(r, r if g is None else g, r if b is None else b):
        if action:
            for i in range(i_size):
                curve[i] = min(max(0.0, curve[i]), 1.0)

