# -*- python -*-
cdef extern int blueshift_randr_open(int use_screen)
cdef extern int blueshift_randr_apply(unsigned long long int use_crtcs,
                                      unsigned short int r_curve[256],
                                      unsigned short int g_curve[256],
                                      unsigned short int b_curve[256])
cdef extern void blueshift_randr_close()


def randr_open(int use_screen):
    return blueshift_randr_open(use_screen)


def randr_apply(unsigned long long int use_crtcs,
                unsigned short int r_curve[256],
                unsigned short int g_curve[256],
                unsigned short int b_curve[256]):
    return blueshift_randr_apply(use_crtcs, r_curve, g_curve, b_curve)


def randr_close():
    blueshift_randr_close()

