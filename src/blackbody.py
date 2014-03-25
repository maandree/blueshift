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
        x = x1 * (1 - temp) + x2 * temp
        y = y1 * (1 - temp) + y2 * temp
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
        x = x1 * (1 - temp) + x2 * temp
        y = y1 * (1 - temp) + y2 * temp
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
        r = r1 * (1 - temp) + r2 * temp
        g = g1 * (1 - temp) + g2 * temp
        b = b1 * (1 - temp) + b2 * temp
        if linear_interpolation:
            (r, g, b) = linear_to_standard(r, g, b)
    return (r, g, b)



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

