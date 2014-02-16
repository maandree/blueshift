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
import sys
import time
import signal
import datetime

from curve import *
from colour import *
from monitor import *


config_file = None


## Set globals variables
global DATADIR, i_size, o_size, r_curve, g_curve, b_curve, clip_result
global periodically, wait_period, monitor_controller, running


def periodically(year, month, day, hour, minute, second, weekday, fade):
    fadein_time = None
    fadeout_time = None
    fadein_steps = 100
    fadeout_steps = 100
    if fade is None:
        negative(False, False, False)
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
        randr(1, 2)



periodically = None
'''
:(int, int, int, int, int, int, int, float?)?→void  Place holder for periodically invoked function

Invoked periodically

If you want to control at what to invoke this function next time
you can set the value of the global variable `wait_period` to the
number of seconds to wait before invoking this function again.
The value does not need to be an integer.

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

wait_period = 60
'''
:float  The number of seconds to wait before invoking `periodically` again
'''

monitor_controller = lambda : randr()
'''
:()→void  Function used by Blueshift on exit to apply reset colour curves
'''

fadein_time = 10
'''
:float?  The number of seconds used to fade in on start, `None` for no fading
'''

fadeout_time = 10
'''
:float?  The number of seconds used to fade out on exit, `None` for no fading
'''

fadein_steps = 100
'''
:int  The number of steps in the fade in phase, if any
'''

fadeout_steps = 100
'''
:int  The number of steps in the fade out phase, if any
'''

running = True
'''
:bool  `True` while to program has not received a terminate signal
'''


## Load extension and configurations via blueshiftrc
if config_file is None:
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
                config_file = file
if config_file is not None:
    code = None
    with open(file, 'rb') as script:
        code = script.read()
    code = code.decode('utf8', 'error') + '\n'
    code = compile(code, file, 'exec')
    exec(code, globals)
    break
else:
    print('No configuration file found')
    sys.exit(1)


## Run periodically if configured to
if periodically is not None:
    def p(t, fade = None):
        wd = t.isocalendar()[2]
        periodically(t.year, t.month, t.day, t.hour, t.minute, t.second, wd, fade)
    
    ## Catch TERM signal
    def signal_SIGTERM(signum, frame):
        if not running:
            running = False
            start_over()
            monitor_controller()
            sys.exit(0)
        running = False
    signal.signal(signal.SIGTERM, signal_SIGTERM)
    
    ## Fade in
    early_exit = False
    ftime = 0
    if fadein_time is not None:
        dtime = fadein_time / fadein_steps
        while running:
            ftime += dtime
            if ftime > 1:
                break
            p(datetime.datetime.now(), ftime)
    
    ## Run periodically
    if not early_exit:
        while running:
            p(datetime.datetime.now(), None)
            if running:
                time.sleep(wait_period)
    
    ## Fade out
    if fadeout_time is not None:
        dtime = fadeout_time / fadeout_steps
        if early_exit:
            ftime = 1
        while True:
            ftime -= dtime
            if ftime <= 0:
                break
            p(datetime.datetime.now(), -ftime)
    
    ## Reset
    start_over()
    monitor_controller()

