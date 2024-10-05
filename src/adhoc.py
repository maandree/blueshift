#!/usr/bin/env python3

# Copyright © 2014, 2015, 2016, 2017  Mattias Andrée (m@maandree.se)
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

# This module contains the implementions of the policies for ad-hoc mode.

import sys
import time
import signal
import datetime


## Warn if we are using configuration script arguments
if len(parser.files) > 0:
    print('%s: warning: configuration script arguments are not supported in ad-hoc mode' % sys.argv[0])

## Determine whether we should run in continuous mode
continuous = any(map(lambda a : (a is not None) and (len(a) == 2), settings)) or (location is not None)

## Select default settings when not specified
d = lambda a, default : [default, default] if a is None else (a * 2 if len(a) == 1 else a)
# Set gamma and brightness to 1 (unmodified) if not specified
gammas = d(gammas, '1:1:1')
rgb_brightnesses = d(rgb_brightnesses, '1')
cie_brightnesses = d(cie_brightnesses, '1')
if (rgb_temperatures is None) and (cie_temperatures is None):
    # If temperature is not specified, set the temperature
    # to 3700 K during the day, and 6500 K (neutral) during
    # the night. Do not use CIE xyY, hence set cie_temperatures
    # to 6500 K (neutral).
    rgb_temperatures = ['3500', '5500']
    cie_temperatures = ['6500', '6500']
else:
    # If cie_temperatures is specified but not rgb_temperatures,
    # then set rgb_temperatures to 6500 K. But if rgb_temperatures
    # is indeed specified but only with one value, duplicate that
    # value so that it is used both during day and night.
    if rgb_temperatures is None:
        rgb_temperatures = ['6500', '6500']
    elif len(rgb_temperatures) == 1:
        rgb_temperatures *= 2
    # And vice versa.
    if cie_temperatures is None:
        cie_temperatures = ['6500', '6500']
    elif len(cie_temperatures) == 1:
        cie_temperatures *= 2

## Parse string arrays into floating point matrices
# Pack all settings into an unregulare matrix
settings = [gammas, rgb_brightnesses, cie_brightnesses, rgb_temperatures, cie_temperatures, [location]]
# Parse into a vector-matrix
s = lambda f, v : f(v) if v is not None else None
settings = [s(lambda c : [s(lambda x : [float(y) for y in x.split(':')], x) for x in c], c) for c in settings]
# Unpack settings
[gammas, rgb_brightnesses, cie_brightnesses, rgb_temperatures, cie_temperatures, location] = settings
location = None if location is None else location[0]

## Select method for calculating to what degree the adjustments should be applied
# Assume it is day if not running in continuous mode
alpha = lambda : 1
if continuous:
    if location is not None:
        # If we have a geographical location, determine to
        # what degree it is day from the Sun's elecation
        alpha = lambda : sun(*location)
    else:
        # If we do not have a location, determine to what
        # degree it is day from local time,
        def alpha():
            '''
            This algorithm is very crude.
            It places 100 % day at 12:00 and 100 % night at
            22:00, and only at those exact time points.
            
            @return  :float  [0, 1] floating point of the degree to which it is day
            '''
            now = datetime.datetime.now()
            hh, mm = now.hour, now.minute + now.second / 60
            if 12 <= hh <= 22:
                return 1 - (hh - 12) / (22 - 12) - mm / 60
            return (hh + (10 if hh <= 12 else 0) - 22) / 14 + mm / 60

## Set monitor control
output_ = []
for o in output:
    output_ += [int(x) for x in o.split(',')]
# Use selected CRTC:s (all if none are selected)
# in the first screen or graphics card.
monitor_controller = lambda : (drm if ttymode else randr)(*output_)

# Interpolation between day and night and between pure and adjusted
interpol_ = lambda d, p, a, r : d * r + (p[0] * a + p[1] * (1 - a)) * (1 - r)

def apply(dayness, pureness):
    '''
    Apply adjustments
    
    @param  dayness:float   The visibility of the sun
    @param  pureness:float  Transitioning progress, 1 for at clean state, 0 for at adjusted state
    '''
    # Clean up adjustments from last run
    start_over()
    # Interpolation between day and night and between pure and adjusted
    interpol = lambda d, p : [interpol_(d, [p[0][i], p[1][i]], dayness, pureness) for i in range(len(p[0]))]
    # Apply temperature adjustment
    temperature_algorithm = lambda t : clip_whitepoint(divide_by_maximum(cmf_10deg(t)))
    rgb_temperature(*interpol(6500, rgb_temperatures), algorithm = temperature_algorithm)
    cie_temperature(*interpol(6500, cie_temperatures), algorithm = temperature_algorithm)
    # Apply white point brightness adjustment
    rgb_brightness(*interpol(1, rgb_brightnesses))
    cie_brightness(*interpol(1, cie_brightnesses))
    # Clip values, specifically those under zero to
    # avoid complex numbers, and apply gamma correction
    clip()
    gamma(*interpol(1, gammas))
    # Clip values to avoid unwanted effects on oversaturation
    clip()
    # Apply settings to all selected monitors
    monitor_controller()

if continuous and not doreset:
    ## Continuous mode
    def periodically(_year, _month, _day, _hour, _minute, _second, _weekday, fade):
        '''
        Invoked periodically
        
        @param  fade:float?  Blueshift can use this function to fade into a state when it start
                             or exits. `fade` can either be negative, zero or positive or `None`,
                             but the magnitude of value cannot exceed 1. When Blueshift starts,
                             this function will be invoked multiple with the time parameters
                             of the time it is invoked and each time `fade` will increase towards
                             1, starting at 0, when the value is 1, the settings should be applied
                             to 100 %. After this this function will be invoked once again with
                             `fade` being `None`. When Blueshift exits the same behaviour is used
                             except, `fade` decrease towards -1 but start slightly below 0, when
                             -1 is reached all settings should be normal. Then Blueshift will NOT
                             invoke this function with `fade` being `None`, instead it will by
                             itself revert all settings and quit.
        '''
        apply(alpha(), 0 if fade is None else 1 - abs(fade))
else:
    ## One shot mode
    if not panicgate:
        ## Fade in to settings
        signal.signal(signal.SIGTERM, signal_SIGTERM)
        trans = 0
        while running and (trans < 1):
            try:
                apply(alpha(), trans if doreset else 1 - trans)
                trans += 0.05
                time.sleep(0.1)
            except KeyboardInterrupt:
                signal_SIGTERM(0, None)
    ## Apply or revert settings and exit
    apply(alpha(), 1 if doreset else 0)

