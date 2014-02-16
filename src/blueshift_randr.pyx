# -*- python -*-
cimport cython
from libc.stdlib cimport malloc, free


cdef extern int blueshift_randr_open(int use_screen)
cdef extern int blueshift_randr_apply(unsigned long long int use_crtcs,
                                      unsigned short int* r_curve,
                                      unsigned short int* g_curve,
                                      unsigned short int* b_curve)
cdef extern void blueshift_randr_close()


def randr_open(int use_screen):
    return blueshift_randr_open(use_screen)


def randr_apply(unsigned long long use_crtcs, r_curve, g_curve, b_curve):
    cdef unsigned short int* r
    cdef unsigned short int* g
    cdef unsigned short int* b
    r = <unsigned short int*>malloc(256 * 2)
    g = <unsigned short int*>malloc(256 * 2)
    b = <unsigned short int*>malloc(256 * 2)
    if (r is NULL) or (g is NULL) or (b is NULL):
        raise MemoryError()
    for i in range(256):
        r[i] = r_curve[i]
        g[i] = g_curve[i]
        b[i] = b_curve[i]
    rc = blueshift_randr_apply(use_crtcs, r, g, b)
    free(r)
    free(g)
    free(b)
    return rc


def randr_close():
    blueshift_randr_close()

