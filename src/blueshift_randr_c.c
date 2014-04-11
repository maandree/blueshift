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
#include "blueshift_randr_c.h"


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
 * Start stage of colour curve control
 * 
 * @param   use_screen  The screen to use
 * @param   display     The display to use, `NULL` for the current one
 * @return              Zero on success
 */
int blueshift_randr_open(int use_screen, char* display)
{
  blueshift_randr_crtc_t* crtcs_;
  
  xcb_randr_query_version_cookie_t version_cookie;
  xcb_randr_query_version_reply_t* randr_version;
  xcb_screen_iterator_t iter;
  xcb_screen_t* screen;
  xcb_randr_get_screen_resources_current_cookie_t res_cookie;
  unsigned int crtc_count;
  xcb_randr_get_crtc_gamma_size_cookie_t gamma_size_cookie;
  xcb_randr_get_crtc_gamma_size_reply_t* gamma_size_reply;
  xcb_randr_get_crtc_gamma_cookie_t gamma_get_cookie;
  xcb_randr_get_crtc_gamma_reply_t* gamma_get_reply;
  int iter_i;
  
  
  /* Get X connection */
  
  connection = xcb_connect(display, NULL);
  
  
  /* Check RandR protocol version */
  
  version_cookie = xcb_randr_query_version(connection, RANDR_VERSION_MAJOR, RANDR_VERSION_MINOR);
  randr_version = xcb_randr_query_version_reply(connection, version_cookie, &error);
  
  if (error || (randr_version == NULL))
    {
      fprintf(stderr, "RandR version query returned %i\n", error ? error->error_code : -1);
      xcb_disconnect(connection);
      return 1;
    }
  
  if (randr_version->major_version != RANDR_VERSION_MAJOR || randr_version->minor_version < RANDR_VERSION_MINOR)
    {
      fprintf(stderr, "Unsupported RandR version, got %u.%u, expected %u.%u\n",
	      randr_version->major_version, randr_version->minor_version,
	      RANDR_VERSION_MAJOR, RANDR_VERSION_MINOR);
      free(randr_version);
      xcb_disconnect(connection);
      return 1;
    }
  
  free(randr_version);
  
  
  /* Get X resources */
  
  iter = xcb_setup_roots_iterator(xcb_get_setup(connection));
  for (iter_i = 0; iter_i < use_screen; iter_i++)
    xcb_screen_next(&iter);
  screen = iter.data;
  
  res_cookie = xcb_randr_get_screen_resources_current(connection, screen->root);
  res_reply = xcb_randr_get_screen_resources_current_reply(connection, res_cookie, &error);
  
  if (error)
    {
      fprintf(stderr, "RandR screen resource query returned %i\n", error->error_code);
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
	  fprintf(stderr, "RandR CRTC gamma size query returned %i\n", error->error_code);
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
	  fprintf(stderr, "RandR CRTC gamma query returned %i\n", error->error_code);
	  xcb_disconnect(connection);
	  return 1;
	}
      
      free(gamma_get_reply);
    }
  
  return 0;
}


/**
 * Gets the current colour curves
 * 
 * @param   use_crtc  The CRTC to use
 * @return            {the size of the red curve, *the red curve,
 *                    the size of the green curve, *the green curve,
 *                    the size of the blue curve, *the blue curve},
 *                    needs to be free:d. `NULL` on error.
 */
uint16_t* blueshift_randr_read(int use_crtc)
{
  xcb_randr_get_crtc_gamma_cookie_t gamma_get_cookie;
  xcb_randr_get_crtc_gamma_reply_t* gamma_get_reply;
  uint16_t* r_gamma, * R_gamma;
  uint16_t* g_gamma, * G_gamma;
  uint16_t* b_gamma, * B_gamma;
  int i, R_size, G_size, B_size;
  
  /* Read curves */
  
  gamma_get_cookie = xcb_randr_get_crtc_gamma(connection, *((crtcs + use_crtc)->crtc));
  gamma_get_reply = xcb_randr_get_crtc_gamma_reply(connection, gamma_get_cookie, &error);
  
  if (error)
    {
      fprintf(stderr, "RandR CRTC gamma query returned %i\n", error->error_code);
      xcb_disconnect(connection);
      return NULL;
    }
  
  R_size = xcb_randr_get_crtc_gamma_red_length(gamma_get_reply);
  G_size = xcb_randr_get_crtc_gamma_green_length(gamma_get_reply);
  B_size = xcb_randr_get_crtc_gamma_blue_length(gamma_get_reply);
  
  if ((R_size < 2) || (G_size < 2) || (B_size < 2))
    {
      fprintf(stderr, "RandR CRTC gamma query returned impossibly small ramps\n");
      xcb_disconnect(connection);
      return NULL;
    }
  
  if ((R_size | G_size | B_size) > UINT16_MAX)
    {
      fprintf(stderr, "RandR CRTC gamma query returned unexpectedly large ramps\n");
      xcb_disconnect(connection);
      return NULL;
    }
  
  R_gamma = xcb_randr_get_crtc_gamma_red(gamma_get_reply);
  G_gamma = xcb_randr_get_crtc_gamma_green(gamma_get_reply);
  B_gamma = xcb_randr_get_crtc_gamma_blue(gamma_get_reply);
  
  r_gamma = malloc((3 + (size_t)R_size + (size_t)G_size + (size_t)B_size) * sizeof(uint16_t));
  g_gamma = r_gamma + R_size + 1;
  b_gamma = g_gamma + G_size + 1;
  if (r_gamma == NULL)
    {
      fprintf(stderr, "Out of memory\n");
      free(gamma_get_reply);
      xcb_disconnect(connection);
      return NULL;
    }
  
  *r_gamma++ = (uint16_t)R_size;
  *g_gamma++ = (uint16_t)G_size;
  *b_gamma++ = (uint16_t)B_size;
  
  for (i = 0; i < R_size; i++)  *(r_gamma + i) = *(R_gamma + i);
  for (i = 0; i < G_size; i++)  *(g_gamma + i) = *(G_gamma + i);
  for (i = 0; i < B_size; i++)  *(b_gamma + i) = *(B_gamma + i);
  
  free(gamma_get_reply);
  return r_gamma - 1;
}


/**
 * Apply stage of colour curve control
 * 
 * @param   use_crtc  The CRTC to use, -1 of all
 * @param   r_curve   The red colour curve
 * @param   g_curve   The green colour curve
 * @param   b_curve   The blue colour curve
 * @return            Zero on success
 */
int blueshift_randr_apply(int use_crtc, uint16_t* r_curve, uint16_t* g_curve, uint16_t* b_curve)
{
  /* Select first CRTC */
  blueshift_randr_crtc_t* crtc_start = crtcs + (use_crtc < 0 ? 0 : use_crtc);
  
  /* Select exclusive last CRTC */
  blueshift_randr_crtc_t* crtc_end = use_crtc < 0 ? crtcs_end : (crtc_start + 1);
  
  blueshift_randr_crtc_t* crtc;
  xcb_void_cookie_t gamma_set_cookie;
  
  
  /* Apply for all selected CRTC:s */
  
  for (crtc = crtc_start; crtc != crtc_end; crtc++)
    {
      /* Apply curves */
      
      gamma_set_cookie = xcb_randr_set_crtc_gamma_checked(connection, *(crtc->crtc), crtc->curve_size,
							  r_curve, g_curve, b_curve);
      error = xcb_request_check(connection, gamma_set_cookie);
      
      if (error)
	{
	  fprintf(stderr, "RandR CRTC control returned %i\n", error->error_code);
	  return 1;
	}
    }
  
  return 0;
}


/**
 * Resource freeing stage of colour curve control
 */
void blueshift_randr_close(void)
{
  /* Free remaining resources */
  
  free(crtcs);
  free(res_reply);
  xcb_disconnect(connection);
}

