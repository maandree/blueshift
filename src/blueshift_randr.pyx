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


cdef extern int blueshift_randr_open(int use_screen, char* display)
'''
Start stage of colour curve control

@param   use_screen  The screen to use
@param   display     The display to use, `NULL` for the current one
@return              Zero on success
'''

cdef extern unsigned short int* blueshift_randr_read(int use_crtc)
'''
Gets the current colour curves

@param   use_crtc  The CRTC to use
@return            {the size of the red curve, *the red curve,
                   the size of the green curve, *the green curve,
                   the size of the blue curve, *the blue curve},
                   needs to be free:d. `NULL` on error.
'''

cdef extern int blueshift_randr_apply(unsigned long long int use_crtcs,
                                      unsigned short int* r_curve,
                                      unsigned short int* g_curve,
                                      unsigned short int* b_curve)
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



cdef unsigned short int* r_c
cdef unsigned short int* g_c
cdef unsigned short int* b_c



def randr_open(int use_screen, display):
    '''
    Start stage of colour curve control
    
    @param   use_screen      The screen to use
    @param   display:bytes?  The display to use, `None` for the current
    @return  :int            Zero on success
    '''
    global r_c, g_c, b_c
    cdef char* display_ = NULL
    if display is not None:
        display_ = display
    r_c = <unsigned short int*>malloc(256 * 2)
    g_c = <unsigned short int*>malloc(256 * 2)
    b_c = <unsigned short int*>malloc(256 * 2)
    if (r_c is NULL) or (g_c is NULL) or (b_c is NULL):
        raise MemoryError()
    return blueshift_randr_open(use_screen, display_)


def randr_read(int use_crtc):
    '''
    Gets the current colour curves
    
    @param   use_crtc                                  The CRTC to use
    @return  :(r:list<int>, g:list<int>, b:list<int>)  The current red, green and blue colour curves
    '''
    cdef unsigned short int* got
    got = blueshift_randr_read(use_crtc)
    if got is NULL:
        raise Exception()
    r, g, b, i = [], [], [], 0
    for c in (r, g, b):
        s = got[i]
        i += 1
        for j in range(s):
            c.append(got[i + j])
        i += s
    free(got)
    return (r, g, b)


def randr_apply(unsigned long long use_crtcs, r_curve, g_curve, b_curve):
    '''
    Apply stage of colour curve control
    
    @param   use_crtcs                         Mask of CRTC:s to use
    @param   r_curve:list<unsigned short int>  The red colour curve
    @param   g_curve:list<unsigned short int>  The green colour curve
    @param   b_curve:list<unsigned short int>  The blue colour curve
    @return                                    Zero on success
    '''
    for i in range(256):
        r_c[i] = r_curve[i] & 0xFFFF
        g_c[i] = g_curve[i] & 0xFFFF
        b_c[i] = b_curve[i] & 0xFFFF
    return blueshift_randr_apply(use_crtcs, r_c, g_c, b_c)


def randr_close():
    '''
    Resource freeing stage of colour curve control
    '''
    free(r_c)
    free(g_c)
    free(b_c)
    blueshift_randr_close()

