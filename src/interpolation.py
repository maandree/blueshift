#!/usr/bin/env python3

# Copyright © 2014, 2015, 2016, 2017  Mattias Andrée (m@maandree.se)
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

# This module contains interpolation functions.

from aux import *
from curve import *

# TODO doc: size parameter has been added


def __interpolate(r, g, b, size, interpolate, decimate = None): ## TODO document
    if decimate is None:
        decimate = lambda orig, out : __decimate(orig, out, interpolate)
    if size is None:
        size = (max(o_size, len(r)), max(o_size, len(g)), max(o_size, len(b)))
    elif isinstance(size, int):
        size = (size, size, size)
    if len(r) == size[0]:
        r = r[:]
    elif len(r) > size[0]:
        r = interpolate(r, [None] * size[0])
    else:
        r = decimate(r, [None] * size[0])
    if len(g) == size[1]:
        g = g[:]
    elif len(g) > size[1]:
        g = interpolate(g, [None] * size[1])
    else:
        g = decimate(g, [None] * size[1])
    if len(b) == size[0]:
        b = b[:]
    elif len(b) > size[0]:
        b = interpolate(b, [None] * size[2])
    else:
        b = decimate(b, [None] * size[2])
    return (r, g, b)


def __decimate(orig, out, interpolate): ## TODO document
    pass # TODO


def linearly_interpolate_ramp(r, g, b, size = None):
    '''
    Linearly interpolate ramps to the size of the output axes
    
    @param   r:list<float>                                   The red colour curves
    @param   g:list<float>                                   The green colour curves
    @param   b:list<float>                                   The blue colour curves
    @param   size:int|(r:int, g:int, b:int)?                 Either the size of all output ramps, the size
                                                             if the output ramps individually, or `None` for
                                                             whichever is larger of`o_size` and the size of
                                                             the input ramps
    @return  :(r:list<float>, g:list<float>, b:list<float>)  The input ramps extended to the choosen size
    '''
    def interpolate(orig, out):
        orig_, out_ = len(orig) - 1, len(out) - 1
        for i in range(len(out)):
            # Scaling
            j = i * orig_ / out_
            # Floor, weight, ceiling
            j, w, k = int(j), j % 1, min(int(j) + 1, orig_)
            # Interpolation
            out[i] = orig[j] * (1 - w) + orig[k] * w
    return __interpolate(r, g, b, size, interpolate)


def cubicly_interpolate_ramp(r, g, b, tension = 0, size = None):
    '''
    Interpolate ramps to the size of the output axes using cubic Hermite spline
    
    @param   r:list<float>                                   The red colour curves
    @param   g:list<float>                                   The green colour curves
    @param   b:list<float>                                   The blue colour curves
    @param   tension:float                                   A [0, 1] value of the tension
    @param   size:int|(r:int, g:int, b:int)?                 Either the size of all output ramps, the size
                                                             if the output ramps individually, or `None` for
                                                             whichever is larger of`o_size` and the size of
                                                             the input ramps
    @return  :(r:list<float>, g:list<float>, b:list<float>)  The input ramps extended to the choosen size
    '''
    if size is None:
        size = (max(o_size, len(r)), max(o_size, len(g)), max(o_size, len(b)))
    elif isinstance(size, int):
        size = (size, size, size)
    C = lambda c, i : c[:] if len(c) >= size[i] else ([None] * size[i])
    R, G, B = C(r, 0), C(g, 1), C(b, 2)
    # Basis functions
    #h00 = lambda t : (1 + 2 * t) * (1 - t) ** 2
    h10 = lambda t : t * (1 - t) ** 2
    h01 = lambda t : t ** 2 * (3 - 2 * t)
    h11 = lambda t : t ** 2 * (t - 1)
    def tangent(values, index, last):
        '''
        Calculate the tangent at a point
        
        @param   values:list<float>  Mapping from points to values
        @param   index:int           The point
        @param   last:int            The last point
        @return  :float              The tangent at the point `index`
        '''
        if last == 0:      return 0
        if index == 0:     return values[1] - values[0]
        if index == last:  return values[last] - values[last - 1]
        return (values[index + 1] - values[index - 1]) / 2
    # Tension coefficent
    c_ = 1 - tension
    # Interpolate each curve
    for small, large in ((r, R), (g, G), (b, B)):
        small_, large_ = len(small) - 1, len(large) - 1
        # Only interpolate if scaling up
        if large_ > small_:
            for i in range(len(large)):
                # Scaling
                j = i * small_ / large_
                # Floor, weight, ceiling
                j, w, k = int(j), j % 1, min(int(j) + 1, small_)
                # Points
                pj, pk = small[j], small[k]
                # Tangents
                mj, mk = c_ * tangent(small, j, small_), c_ * tangent(small, k, small_)
                # Interpolation
                large[i] = pj + h10(w) * mj + h01(w) * (pk - pj) + h11(w) * mk
    ## Check local monotonicity
    eliminate_halos(r, g, b, R, G, B)
    return (R, G, B)


def monotonicly_cubicly_interpolate_ramp(r, g, b, tension = 0, size = None):
    '''
    Interpolate ramps to the size of the output axes using
    monotone cubic Hermite spline and the Fritsch–Carlson method
    
    Does not overshoot, but regular cubic interpolation with uses
    linear replacement for overshot areas is better
    
    @param   r:list<float>                                   The red colour curves
    @param   g:list<float>                                   The green colour curves
    @param   b:list<float>                                   The blue colour curves
    @param   tension:float                                   A [0, 1] value of the tension
    @param   size:int|(r:int, g:int, b:int)?                 Either the size of all output ramps, the size
                                                             if the output ramps individually, or `None` for
                                                             whichever is larger of`o_size` and the size of
                                                             the input ramps
    @return  :(r:list<float>, g:list<float>, b:list<float>)  The input ramps extended to the choosen size
    '''
    if size is None:
        size = (max(o_size, len(r)), max(o_size, len(g)), max(o_size, len(b)))
    elif isinstance(size, int):
        size = (size, size, size)
    C = lambda c, i : c[:] if len(c) >= size[i] else ([None] * size[i])
    R, G, B = C(r, 0), C(g, 1), C(b, 2)
    # Basis functions
    #h00 = lambda t : (1 + 2 * t) * (1 - t) ** 2
    h10 = lambda t : t * (1 - t) ** 2
    h01 = lambda t : t ** 2 * (3 - 2 * t)
    h11 = lambda t : t ** 2 * (t - 1)
    def tangent(values, index, last):
        '''
        Calculate the tangent at a point
        
        @param   values:list<float>  Mapping from points to values
        @param   index:int           The point
        @param   last:int            The last point
        @return  :float              The tangent at the point `index`
        '''
        if last == 0:      return 0
        if index == 0:     return values[1] - values[0]
        if index == last:  return values[last] - values[last - 1]
        return (values[index + 1] - values[index - 1]) / 2
    # Tension coefficent
    c_ = 1 - tension
    ## Interpolant selection
    # Compute the slopes of the secant
    # lines between successive points
    ds = [small[i + 1] - small[i] for i in range(small_)]
    # Initialize the tangents at every
    # data point as the average of the secants
    ms = [ds[0]] + [(ds[i - 1] + ds[i]) / 2 for i in range(1, small_)] + [ds[small_ - 1]]
    βlast = 0
    for i in range(small_):
        if ds[i] == 0:
            # Two successive values are equal, ms[i],
            # must be zero to preserve monotonicity,
            # no idea to do further work on them.
            ms[i], βlast = 0, -1
            continue
        # Look for local extremums
        α, β = ms[i] / ds[i], ms[i + 1] / ds[i]
        if (α < 0) or (βlast < 0):
            # Local extremum found,
            # ensure piecewise monotonicity
            ms[i], β = 0, -1
        elif α ** 2 + β ** 2 > 9:
            # Otherwise, prevent overshoot and ensure
            # monotonicity by restricting the (α, β)
            # vector to a circle of radius 3.
            τ = 3 / (α ** 2 + β ** 2) ** 0.5
            ms[i], ms[i + 1] = τ * α * ds[i], τ * β  * ds[i]
        βlast = β
    ## Interpolate each curve
    for small, large in ((r, R), (g, G), (b, B)):
        small_, large_ = len(small) - 1, len(large) - 1
        # Only interpolate if scaling up
        if large_ > small_:
            for i in range(len(large)):
                # Scaling
                j = i * small_ / large_
                # Floor, weight, ceiling
                j, w, k = int(j), j % 1, min(int(j) + 1, small_)
                # Points
                pj, pk = small[j], small[k]
                # Tangents
                mj, mk = c_ * ms[j], c_ * ms[k]
                # Interpolation
                large[i] = pj + h10(w) * mj + h01(w) * (pk - pj) + h11(w) * mk
    return (R, G, B)


def polynomially_interpolate_ramp(r, g, b, size = None): # TODO Speedup, demo and document this
    '''
    Polynomially interpolate ramps to the size of the output axes.
    
    This function will replace parts of the result with linear interpolation
    where local monotonicity have been broken. That is, there is a local
    maximum or local minimum generated between two reference points, linear
    interpolation will be used instead between those two points.
    
    @param   r:list<float>                                   The red colour curves
    @param   g:list<float>                                   The green colour curves
    @param   b:list<float>                                   The blue colour curves
    @param   size:int|(r:int, g:int, b:int)?                 Either the size of all output ramps, the size
                                                             if the output ramps individually, or `None` for
                                                             whichever is larger of`o_size` and the size of
                                                             the input ramps
    @return  :(r:list<float>, g:list<float>, b:list<float>)  The input ramps extended to the choosen size
    '''
    if size is None:
        size = (max(o_size, len(r)), max(o_size, len(g)), max(o_size, len(b)))
    elif isinstance(size, int):
        size = (size, size, size)
    C = lambda c, i : c[:] if len(c) >= size[i] else ([None] * size[i])
    R, G, B, linear = C(r, 0), C(g, 1), C(b, 2), [None]
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
    eliminate_halos(r, g, b, R, G, B)
    return (R, G, B)


def eliminate_halos(r, g, b, R, G, B):
    '''
    Eliminate haloing effects in interpolations
    
    @param  r:list<float>  The original red curve
    @param  g:list<float>  The original green curve
    @param  b:list<float>  The original blue curve
    @param  R:list<float>  The scaled up red curve
    @param  G:list<float>  The scaled up green curve
    @param  B:list<float>  The scaled up blue curve
    '''
    linear = None
    for ci, (small, large) in enumerate(((r, R), (g, G), (b, B))):
        small_, large_ = len(small) - 1, len(large) - 1
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
                # replace the partition with linear interpolation.
                # If linear interpolation has not yet been calculated,
                if linear is None:
                    # then calculate it.
                    linear = linearly_interpolate_ramp(r, g, b)
                # Extract the linear interpolation for the current colour curve,
                # and replace the local partition with the linear interpolation.
                large[X1 : X2 + 1] = linear[ci][X1 : X2 + 1]


def interpolate_function(function, interpolator): ## TODO size=
    '''
    Interpolate a function that applies adjustments from a lookup table
    
    @param   function:()→void                                 The function that applies the adjustments
    @param   interpolator:(list<float>{3})?→[list<float>{3}]  Function that interpolates lookup tables
    @return  :()→void                                         `function` interpolated
    '''
    # Do not interpolation if none is selected
    if interpolator is None:
        return function
    # Store the current adjustments, we
    # will need to apply our own temporary
    # adjustments
    stored = store()
    # Clean any adjustments,
    start_over()
    # and apply those we should interpolate.
    function()
    # Interpolate the adjustments we just
    # made and make a function out of it
    rc = functionise(interpolator(*store()))
    # Restore the adjustments to those
    # that were applied when we started
    restore(stored)
    return rc

