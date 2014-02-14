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
import os

from colour import *
from curve import *


def periodically(year, month, day, hour, minute, second, weekday, fade):
    '''
    Invoked periodically
    
    If you want to control at what to invoke this function next time
    you can set the value of the global variable `wait_period` to the
    number of seconds to wait before invocing this function again.
    
    @param   year:int     The year
    @param   month:int    The month, 1 = January, 12 = December
    @param   day:int      The day, minimum value is 1, probable maximum value is 31 (*)
    @param   hour:int     The hour, minimum value is 0, maximum value is 23
    @param   minute:int   The minute, minimum value is 0, maximum value is 59
    @param   second:int   The second, minimum value is 0, probable maximum value is 60 (**)
    @param   weekday:int  The weekday, 1 = Monday, 7 = Sunday
    @param   fade:float?  Blueshift can use this function to fade into a state when it start
                          or exits. `fade` can either be negative, zero or positive or `None`,
                          but the magnitude of value cannot exceed 1. When Blueshift starts,
                          the this function will be invoked multiple with the time parameters
                          of the time it is invoked and each time `fade` will increase towards
                          1, starting at 0, when the value is 1, the settings should be applied
                          to 100 %. After this this function will be invoked once again with
                          `fade` being `None`. When Blueshift exits the same behaviour is used
                          except, `fade` decrease towards -1 but start slightly below 0, when
                          -1 is reached all settings should be normal. Then Blueshift will NOT
                          invoke this function with `fade` being `None`, instead it will by
                          itself revert all settings and quit.
    
    (*)  Can be exceeded if the calendar system is changed, like in 1712-(02)Feb-30
    (**) See https://en.wikipedia.org/wiki/Leap_second
    '''
    if fade is None:
        temperature(6500, lambda T : divide_by_maximum(series_d(T)), True)
        temperature(6500, lambda T : clip_whitepoint(simple_whitepoint(T)), True)
        temperature(6500, cmf_2deg, True)
        temperature(6500, cmf_10deg, True)
        rgb_contrast(1.0, 1.0, 1.0)
        cie_contrast(1.0)
        rgb_brightness(1.0, 1.0, 1.0)
        cie_brightness(1.0)
        gamma(1.0, 1.0, 1.0)
        sigmoid(None, None, None)
        manipulate(lambda r : r, lambda g : g, lambda b : b)
        clip()



## Set globals accessible by rc
periodically = None
wait_period = 60
global DATADIR, i_size, o_size, r_curve, g_curve, b_curve, clip_result, periodically, wait_period


## Load extension and configurations via ponysayrc
for file in ('$XDG_CONFIG_HOME/%/%rc', '$HOME/.config/%/%rc', '$HOME/.%rc', '/etc/%rc'):
    file = file.replace('%', 'blueshift')
    for arg in ('XDG_CONFIG_HOME', 'HOME'):
        if arg in os.environ:
            print(arg)
            file = file.replace('$' + arg, os.environ[arg].replace('$', '\0'))
        else:
            file = None
            break
    if file is not None:
        file = file.replace('\0', '$')
        if os.path.exists(file):
            code = None
            with open(file, 'rb') as script:
                code = script.read()
            code = code.decode('utf8', 'error') + '\n'
            code = compile(code, file, 'exec')
            exec(code, globals)
            break


## Translate curve from float to integer
for curve in (r_curve, g_curve, b_curve):
    for i in range(i_size):
        curve[i] = int(curve[i] * (o_size - 1) + 0.5)
        if clip_result:
            curve[i] = min(max(0, curve[i]), (o_size - 1))

print(r_curve)
print(g_curve)
print(b_curve)


