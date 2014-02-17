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
    '''
    Convert [0, 1] linear RGB to [0, 1] sRGB
    
    @param   colour:*float           The red component, the green component, and the blue component
    @return  :[float, float, float]  The red, green and blue components
    '''
    return [12.92 * c if c <= 0.0031308 else (1 + 0.055) * c ** (1 / 2.4) - 0.055 for c in colour]


def standard_to_linear(*colour):
    '''
    Convert [0, 1] sRGB to linear [0, 1] RGB
    
    @param   colour:*float           The red component, the green component, and the blue component
    @return  :[float, float, float]  The red, green and blue components
    '''
    return [c / 12.92 if c <= 0.04045 else ((c + 0.055) / (1 + 0.055)) ** 2.4 for c in colour]


def ciexyy_to_ciexyz(x, y, Y):
    '''
    Convert CIE xyY to CIE XYZ
    
    @param   x:float                 The x parameter
    @param   y:float                 The y parameter
    @param   Y:float                 The Y parameter
    @return  :[float, float, float]  The X, Y and Z parameters
    '''
    return [Y if y == 0 else Y * x / y, Y, Y if y == 0 else Y * (1 - x - y) / y]


def ciexyz_to_ciexyy(X, Y, Z):
    '''
    Convert CIE XYZ to CIE xyY
    
    @param   X:float                 The X parameter
    @param   Y:float                 The Y parameter
    @param   Z:float                 The Z parameter
    @return  :[float, float, float]  The x, y and Y parameters
    '''
    if X + Y + Z == 0:
        return [0, 0, 0]
    y = Y / (X + Y + Z)
    x = X / (X + Y + Z)
    return [x, y, Y]


def ciexyz_to_linear(X, Y, Z):
    '''
    Convert CIE XYZ to [0, 1] linear RGB
    
    @param   X:float                 The X parameter
    @param   Y:float                 The Y parameter
    @param   Z:float                 The Z parameter
    @return  :[float, float, float]  The red, green and blue components
    '''
    r =  3.24156 * X - 1.53767 * Y - 0.49870 * Z
    g = -0.96920 * X + 1.87589 * Y + 0.04155 * Z
    b =  0.05562 * X - 0.20396 * Y + 1.05686 * Z
    return [r, g, b]


def linear_to_ciexyz(r, g, b):
    '''
    Convert [0, 1] linear RGB to CIE XYZ
    
    @param   r:float                 The red component
    @param   g:float                 The green component
    @param   b:float                 The blue component
    @return  :[float, float, float]  The X, Y and Z parameters
    '''
    X = 0.4123160 * r + 0.3576020 * g + 0.1805010 * b
    Y = 0.2126000 * r + 0.7151990 * g + 0.0722016 * b
    Z = 0.0193297 * r + 0.1192040 * g + 0.9506340 * b
    return [X, Y, Z]


def srgb_to_ciexyy(r, g, b):
    '''
    Convert [0, 1] sRGB to CIE xyY
    
    @param   r:float                 The red component
    @param   g:float                 The green component
    @param   b:float                 The blue component
    @return  :[float, float, float]  The x, y and Y parameters
    '''
    if r == g == b == 0:
        return (0.312857, 0.328993, 0)
    rc = standard_to_linear(r, g, b)
    rc = linear_to_ciexyz(*rc)
    rc = ciexyz_to_ciexyy(*rc)
    return rc


def ciexyy_to_srgb(x, y, Y):
    '''
    Convert CIE xyY to [0, 1] sRGB
    
    @param   x:float                 The x parameter
    @param   y:float                 The y parameter
    @param   Y:float                 The Y parameter
    @return  :[float, float, float]  The red, green and blue components
    '''
    rc = ciexyy_to_ciexyz(x, y, Y)
    rc = ciexyz_to_linear(*rc)
    rc = linear_to_standard(*rc)
    return rc

