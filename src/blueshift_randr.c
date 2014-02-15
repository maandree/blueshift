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



#define RANDR_VERSION_MAJOR  1U
#define RANDR_VERSION_MINOR  3U



int main(int argc __attribute__((unused)), char** argv __attribute__((unused)))
{
  xcb_connection_t* connection;
  xcb_generic_error_t* error;
  xcb_randr_query_version_cookie_t version_cookie;
  xcb_randr_query_version_reply_t* randr_version;
  const xcb_setup_t* setup;
  xcb_screen_iterator_t iter;
  xcb_screen_t* screen;
  xcb_randr_get_screen_resources_current_cookie_t res_cookie;
  xcb_randr_get_screen_resources_current_reply_t* res_reply;
  xcb_randr_crtc_t* crtcs;
  xcb_randr_get_crtc_gamma_size_cookie_t gamma_size_cookie;
  xcb_randr_get_crtc_gamma_size_reply_t* gamma_size_reply;
  unsigned int curve_size;
  xcb_randr_get_crtc_gamma_cookie_t gamma_get_cookie;
  xcb_randr_get_crtc_gamma_reply_t* gamma_get_reply;
  uint16_t* r_gamma;
  uint16_t* g_gamma;
  uint16_t* b_gamma;
  unsigned int i;
  xcb_void_cookie_t gamma_set_cookie;
  
  
  connection = xcb_connect(NULL, NULL /* preferred screen */);
  
  
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
  
  
  crtcs = xcb_randr_get_screen_resources_current_crtcs(res_reply);
  
  
  gamma_size_cookie = xcb_randr_get_crtc_gamma_size(connection, *crtcs);
  gamma_size_reply = xcb_randr_get_crtc_gamma_size_reply(connection, gamma_size_cookie, &error);
  
  if (error)
    {
      fprintf(stderr, "RANDR CRTC gamma size query returned %i\n", error->error_code);
      xcb_disconnect(connection);
      return 1;
    }
  
  curve_size = gamma_size_reply->size;
  free(gamma_size_reply);
  
  
  gamma_get_cookie = xcb_randr_get_crtc_gamma(connection, *crtcs);
  gamma_get_reply = xcb_randr_get_crtc_gamma_reply(connection, gamma_get_cookie, &error);
  
  free(res_reply);
  
  if (error)
    {
      fprintf(stderr, "RANDR CRTC gamma query returned %i\n", error->error_code);
      xcb_disconnect(connection);
      return 1;
    }
  
  r_gamma = xcb_randr_get_crtc_gamma_red(gamma_get_reply);
  g_gamma = xcb_randr_get_crtc_gamma_green(gamma_get_reply);
  b_gamma = xcb_randr_get_crtc_gamma_blue(gamma_get_reply);
  
  
  for (i = 0; i < curve_size; i++)
    {
      *(r_gamma + i) = (1 << 16) - 1 - *(r_gamma + i);
      *(g_gamma + i) = (1 << 16) - 1 - *(g_gamma + i);
      *(b_gamma + i) = (1 << 16) - 1 - *(b_gamma + i);
    }
  
  
  gamma_set_cookie = xcb_randr_set_crtc_gamma_checked(connection, *crtcs, curve_size, r_gamma, g_gamma, b_gamma);
  error = xcb_request_check(connection, gamma_set_cookie);
  
  if (error)
    {
      fprintf(stderr, "RANDR CRTC control returned %i\n", error->error_code);
      return 1;
    }
  
  
  free(gamma_get_reply);
  xcb_disconnect(connection);
  return 0;
}

