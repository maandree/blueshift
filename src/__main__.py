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


DATADIR = '.'

i_size = 2 ** 8
o_size = 2 ** 16
r_curve = [i / (i_size - 1) for i in range(i_size)]
g_curve = [i / (i_size - 1) for i in range(i_size)]
b_curve = [i / (i_size - 1) for i in range(i_size)]
clip_result = True

cmf_2deg_cache = None
cmf_10deg_cache = None


def curves(r, g, b):
    '''
    Generate a tuple of curve–parameter pairs
    
    @param   r  The red parameter
    @param   g  The green parameter
    @param   b  The blue parameter
    @return     ((r_curve, r), (g_curve, g), (b_curve, b))
    '''
    return ((r_curve, r), (g_curve, g), (b_curve, b))


def series_d(temperature):
    '''
    Calculate the colour for a blackbody temperature
    
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
    return to_srgb(x, y, 1.0)

def simple_whitepoint(temperature):
    '''
    Calculate the colour for a blackbody temperature using a simple, but inaccurate, algorithm
    
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

def cmf_2deg(temperature):
    '''
    Calculate the colour for a blackbody temperature using raw CIE 1931 2 degree CMF data with interpolation
    
    @param   temperature:float       The blackbody temperature in kelvins, clipped to [1000, 40000]
    @return  :(float, float, float)  The red, green and blue components of the white point
    '''
    if cmf_2deg_cache is None:
        with open(DATADIR + '/2deg', 'rb') as file:
            cmf_2deg_cache = file.read()
        cmf_2deg_cache.decode('utf-8', 'error').split('\n')
        cmf_2deg_cache = [[float(x) for x in x_y.split(' ')] for x_y in cmf_2deg_cache]
    temperature = min(max(0, temperature), 1000)
    x, y = 0, 0
    if (temp % 100) == 0:
        (x, y) = temperature[(temp - 1000) // 100]
    else:
        temp -= 1000
        (x1, y1) = temperature[temp // 100]
        (x2, y2) = temperature[temp // 100 + 1]
        temp = (temp % 100) / 100
        x = x1 * temp + x2 * (1 - temp)
        y = y1 * temp + y2 * (1 - temp)
    return to_srgb(x, y, 1.0)

def cmf_10deg(temperature):
    '''
    Calculate the colour for a blackbody temperature using raw CIE 1964 10 degree CMF data with interpolation
    
    @param   temperature:float       The blackbody temperature in kelvins, clipped to [1000, 40000]
    @return  :(float, float, float)  The red, green and blue components of the white point
    '''
    if cmf_2deg_cache is None:
        with open(DATADIR + '/10deg', 'rb') as file:
            cmf_2deg_cache = file.read()
        cmf_2deg_cache.decode('utf-8', 'error').split('\n')
        cmf_2deg_cache = [[float(x) for x in x_y.split(' ')] for x_y in cmf_2deg_cache]
    temperature = min(max(0, temperature), 1000)
    x, y = 0, 0
    if (temp % 100) == 0:
        (x, y) = temperature[(temp - 1000) // 100]
    else:
        temp -= 1000
        (x1, y1) = temperature[temp // 100]
        (x2, y2) = temperature[temp // 100 + 1]
        temp = (temp % 100) / 100
        x = x1 * temp + x2 * (1 - temp)
        y = y1 * temp + y2 * (1 - temp)
    return to_srgb(x, y, 1.0)


def temperature(temperature, algorithm, linear_rgb = True):
    '''
    Change colour temperature according to the CIE illuminant series D
    
    @param  temperature:float                        The blackbody temperature in kelvins
    @param  algorithm:(float)→(float, float, float)  Algorithm for calculating a white point, for example `series_d` or `simple_whitepoint`
    @param  linear_rgb:[bool]                        Whether to use linear RGB, otherwise sRG is used
    '''
    if temperature == 6500:
        return
    (r, g, b) = algorithm(temperature)
    if linear_rgb:
        for curve in (r_curve, g_curve, b_curve):
            for i in range(i_size):
                R, G, B = r_curve[i], g_curve[i], b_curve[i]
                (R, G, B) = standard_to_linear(R, G, B)
                r_curve[i], g_curve[i], b_curve[i] = R, G, B
    rgb_brightness(r, g, b)
    if linear_rgb:
        for curve in (r_curve, g_curve, b_curve):
            for i in range(i_size):
                R, G, B = r_curve[i], g_curve[i], b_curve[i]
                (R, G, B) = linear_to_standard(R, G, B)
                r_curve[i], g_curve[i], b_curve[i] = R, G, B

def divide_by_maximum():
    '''
    Divide all colour components by the value of the most prominent colour component for each colour
    '''
    for i in range(i_size):
        m = max([abs(x) for x in (r_curve[i], g_curve[i], b_curve[i])])
        if m != 0:
            for curve in (r_curve, g_curve, b_curve):
                curve[i] /= m

def rgb_contrast(r, g, b):
    '''
    Apply contrast correction on the colour curves using sRGB
    
    @param  r:float  The contrast parameter for the red curve
    @param  g:float  The contrast parameter for the green curve
    @param  b:float  The contrast parameter for the blue curve
    '''
    for (curve, level) in curves(r, g, b):
        if not level == 1.0:
            for i in range(i_size):
                curve[i] = (curve[i] - 0.5) * level + 0.5

def cie_contrast(level):
    '''
    Apply contrast correction on the colour curves using CIE XYZ
    
    @param  level:float  The brightness parameter
    '''
    if not level == 1.0:
        for i in range(i_size):
            (x, y, Y) = to_ciexyy(r_curve[i], g_curve[i], b_curve[i])
            (r_curve[i], g_curve[i], b_curve[i]) = to_rgb(x, y, Y * level)

def rgb_brightness(r, g, b):
    '''
    Apply brightness correction on the colour curves using sRGB
    
    @param  r:float  The brightness parameter for the red curve
    @param  g:float  The brightness parameter for the green curve
    @param  b:float  The brightness parameter for the blue curve
    '''
    for (curve, level) in curves(r, g, b):
        if not level == 1.0:
            for i in range(i_size):
                curve[i] *= level

def cie_brightness(level):
    '''
    Apply brightness correction on the colour curves using CIE XYZ
    
    @param  level:float  The brightness parameter
    '''
    if not level == 1.0:
        for i in range(i_size):
            (x, y, Y) = to_ciexyy(r_curve[i], g_curve[i], b_curve[i])
            (r_curve[i], g_curve[i], b_curve[i]) = to_rgb(x, y, Y * level)

def gamma(r, g, b):
    '''
    Apply gamma correction on the colour curves
    
    @param  r:float  The gamma parameter for the red curve
    @param  g:float  The gamma parameter for the green curve
    @param  b:float  The gamma parameter for the blue curve
    '''
    for (curve, level) in curves(r, g, b):
        if not level == 1.0:
            for i in range(i_size):
                curve[i] **= level
    
def sigmoid(r, g, b):
    '''
    Apply S-curve correction on the colour curves
    
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
                    curve[i] = 0;

def clip():
    '''
    Clip all values belowed the actual minimum and above actual maximums
    '''
    for curve in (r_curve, g_curve, b_curve):
        for i in range(i_size):
            curve[i] = min(max(0.0, curve[i]), 1.0)


temperature(6500, series_d, True)
divide_by_maximum()
temperature(6500, simple_whitepoint, True)
clip()
rgb_contrast(1.0, 1.0, 1.0)
cie_contrast(1.0)
rgb_brightness(1.0, 1.0, 1.0)
cie_brightness(1.0)
gamma(1.0, 1.0, 1.0)
sigmoid(None, None, None)
clip()


for curve in (r_curve, g_curve, b_curve):
    for i in range(i_size):
        curve[i] = int(curve[i] * (o_size - 1) + 0.5)
        if clip_result:
            curve[i] = min(max(0, curve[i]), (o_size - 1))
print(r_curve)
print(g_curve)
print(b_curve)


