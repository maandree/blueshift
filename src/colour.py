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

# This module implements functions from convertions between colour spaces
# and comparion of colours


def linear_to_standard(*colour):
    '''
    Convert [0, 1] linear RGB to [0, 1] sRGB
    
    @param   colour:*float           The red component, the green component, and the blue component
    @return  :[float, float, float]  The red, green and blue components
    '''
    return [12.92 * c if c <= 0.0031308 else (1 + 0.055) * c ** (1 / 2.4) - 0.055 for c in colour]


def standard_to_linear(*colour):
    '''
    Convert [0, 1] sRGB to [0, 1] linear RGB
    
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
    s = X + Y + Z
    return [X / s, Y / s, Y] if not s == 0 else [0, 0, 0]


def matrix_mul_vector(matrix, vector):
    '''
    Multiplies a matrix with a vector
    
    @param   matrix:list<list<int>>  The matrix
    @param   vector:list<int>        The vector
    @return  :list<int>              The resulting vector
    '''
    return [sum([r * v for r, v in zip(row, vector)]) for row in matrix]


ciexyz_to_linear_matrix = [[ 3.240450, -1.537140, -0.4985320],
                           [-0.969266,  1.876010,  0.0415561],
                           [0.0556434, -0.204026,  1.0572300]]
'''
Multiplication matrix to convert from CIE xyY to linear RGB
'''

def ciexyz_to_linear(X, Y, Z):
    '''
    Convert CIE XYZ to [0, 1] linear RGB
    
    @param   X:float                 The X parameter
    @param   Y:float                 The Y parameter
    @param   Z:float                 The Z parameter
    @return  :[float, float, float]  The red, green and blue components
    '''
    return matrix_mul_vector(ciexyz_to_linear_matrix, [X, Y, Z])


linear_to_ciexyz_matrix = [[0.4124564, 0.3575761, 0.1804375],
                           [0.2126729, 0.7151522, 0.0721750],
                           [0.0193339, 0.1191920, 0.9503041]]
'''
Multiplication matrix to convert from linear RGB to CIE xyY
'''

def linear_to_ciexyz(r, g, b):
    '''
    Convert [0, 1] linear RGB to CIE XYZ
    
    @param   r:float                 The red component
    @param   g:float                 The green component
    @param   b:float                 The blue component
    @return  :[float, float, float]  The X, Y and Z parameters
    '''
    return matrix_mul_vector(linear_to_ciexyz_matrix, [r, g, b])


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
    return ciexyz_to_ciexyy(*linear_to_ciexyz(*standard_to_linear(r, g, b)))


def ciexyy_to_srgb(x, y, Y):
    '''
    Convert CIE xyY to [0, 1] sRGB
    
    @param   x:float                 The x parameter
    @param   y:float                 The y parameter
    @param   Y:float                 The Y parameter
    @return  :[float, float, float]  The red, green and blue components
    '''
    return linear_to_standard(*ciexyz_to_linear(*ciexyy_to_ciexyz(x, y, Y)))


def ciexyz_to_cielab(x, y, z):
    '''
    Convert from CIE XYZ to CIE L*a*b*
    
    @param   x:float                 The X parameter
    @param   y:float                 The Y parameter
    @param   z:float                 The Z parameter
    @return  :[float, float, float]  The L*, a* and b* components
    '''
    x /= 0.95047
    z /= 1.08883
    f = lambda c : c ** 1 / 3 if c > 0.00885642 else (7.78 + 703 / 99900) * c + 0.1379310
    l = 116 * f(y) - 16
    a = 500 * (f(x) - f(y))
    b = 200 * (f(y) - f(z))
    return (l, a, b)


def cielab_to_xiexyz(l, a, b):
    '''
    Convert from CIE L*a*b* to CIE XYZ
    
    @param   l:float                 The L* parameter
    @param   a:float                 The a* parameter
    @param   b:float                 The b* parameter
    @return  :[float, float, float]  The X, Y and Z components
    '''
    y = (l + 16) / 116
    x = a / 500 + y
    z = y - b / 200
    f = lambda c : c ** 3 if c ** 3 > 0.00885642 else (c - 0.1379310) / (7.78 + 703 / 99900)
    return [f(c) * m for c, m in zip((x, y, z), (0.95047, 1, 1.08883))]


def delta_e(a, b):
    '''
    Convert the distance (∆E*_ab) between two [0, 1] sRGB colours
    
    @param   a:(float, float, float)  The first colour
    @param   b:(float, float, float)  The second colour
    @return  :float                   The difference
    '''
    standard_to_cielab = lambda x : ciexyz_to_cielab(*linear_to_ciexyz(*standard_to_linear(*a)))
    return sum([(c1 - c2) ** 2 for c1, c2 in zip(standard_to_cielab(a), standard_to_cielab(b))]) ** 0.5

