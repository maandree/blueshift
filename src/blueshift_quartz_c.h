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
#ifndef BLUESHIFT_QUARTZ_C_H
#define BLUESHIFT_QUARTZ_C_H


#include <stdio.h>
#include <stdlib.h>

#ifdef FAKE_QUARTZ
#  include "fake_quartz.h"
#else
#  include <CoreGraphics/CGDirectDisplay.h>
#  include <CoreGraphics/CGError.h>
#endif


#ifndef FAKE_QUARTZ
#  define close_fake_quartz()  /* Do nothing */
#endif


/**
 * Start stage of colour curve control
 * 
 * @return  Zero on success
 */
int blueshift_quartz_open(void);

/**
 * Get the number of CRTC:s on the system
 * 
 * @return  The number of CRTC:s on the system
 */
int blueshift_quartz_crtc_count(void);

/**
 * Gets the current colour curves
 * 
 * @param   use_crtc  The CRTC to use
 * @return            {the size of the each curve, *the red curve,
 *                    *the green curve, *the blue curve},
 *                    needs to be free:d. `NULL` on error.
 */
uint16_t* blueshift_quartz_read(int use_crtc);

/**
 * Apply stage of colour curve control
 * 
 * @param   use_crtc  The CRTC to use, -1 for all
 * @param   r_curve   The red colour curve
 * @param   g_curve   The green colour curve
 * @param   b_curve   The blue colour curve
 * @return            Zero on success
 */
int blueshift_quartz_apply(int use_crtc, float* r_curves, float* g_curves, float* b_curves);

/**
 * Resource freeing stage of colour curve control
 */
void blueshift_quartz_close(void);

/**
 * Restore all gamma curves (on each and every CRTC on the system)
 * to the settings on ColorSync
 */
void blueshift_quartz_restore(void);


#endif

