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


cdef extern int blueshift_vidmode_open(int use_screen, char* display)
cdef extern int blueshift_vidmode_read(int use_crtc,
                                       unsigned short int* r_curve,
                                       unsigned short int* g_curve,
                                       unsigned short int* b_curve)
cdef extern int blueshift_vidmode_apply(unsigned long long int use_crtcs,
                                        unsigned short int* r_curve,
                                        unsigned short int* g_curve,
                                        unsigned short int* b_curve)
cdef extern void blueshift_vidmode_close()



cdef int vidmode_gamma_size
vidmode_gamma_size = 0

cdef unsigned short int* r_c
cdef unsigned short int* g_c
cdef unsigned short int* b_c
r_c = <unsigned short int*>malloc(256 * 2)
g_c = <unsigned short int*>malloc(256 * 2)
b_c = <unsigned short int*>malloc(256 * 2)
if (r_c is NULL) or (g_c is NULL) or (b_c is NULL):
    raise MemoryError()



def vidmode_open(int use_screen, display):
    '''
    Start stage of colour curve control
    
    @param   use_screen      The screen to use
    @param   display:bytes?  The display to use, `None` for the current
    @return  :bool           Whether call was successful
    '''
    global vidmode_gamma_size
    cdef char* display_ = NULL
    if display is not None:
        display_ = display
    vidmode_gamma_size = blueshift_vidmode_open(use_screen, display_)
    return vidmode_gamma_size > 1


def vidmode_read(int use_crtc):
    '''
    Gets the current colour curves
    
    @param   use_crtc                                  The CRTC to use
    @return  :(r:list<int>, g:list<int>, b:list<int>)  The current red, green and blue colour curves
    '''
    if not blueshift_vidmode_read(use_crtc, r_c, g_c, b_c) == 0:
        raise Exception()
    r, g, b = [], [], []
    for i in range(vidmode_gamma_size):
        r.append(r_c[i])
        g.append(g_c[i])
        b.append(b_c[i])
    return (r, g, b)


def vidmode_apply(unsigned long long use_crtcs, r_curve, g_curve, b_curve):
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
    return blueshift_vidmode_apply(use_crtcs, r_c, g_c, b_c)


def vidmode_close():
    '''
    Resource freeing stage of colour curve control
    '''
    free(r_c)
    free(g_c)
    free(b_c)
    blueshift_vidmode_close()

