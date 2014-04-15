# -*- python -*-

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

cimport cython
from libc.stdlib cimport malloc, free
from libc.stdint cimport *


cdef extern int blueshift_quartz_open()
'''
Start stage of colour curve control

@return  Zero on success
'''

cdef extern int blueshift_quartz_crtc_count()
'''
Get the number of CRTC:s on the system

@return  The number of CRTC:s on the system
'''

cdef extern uint16_t* blueshift_quartz_read(int use_crtc)
'''
Gets the current colour curves

@param   use_crtc  The CRTC to use
@return            {the size of the each curve, *the red curve,
                   *the green curve, *the blue curve},
                   needs to be free:d. `NULL` on error.
'''

cdef extern int blueshift_quartz_apply(int use_crtc, float* r_curves, float* g_curves, float* b_curves)
'''
Apply stage of colour curve control

@param   use_crtc  The CRTC to use, -1 for all
@param   r_curve   The red colour curve
@param   g_curve   The green colour curve
@param   b_curve   The blue colour curve
@return            Zero on success
'''

cdef extern void blueshift_quartz_close()
'''
Resource freeing stage of colour curve control
'''



cdef float* r_c
'''
Storage space for the red colour curve in C native data structure
'''

cdef float* g_c
'''
Storage space for the green colour curve in C native data structure
'''

cdef float* b_c
'''
Storage space for the blue colour curve in C native data structure
'''



def quartz_open():
    '''
    Start stage of colour curve control
    
    @return  :int  Zero on success
    '''
    global r_c, g_c, b_c
    # Allocate the storage space for the C native colour curves
    r_c = <float*>malloc(256 * sizeof(float))
    g_c = <float*>malloc(256 * sizeof(float))
    b_c = <float*>malloc(256 * sizeof(float))
    # Check for out-of-memory error
    if (r_c is NULL) or (g_c is NULL) or (b_c is NULL):
        raise MemoryError()
    # Start using Quartz
    return blueshift_quartz_open()


def quartz_crtc_count():
    '''
    Get the number of CRTC:s on the system
    
    @return  The number of CRTC:s on the system
    '''
    return blueshift_quartz_crtc_count()


def quartz_read(int use_crtc):
    '''
    Gets the current colour curves
    
    @param   use_crtc                                  The CRTC to use
    @return  :(r:list<int>, g:list<int>, b:list<int>)  The current red, green and blue colour curves
    '''
    cdef uint16_t* got
    # Read the current curves
    got = blueshift_quartz_read(use_crtc)
    if got is NULL:
        raise Exception()
    # Convert to Python integer lists
    r, g, b, i = [], [], [], 1
    s = got[0]
    for c in (r, g, b):
        # while extracting the sizes of the curves
        for j in range(s):
            c.append(got[i + j])
        i += s
    # Free the native curves
    free(got)
    return (r, g, b)


def quartz_apply(crtc_indices, r_curve, g_curve, b_curve):
    '''
    Apply stage of colour curve control
    
    @param   crtc_indices:list<int>  The indices of the CRTC:s to control, -1 for all
    @param   r_curve:list<float>     The red colour curve
    @param   g_curve:list<float>     The green colour curve
    @param   b_curve:list<float>     The blue colour curve
    @return                          Zero on success
    '''
    # Convert curves to C floats
    for i in range(256):
        r_c[i] = r_curve[i]
        g_c[i] = g_curve[i]
        b_c[i] = b_curve[i]
    rc = 0
    # For each selected CRTC,
    for crtc_index in crtc_indices:
        # apply curves.
        rc |= blueshift_quartz_apply(crtc_index, r_c, g_c, b_c)
    return rc


def quartz_close():
    '''
    Resource freeing stage of colour curve control
    '''
    # Free the storage space for the colour curves
    free(r_c)
    free(g_c)
    free(b_c)
    # Close free all resources in the native code
    blueshift_quartz_close()

