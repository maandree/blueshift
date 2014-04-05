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
#include "blueshift_vidmode_c.h"


/**
 * The X server display
 */
static Display* connection;

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
 * @param   display     The display to use, `NULL` for the current one
 * @return              Zero on error, otherwise the size of colours curves
 */
int blueshift_vidmode_open(int use_screen, char* display)
{
  int _major, _minor;
  
  
  /* Get X display */
  
  if ((connection = XOpenDisplay(display)) == NULL)
    {
      fprintf(stderr, "Cannot open X display\n");
      return 0;
    }
  
  
  /* Check for VidMode extension */
  
  if (XF86VidModeQueryVersion(connection, &_major, &_minor) == 0)
    {
      fprintf(stderr, "VidMode version query failed\n");
      XCloseDisplay(connection);
      return 0;
    }
  
  
  /* Get curve's size on the encoding axis */
  
  screen = use_screen;
  if (XF86VidModeGetGammaRampSize(connection, screen, &curve_size) == 0)
    {
      fprintf(stderr, "VidMode gamma size query failed\n");
      XCloseDisplay(connection);
      return 0;
    }
  
  if (curve_size <= 1)
    {
      fprintf(stderr, "VidMode gamma size query failed, impossible dimension\n");
      XCloseDisplay(connection);
      return 0;
    }
  
  return curve_size;
}


/**
 * Gets the current colour curves
 * 
 * @param   r_gamma   Storage location for the red colour curve
 * @param   g_gamma   Storage location for the green colour curve
 * @param   b_gamma   Storage location for the blue colour curve
 * @return            Zero on success
 */
int blueshift_vidmode_read(uint16_t* r_gamma, uint16_t* g_gamma, uint16_t* b_gamma)
{
  /* Read curves */
  
  if (XF86VidModeGetGammaRamp(connection, screen, curve_size, r_gamma, g_gamma, b_gamma) == 0)
    {
      fprintf(stderr, "VidMode gamma query failed\n");
      XCloseDisplay(connection);
      return 1;
    }
  
  return 0;
}


/**
 * Apply stage of colour curve control
 * 
 * @param   r_curve  The red colour curve
 * @param   g_curve  The green colour curve
 * @param   b_curve  The blue colour curve
 * @return           Zero on success
 */
int blueshift_vidmode_apply(uint16_t* r_curve, uint16_t* g_curve, uint16_t* b_curve)
{
  /* Apply curves */
  
  if (XF86VidModeSetGammaRamp(connection, screen, curve_size, r_curve, g_curve, b_curve) == 0)
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
  
  XCloseDisplay(connection);
}

