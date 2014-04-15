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


cdef extern int blueshift_w32gdi_open()
'''
Start stage of colour curve control

@return  Zero on success
'''

cdef extern int blueshift_w32gdi_crtc_count()
'''
Get the number of CRTC:s on the system

@return  The number of CRTC:s on the system
'''

cdef extern uint16_t* blueshift_w32gdi_read(int use_crtc)
'''
Gets the current colour curves

@param   use_crtc  The CRTC to use
@return            {the size of the each curve, *the red curve,
                   *the green curve, *the blue curve},
                   needs to be free:d. `NULL` on error.
'''

cdef extern int blueshift_w32gdi_apply(int use_crtc, uint16_t* rgb_curves)
'''
Apply stage of colour curve control

@param   use_crtc   The CRTC to use, -1 for all
@param   rgb_curve  The concatenation of the red, the green and the blue colour curves
@return             Zero on success
'''

cdef extern void blueshift_w32gdi_close()
'''
Resource freeing stage of colour curve control
'''



cdef uint16_t* rgb_c
'''
Storage space for the colour curves in C native data structure
'''



def w32gdi_open():
    '''
    Start stage of colour curve control
    
    @return  :int  Zero on success
    '''
    global rgb_c
    # Allocate the storage space for the C native colour curves
    rgb_c = <uint16_t*>malloc(3 * 256 * sizeof(uint16_t))
    # Check for out-of-memory error
    if (rgb_c is NULL):
        raise MemoryError()
    # Start using W32 GDI
    return blueshift_w32gdi_open()


def w32gdi_read(int use_crtc):
    '''
    Gets the current colour curves
    
    @param   use_crtc                                  The CRTC to use
    @return  :(r:list<int>, g:list<int>, b:list<int>)  The current red, green and blue colour curves
    '''
    cdef uint16_t* got
    # Read the current curves
    got = blueshift_w32gdi_read(use_crtc)
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


def w32gdi_apply(crtc_indices, r_curve, g_curve, b_curve):
    '''
    Apply stage of colour curve control
    
    @param   crtc_indices:list<int>  The indices of the CRTC:s to control, -1 for all
    @param   r_curve:list<int>       The red colour curve
    @param   g_curve:list<int>       The green colour curve
    @param   b_curve:list<int>       The blue colour curve
    @return                          Zero on success
    '''
    # Convert curves to 16-bit C integers
    for i in range(256):
        rgb_c[0 * 256 + i] = r_curve[i] & 0xFFFF
        rgb_c[1 * 256 + i] = g_curve[i] & 0xFFFF
        rgb_c[2 * 256 + i] = b_curve[i] & 0xFFFF
    rc = 0
    # For each selected CRTC,
    for crtc_index in crtc_indices:
        # apply curves.
        rc |= blueshift_w32gdi_apply(crtc_index, rgb_c)
    return rc


def w32gdi_close():
    '''
    Resource freeing stage of colour curve control
    '''
    # Free the storage space for the colour curves
    free(rgb_c)
    # Close free all resources in the native code
    blueshift_w32gdi_close()

