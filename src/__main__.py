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
from colour import *
from curve import *


#temperature(6500, series_d, True)
#divide_by_maximum()
#temperature(6500, simple_whitepoint, True)
#clip()
#rgb_contrast(1.0, 1.0, 1.0)
#cie_contrast(1.0)
#rgb_brightness(1.0, 1.0, 1.0)
#cie_brightness(1.0)
#gamma(1.0, 1.0, 1.0)
#sigmoid(None, None, None)
#clip()


for curve in (r_curve, g_curve, b_curve):
    for i in range(i_size):
        curve[i] = int(curve[i] * (o_size - 1) + 0.5)
        if clip_result:
            curve[i] = min(max(0, curve[i]), (o_size - 1))
print(r_curve)
print(g_curve)
print(b_curve)


