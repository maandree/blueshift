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


def linear_to_standard(*colour):
    return [12.92 * c if c <= 0.0031308 else (1 + 0.055) * c ** (1 / 2.4) - 0.055 for c in colour]

def standard_to_linear(*colour):
    return [c / 12.92 if c <= 0.04045 else ((c + 0.055) / (1 + 0.055)) ** 2.4 for c in colour]

def ciexyy_to_ciexyz(x, y, Y):
    return [Y * x / y, Y, Y * (1 - x - y) / y]

def ciexyz_to_ciexyy(X, Y, Z):
    p = -Y / X
    q = 1 + Y / X
    y = 1 / (p / 2 + (p ** 2 / 4 - q) ** 0.5)
    x = X * y / Y
    return [x, y, Y]

def ciexyz_to_linear(X, Y, Z):
    r = 3.2406 * X - 1.5372 * Y - 0.4986 * Z
    g = -0.9689 * X + 1.8758 * Y + 0.0415 * Z
    b = 0.0557 * X - 0.2040 * Y + 1.0570 * Z
    return [r, g, b]

def linear_to_ciexyz(r, g, b):
    X = 0.4124 * r + 0.3576 * g + 0.1805 * b
    Y = 0.2126 * r + 0.7152 * g + 0.0722 * b
    Z = 0.0193 * r + 0.1192 * g + 1.9502 * b
    return [X, Y, Z]

def to_ciexyy(r, g, b):
    (r, g, b) = standard_to_linear(r, g, b)
    (X, Y, Z) = linear_to_ciexyz(r, g, b)
    return ciexyz_to_ciexyy(X, Y, Z)

def to_srgb(x, y, Y):
    (X, Y, Z) = ciexyy_to_ciexyz(x, y, Y)
    (r, g, b) = ciexyz_to_linear(X, Y, Z)
    return linear_to_standard(r, g, b)

