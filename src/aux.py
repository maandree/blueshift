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

# This module contains auxiliary function.

from curve import *


def translate_to_integers():
    '''
    Translate the curves from float to integer
    
    @return  :(r:list<int>, g:list<int>, b:list<int>)  The red curve, the green curve and,
                                                       the blue curve mapped to integers
    '''
    R_curve, G_curve, B_curve = [0] * i_size, [0] * i_size, [0] * i_size
    for i_curve, o_curve in ((r_curve, R_curve), (g_curve, G_curve), (b_curve, B_curve)):
        for i in range(i_size):
            o_curve[i] = int(i_curve[i] * (o_size - 1) + 0.5)
            if clip_result:
                o_curve[i] = min(max(0, o_curve[i]), (o_size - 1))
    return (R_curve, G_curve, B_curve)


def ramps_to_function(r, g, b):
    '''
    Convert a three colour curves to a function that applies those adjustments
    
    @param   r:list<int>  The red colour curves as [0, 65535] integers
    @param   g:list<int>  The green colour curves as [0, 65535] integers
    @param   b:list<int>  The blue colour curves as [0, 65535] integers
    @return  :()→void     Function to invoke to apply the curves that the parameters [r, g and b] represents
    '''
    fp = lambda c : [y / 65535 for y in c]
    return functionise((fp(r), fp(g), fp(b)))


def linearly_interpolate_ramp(r, g, b): # TODO demo and document this
    '''
    Linearly interpolate ramps to the size of the output axes
    
    @param   r:list<float>                                   The red colour curves
    @param   g:list<float>                                   The green colour curves
    @param   b:list<float>                                   The blue colour curves
    @return  :(r:list<float>, g:list<float>, b:list<float>)  The input parameters extended to sizes of `o_size`,
                                                             or their original size, whatever is larger.
    '''
    C = lambda c : c[:] if len(c) >= o_size else ([None] * o_size)
    R, G, B = C(r), C(g), C(b)
    for small, large in ((r, R), (g, G), (b, B)):
        small_, large_ = len(small) - 1, len(large) - 1
        # Only interpolate if scaling up
        if large_ > small_:
            for i in range(len(large)):
                # Scaling
                j = i * small_ / large_
                # Floor, weight, ceiling
                j, w, k = int(j), j % 1, min(int(j) + 1, small_)
                # Interpolation
                large[i] = small[j] * (1 - w) + small[k] * w
    return (R, G, B)


def polynomially_interpolate_ramp(r, g, b): # TODO Speedup, demo and document this
    '''
    Polynomially interpolate ramps to the size of the output axes.
    
    This function will replace parts of the result with linear interpolation
    where local monotonicity have been broken. That is, there is a local
    maximum or local minimum generated between two reference points, linear
    interpolation will be used instead between those two points.
    
    @param   r:list<float>                                   The red colour curves
    @param   g:list<float>                                   The green colour curves
    @param   b:list<float>                                   The blue colour curves
    @return  :(r:list<float>, g:list<float>, b:list<float>)  The input parameters extended to sizes of `o_size`,
                                                             or their original size, whatever is larger.
    '''
    C = lambda c : c[:] if len(c) >= o_size else ([None] * o_size)
    R, G, B, linear = C(r), C(g), C(b), None
    for ci, (small, large) in enumerate(((r, R), (g, G), (b, B))):
        small_, large_ = len(small) - 1, len(large) - 1
        # Only interpolate if scaling up
        if large_ > small_:
            n = len(small)
            ## Construct interpolation matrix (TODO this is not working correctly)
            M = [[small[y] ** i for i in range(n)] for y in range(n)]
            A = [x / small_ for x in range(n)]
            ## Eliminate interpolation matrix
            # (XXX this can be done faster by utilising the fact that we have a Vandermonde matrix)
            # Eliminiate lower left
            for k in range(n - 1):
                for i in range(k + 1, n):
                    m = M[i][k] / M[k][k]
                    M[i][k + 1:] = [M[i][j] - M[k][j] * m for j in range(k + 1, n)]
                    A[i] -= A[k] * m
            # Eliminiate upper right
            for k in reversed(range(n)):
                A[:k] = [A[i] - A[k] * M[i][k] / M[k][k] for i in range(k)]
            # Eliminiate diagonal
            A = [A[k] / M[k][k] for k in range(n)]
            ## Construct interpolation function
            f = lambda x : sum(A[i] * x ** i for i in range(n))
            ## Apply interpolation
            large[:] = [f(x / large_) for x in range(len(large))]
            
            ## Check local monotonicity
            for i in range(small_):
                # Small curve
                x1, x2, y1, y2 = i, i + 1, small[i], small[i + 1]
                # Scaled up curve
                X1, X2 = int(x1 * large_ / small_), int(x2 * large_ / small_)
                Y1, Y2 = large[X1], large[X2]
                monotone = True
                if y2 == y1:
                    # Flat part, just make sure it is flat in the interpolation
                    # without doing a check before.
                    for x in range(X1, X2 + 1):
                        large[x] = y1
                elif y2 > y1:
                    # Increasing
                    monotone = all(map(lambda x : large[x + 1] >= large[x], range(X1, X2))) and (Y2 > Y1)
                elif y2 < y1:
                    # Decreasing
                    monotone = all(map(lambda x : large[x + 1] <= large[x], range(X1, X2))) and (Y2 < Y1)
                # If the monotonicity has been broken,
                if not monotone:
                    print('failed')
                    # replace the partition with linear interpolation.
                    # If linear interpolation has not yet been calculated,
                    if linear is None:
                        # then calculate it.
                        linear = linearly_interpolate_ramp(r, g, b)
                    # Extract the linear interpolation for the current colour curve,
                    # and replace the local partition with the linear interpolation.
                    large[X1 : X2 + 1] = linear[ci][X1 : X2 + 1]
    return (R, G, B)


def functionise(rgb):
    '''
    Convert a three colour curves to a function that applies those adjustments
    
    @param   rgb:(r:list<float>, g:list<float>, b:list<float>)  The colour curves as [0, 1] values
    @return  :()→void                                           Function to invoke to apply the curves
                                                                that the parameters [r, g and b] represents
    '''
    def fcurve(R_curve, G_curve, B_curve):
        for curve, cur in curves(R_curve, G_curve, B_curve):
            for i in range(i_size):
                # Nearest neighbour
                y = int(curve[i] * (len(cur) - 1) + 0.5)
                # Truncation to actual neighbour 
                y = min(max(0, y), len(cur) - 1)
                # Remapping
                curve[i] = cur[y]
    return lambda : fcurve(*rgb)


def store():
    '''
    Store the current adjustments
    
    @return  :(r:list<float>, g:list<float>, b:list<float>)  The colour curves
    '''
    return (r_curve[:], g_curve[:], b_curve[:])


def restore(rgb):
    '''
    Discard any currently applied adjustments and apply stored adjustments
    
    @param  rgb:(r:list<float>, g:list<float>, b:list<float>)  The colour curves to restore
    '''
    (r_curve[:], g_curve[:], b_curve[:]) = rgb

