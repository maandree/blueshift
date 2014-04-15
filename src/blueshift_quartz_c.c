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
#include "blueshift_quartz_c.h"



/**
 * The number of CRTC:s on the system
 */
static uint32_t crtc_count = 0;

/**
 * The CRTC:s on the system
 */
static CGDirectDisplayID* crtcs = NULL;

/**
 */
static uint32_t* gamma_sizes = NULL;



/**
 * Start stage of colour curve control
 * 
 * @return  Zero on success
 */
int blueshift_quartz_open(void)
{
  uint32_t cap = 4;
  uint32_t i;
  CGError r;
  
  crtcs = malloc((size_t)cap * sizeof(CGDirectDisplayID));
  if (crtcs == NULL)
    {
      perror("malloc");
      return -1;
    }
  
  for (;;)
    {
      r = CGGetOnlineDisplayList(cap, crtcs, &crtc_count);
      if (r != kCGErrorSuccess)
	{
	  free(crtcs);
	  crtcs = NULL;
	  close_fake_quartz();
	}
      if (crtc_count == cap)
	{
	  cap <<= 1;
	  if (cap == 0) /* We could also test ~0, but it is still too many. */
	    {
	      fprintf(stderr, "A impossible number of CRTC:s are avaiable according to Quartz\n");
	      free(crtcs);
	      close_fake_quartz();
	      return -1;
	    }
	  crtcs = realloc(crtcs, (size_t)cap * sizeof(CGDirectDisplayID));
	  if (crtcs == NULL)
	    {
	      perror("realloc");
	      close_fake_quartz();
	      return -1;
	    }
	}
      else
	break;
    }
  
  if (crtc_count > 0)
    {
      gamma_sizes = malloc((size_t)crtc_count * sizeof(uint32_t));
      if (gamma_sizes == NULL)
	{
	  perror("malloc");
	  free(crtcs);
	  close_fake_quartz();
	  return -1;
	}
      for (i = 0; i < crtc_count; i++)
	{
	  gamma_sizes[i] = CGDisplayGammaTableCapacity(crtcs[i]);
	  if (gamma_sizes[i] < 2)
	    {
	      fprintf(stderr, "Quartz reported impossibly small gamma ramps.\n");
	      free(gamma_sizes);
	      free(crtcs);
	      close_fake_quartz();
	      return -1;
	    }
	}
    }
  
  return 0;
}


/**
 * Get the number of CRTC:s on the system
 * 
 * @return  The number of CRTC:s on the system
 */
int blueshift_quartz_crtc_count(void)
{
  return (int)crtc_count;
}


/**
 * Gets the current colour curves
 * 
 * @param   use_crtc  The CRTC to use
 * @return            {the size of the each curve, *the red curve,
 *                    *the green curve, *the blue curve},
 *                    needs to be free:d. `NULL` on error.
 */
uint16_t* blueshift_quartz_read(int use_crtc)
{
  if ((use_crtc < 0) || (use_crtc >= (int)crtc_count))
    {
      fprintf(stderr, "CRTC %i does not exist\n", use_crtc);
      return NULL;
    }
  else
    {
      uint32_t gamma_size = gamma_sizes[use_crtc];
      uint16_t* rc = malloc((1 + 3 * (size_t)(gamma_size)) * sizeof(uint16_t));
      uint32_t i;
      CGGammaValue* red;
      CGGammaValue* green;
      CGGammaValue* blue;
      CGError r;
      uint32_t _;
      
      if (rc == NULL)
	{
	  perror("malloc");
	  return NULL;
	}
      
      red = malloc((3 * (size_t)gamma_size) * sizeof(CGGammaValue));
      green = red + (size_t)gamma_size;
      blue = green + (size_t)gamma_size;
      
      if (red == NULL)
	{
	  perror("malloc");
	  free(rc);
	  return NULL;
	}
      
      r = CGGetDisplayTransferByTable(crtcs[use_crtc], gamma_size, red, green, blue, &_);
      if (r != kCGErrorSuccess)
	{
	  fprintf(stderr, "Failed to get gamma ramps for CRTC %i\n", use_crtc);
	  free(red);
	  free(rc);
	  return 0;
	}
      
      *rc++ = gamma_sizes[use_crtc];
      for (i = 0; i < gamma_size; i++)
	{
	  int32_t v = red[i] * UINT16_MAX;
	  rc[i] = (uint16_t)(v < 0 ? 0 : v > UINT16_MAX ? UINT16_MAX : v);
	}
      rc += gamma_size;
      for (i = 0; i < gamma_size; i++)
	{
	  int32_t v = blue[i] * UINT16_MAX;
	  rc[i] = (uint16_t)(v < 0 ? 0 : v > UINT16_MAX ? UINT16_MAX : v);
	}
      rc += gamma_size;
      for (i = 0; i < gamma_size; i++)
	{
	  int32_t v = blue[i] * UINT16_MAX;
	  rc[i] = (uint16_t)(v < 0 ? 0 : v > UINT16_MAX ? UINT16_MAX : v);
	}
      
      return rc - (1 + 2 * gamma_size);
    }
}


/**
 * Apply stage of colour curve control
 * 
 * @param   use_crtc  The CRTC to use, -1 for all
 * @param   r_curve   The red colour curve
 * @param   g_curve   The green colour curve
 * @param   b_curve   The blue colour curve
 * @return            Zero on success
 */
int blueshift_quartz_apply(int use_crtc, float* r_curves, float* g_curves, float* b_curves)
{
  if (use_crtc < (int)crtc_count)
    {
      int c = use_crtc < 0 ? 0 : use_crtc;
      int n = use_crtc < 0 ? (int)crtc_count : (use_crtc + 1);
      CGError r = kCGErrorSuccess;
      
      for (; c < n; c++)
	{
	  r = CGSetDisplayTransferByTable(crtcs[c], gamma_sizes[c], r_curves, g_curves, b_curves);
	  if (r != kCGErrorSuccess)
	    {
	      fprintf(stderr, "Failed to set gamma ramps for CRTC %i\n", c);
	      break;
	    }
	}
      return r != kCGErrorSuccess;
    }
  fprintf(stderr, "CRTC %i does not exist\n", use_crtc);
  return -1;
}


/**
 * Resource freeing stage of colour curve control
 */
void blueshift_quartz_close(void)
{
  if (crtcs != NULL)
    free(crtcs);
  if (gamma_sizes != NULL)
    free(gamma_sizes);
  close_fake_quartz();
}


/**
 * Restore all gamma curves (on each and every CRTC on the system)
 * to the settings on ColorSync
 */
void blueshift_quartz_restore(void)
{
  CGDisplayRestoreColorSyncSettings();
}

