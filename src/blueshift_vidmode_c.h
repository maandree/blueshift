/**
 * Copyright © 2014  Mattias Andrée (maandree@member.fsf.org)
 * 
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 * 
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 * 
 * You should have received a copy of the GNU General Public License
 * along with this program.  If not, see <http://www.gnu.org/licenses/>.
 */
#ifndef BLUESHIFT_VIDMODE_C_H
#define BLUESHIFT_VIDMODE_C_H


#include <stdlib.h>
#include <stdio.h>
#include <inttypes.h>

#include <X11/Xlib.h>
#include <X11/extensions/xf86vmode.h>



/**
 * Start stage of colour curve control
 * 
 * @param   use_screen  The screen to use
 * @return              Zero on error, otherwise the size of colours curves
 */
int blueshift_vidmode_open(int use_screen);

/**
 * Gets the current colour curves
 * 
 * @param   use_crtc  The CRTC to use
 * @param   r_gamma   Storage location for the red colour curve
 * @param   g_gamma   Storage location for the green colour curve
 * @param   b_gamma   Storage location for the blue colour curve
 * @return            Zero on success
 */
int blueshift_vidmode_read(int use_crtc, uint16_t* r_gamma, uint16_t* g_gamma, uint16_t* b_gamma);

/**
 * Apply stage of colour curve control
 * 
 * @param   use_crtcs  Mask of CRTC:s to use
 * @param   r_curve    The red colour curve
 * @param   g_curve    The green colour curve
 * @param   b_curve    The blue colour curve
 * @return             Zero on success
 */
int blueshift_vidmode_apply(uint64_t use_crtcs, uint16_t* r_curve, uint16_t* g_curve, uint16_t* b_curve);

/**
 * Resource freeing stage of colour curve control
 */
void blueshift_vidmode_close(void);


#endif

