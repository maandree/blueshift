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
# GNU Affero General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

cimport cython
from libc.stdlib cimport malloc, free


cdef extern int blueshift_vidmode_open(int use_screen)
cdef extern unsigned short int* blueshift_vidmode_read(int use_crtc)
cdef extern int blueshift_vidmode_apply(unsigned long long int use_crtcs,
                                      unsigned short int* r_curve,
                                      unsigned short int* g_curve,
                                      unsigned short int* b_curve)
cdef extern void blueshift_vidmode_close()


def vidmode_open(int use_screen):
    '''
    Start stage of colour curve control
    
    @param   use_screen  The screen to use
    @return              Zero on success
    '''
    return blueshift_vidmode_open(use_screen)


def vidmode_read(int use_crtc):
    '''
    Gets the current colour curves
    
    @param   use_crtc                                  The CRTC to use
    @return  :(r:list<int>, g:list<int>, b:list<int>)  The current red, green and blue colour curves
    '''
    cdef unsigned short int* got
    got = blueshift_vidmode_read(use_crtc)
    if got is NULL:
        raise Exception()
    r, g, b, i = [], [], [], 0
    for c in (r, g, b):
        s = got[i]
        i += 1
        for j in range(s):
            c.append(got[i + j])
        i += s
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
    cdef unsigned short int* r
    cdef unsigned short int* g
    cdef unsigned short int* b
    r = <unsigned short int*>malloc(256 * 2)
    g = <unsigned short int*>malloc(256 * 2)
    b = <unsigned short int*>malloc(256 * 2)
    if (r is NULL) or (g is NULL) or (b is NULL):
        raise MemoryError()
    for i in range(256):
        r[i] = r_curve[i] & 0xFFFF
        g[i] = g_curve[i] & 0xFFFF
        b[i] = b_curve[i] & 0xFFFF
    rc = blueshift_vidmode_apply(use_crtcs, r, g, b)
    free(r)
    free(g)
    free(b)
    return rc


def vidmode_close():
    '''
    Resource freeing stage of colour curve control
    '''
    blueshift_vidmode_close()

