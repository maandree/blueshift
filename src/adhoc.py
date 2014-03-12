#!/usr/bin/env python3

# Copyright © 2014  Mattias Andrée (maandree@member.fsf.org)
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

import sys
import time
import signal
import datetime


## Warn if we are using configuration script arguments
if len(parser.files) > 0:
    print('%s: warning: configuration script arguments are not supported in ad-hoc mode' % sys.argv[0])

## Determine whether we should run in continuous mode
continuous = any(map(lambda a : (a is not None) and (len(a) == 2), settings))
continuous = continuous or (location is not None)

## Select default settings when not specified
d = lambda a, default : [default, default] if a is None else (a * 2 if len(a) == 1 else a)
gammas = d(gammas, "1:1:1")
rgb_brightnesses = d(rgb_brightnesses, "1")
cie_brightnesses = d(cie_brightnesses, "1")
if temperatures is None:
    temperatures = ['3700', '6500']
elif len(temperatures) == 1:
    temperatures *= 2

## Parse string arrays into floating point matrices
settings = [gammas, rgb_brightnesses, cie_brightnesses, temperatures, [location]]
s = lambda f, v : f(v) if v is not None else None
settings = [s(lambda c : [s(lambda x : [float(y) for y in x.split(':')], x) for x in c], c) for c in settings]
[gammas, rgb_brightnesses, cie_brightnesses, temperatures, location] = settings
location = None if location is None else location[0]

## Select method for calculating to what degree the adjustments should be applied
alpha = lambda : 1
if continuous:
    if location is not None:
        alpha = lambda : sun(*location)
    else:
        def alpha_():
            now = datetime.datetime.now()
            hh, mm = now.hour, now.minute + now.second / 60
            if 12 <= hh <= 22:
                return 1 - (hh - 12) / (22 - 12) - mm / 60
            if hh <= 12:
                hh += 22 - 12
            return (hh - 22) / 14 + m / 60
        alpha = alpha_

## Set monitor control
def reduce(f, items):
    '''
    https://en.wikipedia.org/wiki/Fold_(higher-order_function)
    '''
    if len(items) < 2:
        return items
    rc = items[0]
    for i in range(1, len(items)):
        rc = f(rc, items[i])
    return rc
output = reduce(lambda x, y : x + y, [a.split(',') for a in output])
monitor_controller = lambda : randr(*output)

def apply(dayness, pureness):
    '''
    Apply adjustments
    
    @param  dayness:float   The visibility of the sun
    @param  pureness:float  Transitioning progress, 1 for at clean state, 0 for at adjusted state
    '''
    start_over()
    interpol_ = lambda d, p, a, r : d * r + (p[0] * a + p[1] * (1 - a)) * (1 - r)
    interpol = lambda d, p : [interpol_(d, [p[0][i], p[1][i]], dayness, pureness) for i in range(len(p[0]))]
    temperature(*interpol(6500, temperatures), algorithm = lambda t : divide_by_maximum(cmf_10deg(t)))
    rgb_brightness(*interpol(1, rgb_brightnesses))
    cie_brightness(*interpol(1, cie_brightnesses))
    clip()
    gamma(*interpol(1, gammas))
    clip()
    monitor_controller()

if continuous and not doreset:
    ## Continuous mode
    def periodically(year, month, day, hour, minute, second, weekday, fade):
        apply(alpha(), 0 if fade is None else 1 - abs(fade))
else:
    ## One shot mode
    if not panicgate:
        signal.signal(signal.SIGTERM, signal_SIGTERM)
        trans = 0
        while running:
            try:
                apply(alpha(), trans if doreset else 1 - trans)
                trans += 0.05
                time.sleep(0.1)
            except KeyboardInterrupt:
                signal_SIGTERM(0, None)
            if trans >= 1:
                break
    apply(alpha(), 1 if doreset else 0)

