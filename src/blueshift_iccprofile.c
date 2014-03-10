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
 * GNU Affero General Public License for more details.
 * 
 * You should have received a copy of the GNU General Public License
 * along with this program.  If not, see <http://www.gnu.org/licenses/>.
 */
#define _GNU_SOURCE /* for strcasestr */
#include <stdlib.h>
#include <stdio.h>
#include <alloca.h>
#include <string.h>

#include <xcb/xcb.h>



/**
 * Connection to the X server
 */
static xcb_connection_t* connection;

/**
 * Used to store errors in
 */
static xcb_generic_error_t* error;



/**
 * Main entry point of the program
 * 
 * @param   argc  Length of `argv`
 * @param   argv  Command line arguments
 * @return        Zero on success
 */
int main(int argc, char** argv)
{
  const xcb_setup_t* setup;
  xcb_screen_iterator_t iter;
  int screen_count;
  xcb_screen_t* screens;
  int screen_i;
  
  (void) argc;
  (void) argv;
  
  
  /* Get X connection */
  
  connection = xcb_connect(NULL, NULL);
  
  
  /* Get screen information */
  
  setup = xcb_get_setup(connection);
  iter = xcb_setup_roots_iterator(setup);
  screen_count = iter.rem;
  screens = iter.data;
  
  for (screen_i = 0; screen_i < screen_count; screen_i++)
    {
      xcb_screen_t* screen = screens + screen_i;
      xcb_list_properties_cookie_t list_cookie;
      xcb_list_properties_reply_t* list_reply;
      xcb_atom_t* atoms;
      xcb_atom_t* atoms_end;
      
      
      /* Get root window properties */
      
      list_cookie = xcb_list_properties(connection, screen->root);
      list_reply = xcb_list_properties_reply(connection, list_cookie, &error);
      
      if (error)
	{
	  fprintf(stderr, "Screen root window property list query returned %i\n", error->error_code);
	  xcb_disconnect(connection);
	  return 1;
	}
      
      atoms = xcb_list_properties_atoms(list_reply);
      atoms_end = atoms + xcb_list_properties_atoms_length(list_reply);
      
      for (; atoms != atoms_end; atoms++)
	{
	  xcb_get_atom_name_cookie_t name_cookie;
	  xcb_get_atom_name_reply_t* name_reply;
	  char* name;
	  char* name_;
	  int len;
	  xcb_get_property_cookie_t prop_cookie;
	  xcb_get_property_reply_t* prop_reply;
	  int monitor;
	  
	  
	  /* Get root window property name */
	  
	  name_cookie = xcb_get_atom_name(connection, *atoms);
	  name_reply = xcb_get_atom_name_reply(connection, name_cookie, &error);
	  
	  if (error)
	    {
	      fprintf(stderr, "Screen root window property name query returned %i\n", error->error_code);
	      free(list_reply);
	      xcb_disconnect(connection);
	      return 1;
	    }
	  
	  name_ = xcb_get_atom_name_name(name_reply);
	  len = xcb_get_atom_name_name_length(name_reply);
	  
	  name = alloca((len + 1) * sizeof(char));
	  memcpy(name, name_, len * sizeof(char));
	  *(name + len) = 0;
	  free(name_reply);
	  
	  
	  /* Check property name pattern */
	  
	  if (!strcmp(name, "_icc_profile"))
	    monitor = 0;
	  else if (strcasestr(name, "_icc_profile_") == name)
	    {
	      name += strlen("_icc_profile_");
	      monitor = 0;
	      if (*name)
		continue;
	      while (*name)
		{
		  char c = *name;
		  if (('0' <= c) && (c <= '9'))
		    monitor = monitor * 10 - (c & 15);
		  else
		    goto monitor_bad;
		}
	      monitor = -monitor;
	      goto monitor_ok;
	      
	    monitor_bad:
	      continue;
	    }
	  else
	    continue;
	  
	  
	  /* Get root window property value */
	  
	monitor_ok:
	  prop_cookie = xcb_get_property(connection, 0, screen->root, *atoms, XCB_GET_PROPERTY_TYPE_ANY, 0, 0);
	  prop_reply = xcb_get_property_reply(connection, prop_cookie, &error);
	  
	  if (error)
	    {
	      fprintf(stderr, "Screen root window property value query returned %i\n", error->error_code);
	      free(prop_reply);
	      free(list_reply);
	      xcb_disconnect(connection);
	      return 1;
	    }
	  
	  len = prop_reply->bytes_after;
	  free(prop_reply);
	  
	  prop_cookie = xcb_get_property(connection, 0, screen->root, *atoms, XCB_GET_PROPERTY_TYPE_ANY, 0, len);
	  prop_reply = xcb_get_property_reply(connection, prop_cookie, &error);
	  
	  if (error)
	    {
	      fprintf(stderr, "Screen root window property value query returned %i\n", error->error_code);
	      free(prop_reply);
	      free(list_reply);
	      xcb_disconnect(connection);
	      return 1;
	    }
	  
	  {
	    char* value = alloca((2 * len + 1) * sizeof(char));
	    char* value_ = xcb_get_property_value(prop_reply);
	    int i;
	    
	    for (i = 0; i < len; i++)
	      {
		*(value + i * 2 + 0) = "0123456789abcdef"[(*(value_ + i) >> 4) & 15];
		*(value + i * 2 + 1) = "0123456789abcdef"[(*(value_ + i) >> 0) & 15];
	      }
	    *(value + 2 * len) = 0;
	    
	    printf("%i: %i: %s\n", screen_i, monitor, value);
	  }
	  
	  free(prop_reply);
	}
      
      free(list_reply);
    }
  
  fflush(stdout);
  
  /* Free resources **/
  
  xcb_disconnect(connection);
  return 0;
}

