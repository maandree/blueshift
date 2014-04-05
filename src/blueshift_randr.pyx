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


cdef extern int blueshift_randr_open(int use_screen, char* display)
'''
Start stage of colour curve control

@param   use_screen  The screen to use
@param   display     The display to use, `NULL` for the current one
@return              Zero on success
'''

cdef extern uint16_t* blueshift_randr_read(int use_crtc)
'''
Gets the current colour curves

@param   use_crtc  The CRTC to use
@return            {the size of the red curve, *the red curve,
                   the size of the green curve, *the green curve,
                   the size of the blue curve, *the blue curve},
                   needs to be free:d. `NULL` on error.
'''

cdef extern int blueshift_randr_apply(unsigned long long int use_crtcs,
                                      uint16_t* r_curve, uint16_t* g_curve, uint16_t* b_curve)
'''
Apply stage of colour curve control

@param   use_crtcs  Mask of CRTC:s to use
@param   r_curve    The red colour curve
@param   g_curve    The green colour curve
@param   b_curve    The blue colour curve
@return             Zero on success
'''

cdef extern void blueshift_randr_close()
'''
Resource freeing stage of colour curve control
'''



cdef uint16_t* r_c
'''
Storage space for the red colour curve in C native data structure
'''

cdef uint16_t* g_c
'''
Storage space for the green colour curve in C native data structure
'''

cdef uint16_t* b_c
'''
Storage space for the blue colour curve in C native data structure
'''



def randr_open(int use_screen, display):
    '''
    Start stage of colour curve control
    
    @param   use_screen      The screen to use
    @param   display:bytes?  The display to use, `None` for the current
    @return  :int            Zero on success
    '''
    global r_c, g_c, b_c
    # Get the display to use
    cdef char* display_ = NULL
    if display is not None:
        display_ = display
    # Allocate the storage space for the C native colour curves
    r_c = <uint16_t*>malloc(256 * sizeof(uint16_t))
    g_c = <uint16_t*>malloc(256 * sizeof(uint16_t))
    b_c = <uint16_t*>malloc(256 * sizeof(uint16_t))
    # Check for out-of-memory error
    if (r_c is NULL) or (g_c is NULL) or (b_c is NULL):
        raise MemoryError()
    # Start using RandR for the screen and display
    return blueshift_randr_open(use_screen, display_)


def randr_read(int use_crtc):
    '''
    Gets the current colour curves
    
    @param   use_crtc                                  The CRTC to use
    @return  :(r:list<int>, g:list<int>, b:list<int>)  The current red, green and blue colour curves
    '''
    cdef uint16_t* got
    # Read the current curves
    got = blueshift_randr_read(use_crtc)
    if got is NULL:
        raise Exception()
    # Convert to Python integer lists
    r, g, b, i = [], [], [], 0
    for c in (r, g, b):
        # while extracting the sizes of the curves
        s = got[i]
        i += 1
        for j in range(s):
            c.append(got[i + j])
        i += s
    # Free the native curves
    free(got)
    return (r, g, b)


def randr_apply(unsigned long long use_crtcs, r_curve, g_curve, b_curve):
    '''
    Apply stage of colour curve control
    
    @param   use_crtcs          Mask of CRTC:s to use
    @param   r_curve:list<int>  The red colour curve
    @param   g_curve:list<int>  The green colour curve
    @param   b_curve:list<int>  The blue colour curve
    @return                     Zero on success
    '''
    # Convert curves to 16-bit C integers
    for i in range(256):
        r_c[i] = r_curve[i] & 0xFFFF
        g_c[i] = g_curve[i] & 0xFFFF
        b_c[i] = b_curve[i] & 0xFFFF
    # Apply curves
    return blueshift_randr_apply(use_crtcs, r_c, g_c, b_c)


def randr_close():
    '''
    Resource freeing stage of colour curve control
    '''
    # Free the storage space for the colour curves
    free(r_c)
    free(g_c)
    free(b_c)
    # Close free all resources in the native code
    blueshift_randr_close()

