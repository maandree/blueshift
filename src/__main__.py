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


r_curve = [i / 255 for i in range(256)]
g_curve = [i / 255 for i in range(256)]
b_curve = [i / 255 for i in range(256)]


def curves(r, g, b):
    return ((r_curve, r), (g_curve, g), (b_curve, b))


def contrast(r, g, b):
    for (curve, level) in curves(r, g, b):
        if not level == 1.0:
            for i in range(256):
                curve[i] = (curve[i] - 0.5) * level + 0.5

def brightness(r, g, b):
    for (curve, level) in curves(r, g, b):
        if not level == 1.0:
            for i in range(256):
                curve[i] *= level

def gamma(r, g, b):
    for (curve, level) in curves(r, g, b):
        if not level == 1.0:
            for i in range(256):
                curve[i] **= level

def clip():
    for curve in (r_curve, g_curve, b_curve):
        for i in range(256):
            curve[i] = min(max(0.0, curve[i]), 1.0)


contrast(1.0, 1.0, 1.0)
brightness(1.0, 1.0, 1.0)
gamma(1.0, 1.0, 1.0)
temperature(1.0, 1.0, 1.0)
clip()


for curve in (r_curve, g_curve, b_curve):
    for i in range(256):
        curve[i] = int(curve[i] * 65535 + 0.5)
print(r_curve)
print(g_curve)
print(b_curve)

