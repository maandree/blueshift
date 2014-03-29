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

# This module implements support for colour temperature based
# calculation of white points

import os
import math

from colour import *



# /usr/share/blueshift
DATADIR = 'res'



def series_d(temperature):
    '''
    Calculate the colour for a blackbody temperature
    
    Using `lambda t : divide_by_maximum(series_d(t))` as the algorithm is better than just `series_d`
    
    @param   temperature:float       The blackbody temperature in kelvins, must be inside [4000, 7000]
    @return  :(float, float, float)  The red, green and blue components of the white point
    '''
    # Get coefficients for calculating the x component
    # of the colour in the CIE xyY colour space
    x, ks = 0, (0.244063, 0.09911, 2.9678, -4.6070)
    if temperature > 7000:
        ks = (0.237040, 0.24748, 1.9018, -2.0064)
    # Calculate the x component of the colour in the CIE xyY colour space
    for d, k in enumerate(ks):
        x += k * 10 ** (d * 3) / temperature ** d
    # Calculate the y component of the colour in the CIE xyY colour space
    y = 2.870 * x - 3.000 * x ** 2 - 0.275
    # Convert to sRGB and return, with full illumination
    return ciexyy_to_srgb(x, y, 1.0)


def simple_whitepoint(temperature):
    '''
    Calculate the colour for a blackbody temperature using a simple algorithm
    
    @param   temperature:float       The blackbody temperature in kelvins, not guaranteed for values outside [1000, 40000]
    @return  :(float, float, float)  The red, green and blue components of the white point
    '''
    r, g, b, temp = 1, 1, 1, temperature / 100
    if temp > 66:
        r = 1.292936186 * (temp - 60) ** 0.1332047592
        g = 1.129890861 * (temp - 60) ** -0.0755148492
    else:
        g = 0.390081579 * math.log(temp) - 0.631841444
        if temp < 66:
            b = 0 if temp <= 19 else 0.543206789 * math.log(temp - 10) - 1.196254089
    return (r, g, b)


cmf_2deg_cache = None
def cmf_2deg(temperature):
    '''
    Calculate the colour for a blackbody temperature using raw CIE 1931 2 degree CMF data with interpolation
    
    Using `lambda t : divide_by_maximum(cmf_2deg(t))` as the algorithm is better than just `cmf_2deg`,
    `lambda t : clip_whitepoint(divide_by_maximum(cmf_2deg(t)))` is even better if you plan to use really
    low temperatures,
    
    @param   temperature:float       The blackbody temperature in kelvins, clipped to [1000, 40000]
    @return  :(float, float, float)  The red, green and blue components of the white point
    '''
    global cmf_2deg_cache
    if cmf_2deg_cache is None:
        # Load, parse and cache lookup table if not cached
        cmf_2deg_cache = get_blackbody_lut('2deg')
    # Calculate whitepoint
    return cmf_xdeg(temperature, cmf_2deg_cache)


cmf_10deg_cache = None
def cmf_10deg(temperature):
    '''
    Calculate the colour for a blackbody temperature using raw CIE 1964 10 degree CMF data with interpolation
    
    Using `lambda t : divide_by_maximum(cmf_10deg(t))` as the algorithm is better than just `cmf_10deg`,
    `lambda t : clip_whitepoint(divide_by_maximum(cmf_10deg(t)))` is even better if you plan to use really
    low temperatures,
    
    @param   temperature:float       The blackbody temperature in kelvins, clipped to [1000, 40000]
    @return  :(float, float, float)  The red, green and blue components of the white point
    '''
    global cmf_10deg_cache
    if cmf_10deg_cache is None:
        # Load, parse and cache lookup table if not cached
        cmf_10deg_cache = get_blackbody_lut('10deg')
    # Calculate whitepoint
    return cmf_xdeg(temperature, cmf_10deg_cache)


def cmf_xdeg(temperature, lut, temp_min = 1000, temp_max = 40000, temp_step = 100):
    '''
    Calculate the colour for a blackbody temperature using
    raw data in the CIE xyY colour space with interpolation
    
    This function is intended as help functions for the two functions above this one in this module
    
    @param   temperature:float             The blackbody temperature in kelvins
    @param   lut:list<[x:float, y:float]>  Raw data lookup table
    @param   temp_min:float                The lowest temperature in the lookup table
    @param   temp_max:float                The highest temperature in the lookup table
    @param   temp_step:float               The interval between the temperatures
    @return  :(r:float, g:float, b:float)  The whitepoint in [0, 1] sRGB
    '''
    # Clip temperature to definition domain and remove offset
    x, y, temp = 0, 0, min(max(temp_min, temperature), temp_max) - temp_min
    if temp % temp_step == 0:
        # Exact temperature is included in the lookup table
        (x, y) = lut[int(temp // temp_step)]
    else:
        # x component floor and y component floor
        floor   = lut[int(temp // temp_step)]
        # x component ceiling and y component ceiling
        celiing = lut[int(temp // temp_step + 1)]
        # Weight
        temp = (temp % temp_step) / temp_step
        # Interpolation
        (x, y) = [c1 * (1 - temp) + c2 * temp for c1, c2 in zip(floor, ceilng)]
    # Convert to sRGB
    return ciexyy_to_srgb(x, y, 1.0)


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
    # Retrieve cache
    cache = redshift_old_cache if old_version else redshift_cache
    if cache is None:
        # Load and parse lookup table if not cached
        cache = get_blackbody_lut('redshift_old' if old_version else 'redshift')
        # Cache lookup table
        if old_version:  redshift_old_cache = cache
        else:            redshift_cache = cache
    # Clip to definition domain and remove offset
    temp = min(max(1000, temperature), 10000 if old_version else 25100) - 1000
    r, g, b = 1, 1, 1
    if (temp % 100) == 0:
        # Exact temperature is included in the lookup table
        (r, g, b) = cache[int(temp // 100)]
    else:
        # Floor
        rgb1 = cache[int(temp // 100)]
        # Ceiling
        rgb2 = cache[int(temp // 100 + 1)]
        # Weight
        temp = (temp % 100) / 100
        # Interpolation
        if linear_interpolation:
            (rgb1, rgb2) = [standard_to_linear(*rgb) for rgb in (rgb1, rgb2)]
        (r, g, b) = [c1 * (1 - temp) + c2 * temp for c1, c2 in zip(rgb1, rgb2)]
        if linear_interpolation:
            (r, g, b) = linear_to_standard(r, g, b)
    return (r, g, b)



def get_blackbody_lut(filename):
    '''
    Load and parse a blackbody data lookup table
    
    This function is intended as help functions for the functions above this one in this module
    
    @param   filename:str        The filename of the lookup table
    @return  :list<list<float>>  A float matrix of all values in the lookup table
    '''
    # Load lookup table
    lut = None
    with open(DATADIR + os.sep + filename, 'rb') as file:
        lut = file.read().decode('utf-8', 'error').split('\n')
    # Parse lookup table
    return [[float(cell) for cell in line.split(' ')] for line in lut if not line == '']



def divide_by_maximum(rgb):
    '''
    Divide all colour components by the value of the most prominent colour component
    
    @param   rgb:[float, float, float]  The three colour components
    @return  :[float, float, float]     The three colour components divided by the maximum
    '''
    m = max([abs(x) for x in rgb])
    return rgb if m == 0 else [x / m for x in rgb]


def clip_whitepoint(rgb):
    '''
    Clip all colour components to fit inside [0, 1]
    
    @param   rgb:[float, float, float]  The three colour components
    @return  :[float, float, float]     The three colour components clipped
    '''
    return [min(max(0, x), 1) for x in rgb]

