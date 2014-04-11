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
#ifndef BLUESHIFT_RANDR_C_H
#define BLUESHIFT_RANDR_C_H


#include <stdlib.h>
#include <stdio.h>
#include <inttypes.h>

#include <xcb/xcb.h>
#include <xcb/randr.h>



/**
 * The major version of RandR the program expects
 */
#define RANDR_VERSION_MAJOR  1

/**
 * The minor version of RandR the program expects
 */
#define RANDR_VERSION_MINOR  3



/**
 * Data structure for CRTC caches
 */
typedef struct blueshift_randr_crtc
{
  /**
   * Size of colour curves on the X-axis
   */
  uint16_t curve_size;
  
  /**
   * CRT controller
   */
  xcb_randr_crtc_t* crtc;
  
} blueshift_randr_crtc_t;



/**
 * Start stage of colour curve control
 * 
 * @param   use_screen  The screen to use
 * @param   display     The display to use, `NULL` for the current one
 * @return              Zero on success
 */
int blueshift_randr_open(int use_screen, char* display);

/**
 * Gets the current colour curves
 * 
 * @param   use_crtc  The CRTC to use
 * @return            {the size of the red curve, *the red curve,
 *                    the size of the green curve, *the green curve,
 *                    the size of the blue curve, *the blue curve},
 *                    needs to be free:d. `NULL` on error.
 */
uint16_t* blueshift_randr_read(int use_crtc);

/**
 * Apply stage of colour curve control
 * 
 * @param   use_crtc  The CRTC to use, -1 for all
 * @param   r_curve   The red colour curve
 * @param   g_curve   The green colour curve
 * @param   b_curve   The blue colour curve
 * @return            Zero on success
 */
int blueshift_randr_apply(int use_crtc, uint16_t* r_curve, uint16_t* g_curve, uint16_t* b_curve);

/**
 * Resource freeing stage of colour curve control
 */
void blueshift_randr_close(void);



#endif

