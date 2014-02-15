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

#include <xcb/xcb.h>
#include <xcb/randr.h>



/**
 * The major version of RANDR the program expects
 */
#define RANDR_VERSION_MAJOR  1U

/**
 * The minor version of RANDR the program expects
 */
#define RANDR_VERSION_MINOR  3U



/**
 * Data structure for CRTC caches
 */
typedef struct blueshift_randr_crtc
{
  /**
   * Size of colour curves on the X-axis
   */
  unsigned int curve_size;
  
  /**
   * CRT controller
   */
  xcb_randr_crtc_t* crtc;
  
} blueshift_randr_crtc_t;



/**
 * Connection to the X server
 */
static xcb_connection_t* connection;

/**
 * Used to store errors in
 */
static xcb_generic_error_t* error;

/**
 * Screen resources
 */
static xcb_randr_get_screen_resources_current_reply_t* res_reply;

/**
 * The first CRTC
 */
static blueshift_randr_crtc_t* crtcs;

/**
 * The CRTC after the last CRTC
 */
static blueshift_randr_crtc_t* crtcs_end;

/**
 * The red colour curve
 */
static uint16_t* r_curve;

/**
 * The green colour curve
 */
static uint16_t* g_curve;

/**
 * The blue colour curve
 */
static uint16_t* b_curve;



/**
 * Start stage of colour curve control
 * 
 * @param   use_screen  The screen to use
 * @return              Zero on success
 */
int blueshift_randr_open(int use_screen)
{
  blueshift_randr_crtc_t* crtcs_;
  
  xcb_randr_query_version_cookie_t version_cookie;
  xcb_randr_query_version_reply_t* randr_version;
  const xcb_setup_t* setup;
  xcb_screen_iterator_t iter;
  xcb_screen_t* screen;
  xcb_randr_get_screen_resources_current_cookie_t res_cookie;
  unsigned int crtc_count;
  xcb_randr_get_crtc_gamma_size_cookie_t gamma_size_cookie;
  xcb_randr_get_crtc_gamma_size_reply_t* gamma_size_reply;
  xcb_randr_get_crtc_gamma_cookie_t gamma_get_cookie;
  xcb_randr_get_crtc_gamma_reply_t* gamma_get_reply;
  
  
  
  /* Get X connection */
  
  connection = xcb_connect(NULL, &use_screen);
  
  
  /* Check RANDR protocol version */
  
  version_cookie = xcb_randr_query_version(connection, RANDR_VERSION_MAJOR, RANDR_VERSION_MINOR);
  randr_version = xcb_randr_query_version_reply(connection, version_cookie, &error);
  
  if (error || (randr_version == NULL))
    {
      fprintf(stderr, "RANDR version query returned %i", error ? error->error_code : -1);
      xcb_disconnect(connection);
      return 1;
    }
  
  if (randr_version->major_version != RANDR_VERSION_MAJOR || randr_version->minor_version < RANDR_VERSION_MINOR)
    {
      fprintf(stderr, "Unsupported RANDR version, got %u.%u, expected %u.%u\n",
	      randr_version->major_version, randr_version->minor_version,
	      RANDR_VERSION_MAJOR, RANDR_VERSION_MINOR);
      free(randr_version);
      xcb_disconnect(connection);
      return 1;
    }
  
  free(randr_version);
  
  
  /* Get X resources */
  
  setup = xcb_get_setup(connection);
  iter = xcb_setup_roots_iterator(setup);
  screen = iter.data;
  
  res_cookie = xcb_randr_get_screen_resources_current(connection, screen->root);
  res_reply = xcb_randr_get_screen_resources_current_reply(connection, res_cookie, &error);
  
  if (error)
    {
      fprintf(stderr, "RANDR screen resource query returned %i\n", error->error_code);
      xcb_disconnect(connection);
      return 1;
    }
  
  
  /* Get CRTC:s */
  
  crtc_count = res_reply->num_crtcs;
  crtcs = malloc(crtc_count * sizeof(blueshift_randr_crtc_t));
  crtcs->crtc = xcb_randr_get_screen_resources_current_crtcs(res_reply);
  crtcs_end = crtcs + crtc_count;
  
  
  /* Prepare CRTC:s */
  
  for (crtcs_ = crtcs; crtcs_ != crtcs_end; crtcs_++)
    {
      /* Set CRTC */
      
      if (crtcs_ != crtcs)
	crtcs_->crtc = (crtcs_ - 1)->crtc + 1;
      
      
      /* Get curve X-axis size */
      
      gamma_size_cookie = xcb_randr_get_crtc_gamma_size(connection, *(crtcs_->crtc));
      gamma_size_reply = xcb_randr_get_crtc_gamma_size_reply(connection, gamma_size_cookie, &error);
      
      if (error)
	{
	  fprintf(stderr, "RANDR CRTC gamma size query returned %i\n", error->error_code);
	  xcb_disconnect(connection);
	  return 1;
	}
      
      crtcs_->curve_size = gamma_size_reply->size;
      free(gamma_size_reply);
      
      
      /* Acquire curve control */
      
      gamma_get_cookie = xcb_randr_get_crtc_gamma(connection, *(crtcs_->crtc));
      gamma_get_reply = xcb_randr_get_crtc_gamma_reply(connection, gamma_get_cookie, &error);
      
      if (error)
	{
	  fprintf(stderr, "RANDR CRTC gamma query returned %i\n", error->error_code);
	  xcb_disconnect(connection);
	  return 1;
	}
      
      free(gamma_get_reply);
    }
  
  
  /* Allocate curves */
  
  r_curve = malloc(3 * 256 * sizeof(uint16_t));
  g_curve = r_curve + 256;
  b_curve = g_curve + 256;
  
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
int blueshift_randr_apply(uint64_t use_crtcs, uint16_t* r_curve, uint16_t* g_curve, uint16_t* b_curve)
{
  blueshift_randr_crtc_t* crtcs_ = crtcs;
  
  xcb_void_cookie_t gamma_set_cookie;
  
  
  /* Use CRTC:s */
  
  while (crtcs_ != crtcs_end)
    {
      /* Check whether we should use the CRTC */

      if ((use_crtcs & 1) == 0)
	goto next_crtc;
      
      
      /* Apply curves */
      
      gamma_set_cookie = xcb_randr_set_crtc_gamma_checked(connection, *(crtcs_->crtc), crtcs_->curve_size,
							  r_curve, g_curve, b_curve);
      error = xcb_request_check(connection, gamma_set_cookie);
      
      if (error)
	{
	  fprintf(stderr, "RANDR CRTC control returned %i\n", error->error_code);
	  return 1;
	}
      
      
      /* Next CRTC */
      
    next_crtc:
      crtcs_++;
      use_crtcs >>= 1;
    }
  
  return 0;
}


/**
 * Resource freeing stage of colour curve control
 */
void blueshift_randr_close(void)
{
  /* Free remaining resources */
  
  free(r_curve);
  free(crtcs);
  free(res_reply);
  xcb_disconnect(connection);
}



int main(int argc, char** argv)
{
  long i;
  
  (void) argc;
  (void) argv;
  
  if (blueshift_randr_open(0))
    return 1;
  
  for (i = 0; i < 256; i++)
    r_curve[i] = g_curve[i] = b_curve[i] = (int)((float)i / 255.f * (float)((1 << 16) - 1) + 0.f);
  
  i = blueshift_randr_apply(~0, r_curve, g_curve, b_curve);
  blueshift_randr_close();
  return i;
}

