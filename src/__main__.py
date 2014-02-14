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
global DATADIR, i_size, o_size, r_curve, g_curve, b_curve, clip_result


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
            with open(file, 'rb') as script:
                code = script.read().decode('utf8', 'error') + '\n'
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


