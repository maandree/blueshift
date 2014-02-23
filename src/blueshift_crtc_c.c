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
 * Connection to the X server
 */
static xcb_connection_t* connection;

/**
 * Used to store errors in
 */
static xcb_generic_error_t* error;


int main(int argc __attribute__((unused)), char** argv __attribute__((unused)))
{
  xcb_randr_query_version_cookie_t version_cookie;
  xcb_randr_query_version_reply_t* randr_version;
  const xcb_setup_t* setup;
  xcb_screen_iterator_t iter;
  int screen_count;
  xcb_screen_t* screens;
  int screen_i;
  
  
  /* Get X connection */
  
  connection = xcb_connect(NULL, NULL);
  
  
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
  
  
  /* Get screen information */
  
  setup = xcb_get_setup(connection);
  iter = xcb_setup_roots_iterator(setup);
  screen_count = iter.rem;
  screens = iter.data;
  
  printf("Screen count: %i\n", screen_count);
  for (screen_i = 0; screen_i < screen_count; screen_i++)
    {
      xcb_screen_t* screen = screens + screen_i;
      xcb_randr_get_screen_resources_current_cookie_t res_cookie;
      xcb_randr_get_screen_resources_current_reply_t* res_reply;
      xcb_randr_output_t* outputs;
      xcb_randr_crtc_t* crtcs;
      int output_i;
      
      printf("Screen: %i\n", screen_i);
      
      res_cookie = xcb_randr_get_screen_resources_current(connection, screen->root);
      res_reply = xcb_randr_get_screen_resources_current_reply(connection, res_cookie, &error);
      
      if (error)
	{
	  fprintf(stderr, "RANDR screen resource query returned %i\n", error->error_code);
	  xcb_disconnect(connection);
	  return 1;
	}
      
      printf("  CRTC count: %i\n", res_reply->num_crtcs);
      printf("  Output count: %i\n", res_reply->num_outputs);
      
      outputs = xcb_randr_get_screen_resources_current_outputs(res_reply);
      crtcs = xcb_randr_get_screen_resources_current_crtcs(res_reply);
      for (output_i = 0; output_i < res_reply->num_outputs; output_i++)
        {
	  xcb_randr_get_output_info_cookie_t out_cookie;
	  xcb_randr_get_output_info_reply_t* out_reply;
	  
	  out_cookie = xcb_randr_get_output_info(connection, outputs[output_i], res_reply->config_timestamp);
	  out_reply = xcb_randr_get_output_info_reply(connection, out_cookie, &error);
	  
	  if (error)
	    {
	      fprintf(stderr, "RANDR output query returned %i\n", error->error_code);
	      xcb_disconnect(connection);
	      return 1;
	    }
	  
	  printf("  Output: %i\n", output_i);
	  switch (out_reply->connection)
	    {
	    case XCB_RANDR_CONNECTION_CONNECTED:
	      {
		int crtc_i;
		printf("    Connection: connected\n");
		printf("    Size: %i %i\n", out_reply->mm_width, out_reply->mm_height);
		for (crtc_i = 0; crtc_i < res_reply->num_crtcs; crtc_i++)
		  if (crtcs[crtc_i] == out_reply->crtc)
		    printf("    CRTC: %i\n", crtc_i);
	      }
	      break;
	    case XCB_RANDR_CONNECTION_DISCONNECTED:
	      printf("    Connection: disconnected\n");
	      break;
	    case XCB_RANDR_CONNECTION_UNKNOWN:
	    default:
	      printf("    Connection: unknown\n");
	      break;
	    }
	}
      
      free(res_reply);
    }
  
  
  /* Free resources **/
  
  xcb_disconnect(connection);
  return 0;
}

