#!/usr/bin/env python3

# Copyright © 2014, 2015, 2016, 2017  Mattias Andrée (m@maandree.se)
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



DATADIR = 'res'
'''
:str  The path to program resources, '/usr/share/blueshift' is standard
'''



# None (except those from the D series) of these
# colour temperatures are exact or guaranteed to
# even be approximate values. A few of them are
# from Wikipedia, others are from very(!)
# questionable sources.

K_F_LUX_W32_EMBER = 1200
'''
The colour temperature in the Windows port of f.lux named ‘ember’
'''

# Warning: f.lux is nasty software that is extremely
#  negative in the freedom dimension. Values are not
#  verified, they are only acquired from f.lux's
#  “Frequently asked questions”.

K_MATCH_FLAME = 1700
'''
Approximate colour temperature of the flame of a match stick

@ref  https://en.wikipedia.org/wiki/Colour_temperature
'''

K_CANDLE_FLAME = 1850
'''
Approximate colour temperature of the flame of a candle

@ref  https://en.wikipedia.org/wiki/Colour_temperature
'''

K_CANDLELIGHT = K_CANDLE_FLAME
'''
Synonym for `K_CANDLE_FLAME`
'''

K_SUNSET = 1850
'''
Approximate colour temperature of the sunset

@ref  https://en.wikipedia.org/wiki/Colour_temperature
'''

K_SUNRISE = K_SUNSET
'''
Approximate colour temperature of the sunrise

@ref  https://en.wikipedia.org/wiki/Colour_temperature
'''

K_F_LUX_W32_CANDLE = 1900
'''
The colour temperature in the Windows port of f.lux named ‘candle’
'''

K_HIGH_PRESSURE_SODIUM = 2100
'''
Approximate colour temperature of high pressure sodium
'''

K_F_LUX_MAC_CANDLE = 2300
'''
The colour temperature in the Mac OS X and iOS port of f.lux named ‘candle’
'''

K_F_LUX_W32_WARM_INCANDESCENT = 2300
'''
The colour temperature in the Windows port of f.lux named ‘warm incandescent’
'''

K_STANDARD_INCANDESCENT = 2500
'''
Approximate colour of standard incandescent
'''

K_INCANDESCENT = K_STANDARD_INCANDESCENT
'''
Synonym for `K_STANDARD_INCANDESCENT`
'''

K_F_LUX_MAC_TUNGSTEN = 2700
'''
The colour temperature in the Mac OS X and iOS port of f.lux named ‘tungsten’
'''

K_F_LUX_W32_INCANDESCENT = 2700
'''
The colour temperature in the Windows port of f.lux named ‘incandescent’
'''

K_EXTRA_SOFT = 2700
'''
A very soft colour temperature
'''

K_PIANO_PIANO_LUX = K_EXTRA_SOFT
'''
Synonym for `K_EXTRA_SOFT` and `K_PIANO_PIANO`
'''

K_PIANO_PIANO = K_PIANO_PIANO_LUX
'''
Synonym for `K_EXTRA_SOFT` and `K_PIANO_PIANO_LUX`
'''

K_INCANDESCENT_LAMP = (2700 + 3300) / 2
'''
Approximate average colour temperature of incandescent lamps

@ref  https://en.wikipedia.org/wiki/Colour_temperature
'''

K_EARLY_SUNRISE = (2800 + 3200) / 2
'''
Approximate average colour temperature the the sunrise at its early stage
'''

K_LATE_SUNSET = K_EARLY_SUNRISE
'''
Approximate average colour temperature the the sunsun at its late stage
'''

K_WARM_WHITE = 3000
'''
Approximate colour temperature of “warm white”
'''

K_SOFT_WHITE_COMPACT_FLOURESCENT_LAMP = 3000
'''
Approximate colour temperature of soft/warm white compact flourescent lamps

@ref  https://en.wikipedia.org/wiki/Colour_temperature
'''

K_WARM_WHITE_COMPACT_FLOURESCENT_LAMP = K_SOFT_WHITE_COMPACT_FLOURESCENT_LAMP
'''
Synonym for `K_SOFT_WHITE_COMPACT_FLOURESCENT_LAMP`
'''

K_HALOGEN_LIGHT = 3000
'''
Approximate colour temperature of halogen light
'''

K_TUNGSTEN_LIGHT = 3200
'''
Approximate colour temperature of tungsten light
(not to be confused with scheelite)
'''

K_HOUSEHOLD_LIGHT_BULB = K_TUNGSTEN_LIGHT
'''
Approximate colour temperature regular household light bulbs
'''

K_LIGHT_BULB = K_HOUSEHOLD_LIGHT_BULB
'''
Synonym for `K_HOUSEHOLD_LIGHT_BULB`
'''

K_STUDIO_LAMP = K_TUNGSTEN_LIGHT
'''
Approximate colour temperature studio lamps

@ref  https://en.wikipedia.org/wiki/Colour_temperature
'''

K_PHOTOFLOOD = K_STUDIO_LAMP
'''
Approximate colour temperature photoflood

@ref  https://en.wikipedia.org/wiki/Colour_temperature
'''

K_STUDIO_CP_LIGHT = 3350
'''
Approximate colour temperature studio ‘CP’ light

@ref  https://en.wikipedia.org/wiki/Colour_temperature
'''

K_F_LUX_MAC_HALOGEN = 3400
'''
The colour temperature in the Mac OS X and iOS port of f.lux named ‘halogen’
'''

K_F_LUX_W32_HALOGEN = 3400
'''
The colour temperature in the Windows port of f.lux named ‘halogen’
'''

K_SOFT = 3700
'''
A soft colour temperature
'''

K_PIANO_LUX = K_SOFT
'''
Synonym for `K_SOFT` and `K_PIANO`
'''

K_PIANO = K_PIANO_LUX
'''
Synonym for `K_SOFT` and `K_PIANO_LUX`
'''

K_MOONLIGHT = (4100 + 4150) / 2
'''
Approximate average colour temperature of moonlight

@ref  https://en.wikipedia.org/wiki/Colour_temperature
'''

K_COOL_WHITE = 4200
'''
Approximate colour temperature of “cool white”
'''

K_F_LUX_MAC_FLOURESCENT = 4200
'''
The colour temperature in the Mac OS X and iOS port of f.lux named ‘flourescent’
'''

K_F_LUX_W32_FLOURESCENT = 4200
'''
The colour temperature in the Windows port of f.lux named ‘flourescent’
'''

K_ELECTRONIC_FLASH_BULB = 4500
'''
Approximate colour temperature of electronic flash bulbs
'''

K_FLASH_BULB = K_ELECTRONIC_FLASH_BULB
'''
Synonym for `K_ELECTRONIC_FLASH_BULB`
'''

K_D50 = 5000
'''
The standard illuminant D50 (5000 K) of the CIE standard illuminant series D
'''

K_NOON_DAYLIGHT = 5000
'''
Approximate colour temperature of noon daylight
'''

K_DIRECT_SUN = K_NOON_DAYLIGHT
'''
Approximate colour temperature of direct sunlight
'''

K_METAL_HALIDE = 5000
'''
Approximate colour temperature of metal halide
'''

K_HORIZON_DAYLIGHT = 5000
'''
Approximate colour temperature of horizon daylight

@ref  https://en.wikipedia.org/wiki/Colour_temperature
'''

K_TUBULAR_FLUORESCENT_LAMP = 5000
'''
Approximate colour temperature of tubular fluorescent lamps

@ref  https://en.wikipedia.org/wiki/Colour_temperature
'''

K_COOL_WHITE_COMPACT_FLUORESCENT_LAMPS = 5000
'''
Approximate colour temperature of cool white/daylight compact fluorescent lamps

@ref  https://en.wikipedia.org/wiki/Colour_temperature
'''

K_DAYLIGHT_WHITE_COMPACT_FLUORESCENT_LAMPS = K_COOL_WHITE_COMPACT_FLUORESCENT_LAMPS
'''
Synonym for `K_COOL_WHITE_COMPACT_FLUORESCENT_LAMPS`
'''

K_F_LUX_MAC_DAYLIGHT = 5000
'''
The colour temperature in the Mac OS X and iOS port of f.lux named ‘daylight’
'''

K_D55 = 5500
'''
The standard illuminant D55 (5500 K) of the CIE standard illuminant series D
'''

K_F_LUX_W32_DAYLIGHT = 5500
'''
The colour temperature in the Windows port of f.lux named ‘daylight’
'''

K_MODERATELY_SOFT = 5500
'''
A moderately soft colour temperature
'''

K_MEZZO_PIANO_LUX = K_MODERATELY_SOFT
'''
Synonym for `K_MODERATELY_SOFT` and `K_MEZZO_PIANO`
'''

K_MEZZO_PIANO = K_MEZZO_PIANO_LUX
'''
Synonym for `K_MODERATELY_SOFT` and `K_MEZZO_PIANO_LUX`
'''

K_CRYSTAL_VERTICAL = 5600
'''
The colour temperature of the standard lighting of
"Kristall, vertikal accent i glas och stål"
(Crystal, vertical accent in glass and steal)

@ref  http://ljusdesign.com/meriter/juryn.htm
'''

K_CLEAR_MID_DAY = 5600
'''
Approximate colour temperature of a clear mid-day
'''

K_VERTICAL_DAYLIGHT = (5500 + 6000) / 2
'''
Approximate average colour temperature of vertical daylight

@ref  https://en.wikipedia.org/wiki/Colour_temperature
'''

K_ELECTRONIC_FLASH = (5500 + 6000) / 2
'''
Approximate average colour temperature of electronic flash

@ref  https://en.wikipedia.org/wiki/Colour_temperature
'''

K_XENON_SHORT_ARC_LAMP = 6200
'''
Approximate colour temperature of xenon short-arc lamp

@ref  https://en.wikipedia.org/wiki/Colour_temperature
'''

K_DAYLIGHT = 6500
'''
Approximate colour temperature of daylight

@ref  https://en.wikipedia.org/wiki/Colour_temperature
'''

K_OVERCAST_DAY = 6500
'''
Approximate colour temperature of daylight during an overcast day

@ref  https://en.wikipedia.org/wiki/Colour_temperature
'''

K_D65 = 6500
'''
The standard illuminant D65 (6500 K) of the CIE standard illuminant series D
'''

K_NEUTRAL = K_D65
'''
Synonym for `K_D65`, the standard colour temperature
'''

K_WHITE = K_NEUTRAL
'''
Synonym for `K_NEUTRAL`
'''

K_MEZZO_LUX = K_NEUTRAL
'''
A moderate colour temperature
'''

K_MEZZO = K_MEZZO_LUX
'''
Synonym for `K_MEZZO_LUX`
'''

K_SHARP = 7000
'''
A sharp colour temperature
'''

K_FORTE_LUX = K_SHARP
'''
Synonym for `K_SHARP` and `K_FORTE`
'''

K_FORTE = K_FORTE_LUX
'''
Synonym for `K_SHARP` and `K_FORTE_LUX`
'''

K_D75 = 7500
'''
The standard illuminant D75 (7500 K) of the CIE standard illuminant series D
'''

K_BLUE_FILTER = 8000
'''
Approximate colour temperature of a standard blue filter
'''

K_NORTH_LIGHT = 10000
'''
Approximate colour temperature of north light
'''

K_BLUE_SKY = K_NORTH_LIGHT
'''
Synonym for `K_NORTH_LIGHT`
'''

K_EXTRA_SHARP = 10000
'''
A very sharp colour temperature
'''

K_FORTE_FORTE_LUX = K_EXTRA_SHARP
'''
Synonym for `K_EXTRA_SHARP` and `K_FORTE_FORTE`
'''

K_FORTE_FORTE = K_FORTE_FORTE_LUX
'''
Synonym for `K_EXTRA_SHARP` and `K_FORTE_FORTE_LUX`
'''

K_SKYLIGHT = (9000 + 15000) / 2
'''
Approximate average colour temperature of the skylight
'''

K_OUTDOOR_SHADE = K_SKYLIGHT
'''
Approximate average colour temperature of an outdoor shade
'''

K_CLEAR_BLUE_POLEWARD_SKY = (15000 + 27000) / 2
'''
Approximate average colour temperature of a clear blue poleward sky

@ref  https://en.wikipedia.org/wiki/Colour_temperature
'''



def series_d(temperature):
    '''
    Calculate the colour for a blackbody temperature
    
    Using `lambda t : divide_by_maximum(series_d(t))` as the algorithm is better than just `series_d`
    
    @param   temperature:float       The blackbody temperature in kelvins, must be inside [4000, 25000]
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
        r = 1.292936186 * (temp - 60) ** -0.1332047592
        g = 1.129890861 * (temp - 60) ** -0.0755148492
    else:
        g = 0.390081579 * math.log(temp) - 0.631841444
        if temp < 66:
            b = 0 if temp <= 19 else 0.543206789 * math.log(temp - 10) - 1.196254089
    r = min(max(0, r), 1)
    g = min(max(0, g), 1)
    b = min(max(0, b), 1)
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
        ceiling = lut[int(temp // temp_step + 1)]
        # Weight
        temp = (temp % temp_step) / temp_step
        # Interpolation
        (x, y) = [c1 * (1 - temp) + c2 * temp for c1, c2 in zip(floor, ceiling)]
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


def kelvins(temperature):
    '''
    Resolve and colour temperature name
    
    @param   temperature:float|str  The colour temperature
    @return  :float                 The colour temperature
    '''
    # If float (or something we do not allow) return the input
    if not isinstance(temperature, str):
        return temperature
    # Replace punctuation with underscore
    temperature = temperature.replace('.', '_').replace('-', '_').replace(' ', '_')
    # Add prefix and turn into upper case
    temperature = 'K_' + temperature.upper()
    # Evaluate (that is, return the named variable)
    return eval(temperature)

