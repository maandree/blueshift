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
#include "blueshift_w32gdi_c.h"



/**
 * The number of CRTC:s on the system
 */
static int crtc_count;

/**
 * The device contexts for each CRTC
 */
static HDC* crtcs;



/**
 * Start stage of colour curve control
 * 
 * @return  Zero on success
 */
int blueshift_w32gdi_open(void)
{
  int c;
  HDC hDC;
  DISPLAY_DEVICE display;
  display.cb = sizeof(DISPLAY_DEVICE);
  
  crtc_count = 0;
  while (EnumDisplayDevices(NULL, crtc_count, &display, 0))
    crtc_count++;
  
  if (crtc_count == 0)
    {
      crtcs = NULL;
      return 0;
    }
  
  crtcs = malloc(crtc_count * sizeof(HDC));
  if (crtcs == NULL)
    {
      fprintf(stderr, "Out of memory\n");
      return 1;
    }
  
  for (c = 0; c < crtc_count; c++)
    {
      /* Open device context */
      if (EnumDisplayDevices(NULL, c, &display, 0) == FALSE)
	{
	  fprintf(stderr, "Cannot find display, are you unplugging stuff?\n");
	  crtc_count = c;
	  return 1;
	}
      if (!(display.StateFlags & DISPLAY_DEVICE_ACTIVE))
	{
	  fprintf(stderr, "Cannot to open device context, it is not active\n");
	  crtc_count = c;
	  return 1;
	}
      hDC = *(crtcs + c) = CreateDC(TEXT("DISPLAY"), display.DeviceName, NULL, NULL);
      if (hDC == NULL)
	{
	  fprintf(stderr, "Unable to open device context\n");
	  crtc_count = c;
	  return 1;
	}
      
      /* Check support for gamma ramps */
      if (GetDeviceCaps(hDC, COLORMGMTCAPS) != CM_GAMMA_RAMP)
	{
	  fprintf(stderr, "CRTC %i does not support gamma ramps\n", c);
	  ReleaseDC(NULL, hDC);
	  crtc_count = c;
	  return 1;
	}
    }
  
  return 0;
}


/**
 * Get the number of CRTC:s on the system
 * 
 * @return  The number of CRTC:s on the system
 */
int blueshift_w32gdi_crtc_count(void)
{
  return crtc_count;
}


/**
 * Gets the current colour curves
 * 
 * @param   use_crtc  The CRTC to use
 * @return            {the size of the each curve, *the red curve,
 *                    *the green curve, *the blue curve},
 *                    needs to be free:d. `NULL` on error.
 */
uint16_t* blueshift_w32gdi_read(int use_crtc)
{
  uint16_t* rc = NULL;
  if ((use_crtc < 0) || (use_crtc >= crtc_count))
    fprintf(stderr, "CRTC %i does not exist\n", use_crtc);
  else
    {
      rc = malloc((1 + 3 * GAMMA_RAMP_SIZE) * sizeof(uint16_t));
      if (rc == NULL)
	fprintf(stderr, "Out of memory\n");
      else
	{
	  *rc = GAMMA_RAMP_SIZE;
	  if (GetDeviceGammaRamp(*(crtcs + use_crtc), rc + 1) == FALSE)
	    {
	      fprintf(stderr, "Unable to read current gamma ramps from CRTC %i\n", use_crtc);
	      free(rc);
	      rc = NULL;
	    }
	}
    }
  return rc;
}


/**
 * Apply stage of colour curve control
 * 
 * @param   use_crtc   The CRTC to use, -1 for all
 * @param   rgb_curve  The concatenation of the red, the green and the blue colour curves
 * @return             Zero on success
 */
int blueshift_w32gdi_apply(int use_crtc, uint16_t* rgb_curves)
{
  int r = 1;
  if (use_crtc < crtc_count)
    {
      int c = use_crtc < 0 ? 0 : use_crtc;
      int n = use_crtc < 0 ? crtc_count : (use_crtc + 1);
      for (; c < n; c++)
	if (!(r = SetDeviceGammaRamp(*(crtcs + c), rgb_curves)))
	  {
	    fprintf(stderr, "Unable to set gamma ramps\n");
	    break;
	  }
    }
  else
    fprintf(stderr, "CRTC %i does not exist\n", use_crtc);
  return !r;
}


/**
 * Resource freeing stage of colour curve control
 */
void blueshift_w32gdi_close(void)
{
  int c;
  for (c = 0; c < crtc_count; c++)
    ReleaseDC(NULL, *(crtcs + c));
  if (crtcs != NULL)
    free(crtcs);
}

