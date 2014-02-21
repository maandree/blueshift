/**
 * Copyright © 2014  Mattias Andrée (maandree@member.fsf.org)
 * 
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Affero General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 * 
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU Affero General Public License for more details.
 * 
 * You should have received a copy of the GNU Affero General Public License
 * along with this program.  If not, see <http://www.gnu.org/licenses/>.
 */
#include <stdlib.h>
#include <stdio.h>
#include <inttypes.h>

#include <X11/Xlib.h>
#include <X11/extensions/xf86vmode.h>



/**
 * The X server display
 */
static Display* display;

/**
 * The X screen
 */
static int screen;

/**
 * Size of colour curves on the X-axis
 */
static int curve_size;



/**
 * Start stage of colour curve control
 * 
 * @param   use_screen  The screen to use
 * @return              Zero on success
 */
int blueshift_vidmode_open(int use_screen)
{
  int _major, _minor;
  uint16_t* r_gamma;
  uint16_t* g_gamma;
  uint16_t* b_gamma;
  
  
  /* Get X display */
  
  if ((display = XOpenDisplay(NULL)) == NULL)
    {
      fprintf(stderr, "Cannot open X display\n");
      return 1;
    }
  
  
  /* Check for VidMode extension */
  
  if (XF86VidModeQueryVersion(display, &_major, &_minor) == 0)
    {
      fprintf(stderr, "VidMode version query failed\n");
      XCloseDisplay(display);
      return 1;
    }
  
  
  /* Get curve X-axis size */
  
  screen = use_screen;
  if (XF86VidModeGetGammaRampSize(display, screen, &curve_size) == 0)
    {
      fprintf(stderr, "VidMode gamma size query failed\n");
      XCloseDisplay(display);
      return 1;
    }
  
  if (curve_size < 1)
    {
      fprintf(stderr, "VidMode gamma size query failed\n");
      XCloseDisplay(display);
      return 1;
    }
  
  
  /* Acquire curve control */
  
  r_gamma = malloc(3 * curve_size * sizeof(uint16_t));
  if (r_gamma == NULL)
    {
      fprintf(stderr, "Out of memory\n");
      return 1;
    }
  g_gamma = r_gamma + curve_size;
  b_gamma = g_gamma + curve_size;
  if (XF86VidModeGetGammaRamp(display, screen, curve_size, r_gamma, g_gamma, b_gamma) == 0)
    {
      fprintf(stderr, "VidMode gamma query failed\n");
      free(r_gamma);
      XCloseDisplay(display);
      return 1;
    }
  free(r_gamma);
  
  return 0;
}


/**
 * Apply stage of colour curve control
 * 
 * @param   use_crtcs  Mask of CRTC:s to use
 * @param   r_curve    The red colour curve
 * @param   g_curve    The green colour curve
 * @param   b_curve    The blue colour curve
 * @return             Zero on success
 */
int blueshift_vidmode_apply(uint64_t use_crtcs, uint16_t* r_curve, uint16_t* g_curve, uint16_t* b_curve)
{
  (void) use_crtcs;
  
  /* Apply curves */
  
  if (XF86VidModeSetGammaRamp(display, screen, curve_size, r_curve, g_curve, b_curve) == 0)
    {
      fprintf(stderr, "VidMode gamma control failed\n");
      return 1;
    }
  
  return 0;
}


/**
 * Resource freeing stage of colour curve control
 */
void blueshift_vidmode_close(void)
{
  /* Free remaining resources */
  
  XCloseDisplay(display);
}

