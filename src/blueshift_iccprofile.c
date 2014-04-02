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
  xcb_screen_iterator_t iter;
  int screen_count;
  xcb_screen_t* screens;
  int screen_i;
  
  (void) argc;
  (void) argv;
  
  
  /* To get all ICC profiles, which are binary encoded, we have
     to connect to the display and for each screen look for
     properties maching the pattern "_ICC_PROFILE(|_[0-9]*)".
     But we should also do it without being case sensitive,
     because it is not well defined how the casing should be.
     The _ICC_PROFILE atom is the profile for the first CRTC
     (with the primary one being the first) within the screen.
     _ICC_PROFILE_0 is not a valid atom for a profile,
     _ICC_PROFILE_1 is for the secondard, and _ICC_PROFILE_2
     is for the tertiary, and so on.
   */
  
  
  /* Get X connection */
  
  /* This acquires a connection to the
     X display indicated by the DISPLAY
     environ variable. */
  connection = xcb_connect(NULL, NULL);
  
  
  /* Get screen information */
  
  /* Acquire a list of all screens in the display, */
  iter = xcb_setup_roots_iterator(xcb_get_setup(connection));
  /* count the list, */
  screen_count = iter.rem;
  /* and start at the first screen. */
  screens = iter.data;
  
  for (screen_i = 0; screen_i < screen_count; screen_i++)
    {
      /* For each screen */
      xcb_screen_t* screen = screens + screen_i;
      
      xcb_list_properties_cookie_t list_cookie;
      xcb_list_properties_reply_t* list_reply;
      xcb_atom_t* atoms;
      xcb_atom_t* atoms_end;
      
      
      /* Get root window properties */
      
      /* Acquire a list of all properties on the current screen's root window.
         global properties are set here, as well as monitor specific properties
         that are actual monitor properties. */
      list_cookie = xcb_list_properties(connection, screen->root);
      list_reply = xcb_list_properties_reply(connection, list_cookie, &error);
      
      if (error)
	{
	  /* If we were not successful lets print an error
	     message and close the connection to the display. */
	  fprintf(stderr, "Screen root window property list query returned %i\n", error->error_code);
	  xcb_disconnect(connection);
	  return 1;
	}
      
      /* Extract the properties for the data structure that holds them, */
      atoms = xcb_list_properties_atoms(list_reply);
      /* and get the last one so that we can iterate over them nicely. */
      atoms_end = atoms + xcb_list_properties_atoms_length(list_reply);
      
      /* For each property */
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
	  
	  /* Acquire the the atom name. */
	  name_cookie = xcb_get_atom_name(connection, *atoms);
	  name_reply = xcb_get_atom_name_reply(connection, name_cookie, &error);
	  
	  if (error)
	    {
	      /* If we were not successful lets print an error
		 message, free the property list and close the
		 connection to the display. */
	      fprintf(stderr, "Screen root window property name query returned %i\n", error->error_code);
	      free(list_reply);
	      xcb_disconnect(connection);
	      return 1;
	    }
	  
	  /* Extract the atom name from the data structure that holds it. */
	  name_ = xcb_get_atom_name_name(name_reply);
	  /* As well as the length of the name; it is not NUL-termianted.*/
	  len = xcb_get_atom_name_name_length(name_reply);
	  
	  /* NUL-terminate the atom name, */
	  name = alloca((len + 1) * sizeof(char)); /* It is allocated on the stack, so it should not be free:d */
	  memcpy(name, name_, len * sizeof(char));
	  *(name + len) = 0;
	  /* and free the version that is not NUL-terminated. */
	  free(name_reply);
	  
	  
	  /* Check property name pattern */
	  
	  /* Read the atom name */
	  if (!strcasecmp(name, "_icc_profile"))
	    /* _ICC_PROFILE is for monitor 0 */
	    monitor = 0;
	  else if (strcasestr(name, "_icc_profile_") == name)
	    {
	      /* Skip to the part that should be numerical */
	      name += strlen("_icc_profile_");
	      monitor = 0;
	      if (*name == '\0')
		/* Invalid: no index */
		continue;
	      /* Parse index */
	      while (*name)
		{
		  char c = *name++;
		  /* with strict format matching. */
		  if (('0' <= c) && (c <= '9'))
		    monitor = monitor * 10 - (c & 15);
		  else
		    /* Not numerical: did not match */
		    goto monitor_bad;
		}
	      /* Convert from negative to possitive. */
	      monitor = -monitor;
	      /* Check that it is not zero, zero is
	         not a valid index, it should just be
		 _ICC_PROFILE in such case. */
	      if (monitor > 0)
		goto monitor_ok;
	      
	    monitor_bad:
	      /* Atom name ultimately did not match the, pattern
		 ignore it, it may be for something else, but it
		 is propably just invalid. */
	      continue;
	    }
	  else
	    /* Atom name does not match the pattern,
	       ignore it, it is for something else. */
	    continue;
	  
	  
	  /* Get root window property value */
	  
	monitor_ok:
	  /* Acquire the property's value, partially. */
	  prop_cookie = xcb_get_property(connection, 0, screen->root, *atoms, XCB_GET_PROPERTY_TYPE_ANY, 0, 0);
	  prop_reply = xcb_get_property_reply(connection, prop_cookie, &error);
	  
	  if (error)
	    {
	      /* If we were not successful lets print an error
		 message, free the property and property list
		 and close the connection to the display. */
	      fprintf(stderr, "Screen root window property value query returned %i\n", error->error_code);
	      free(prop_reply);
	      free(list_reply);
	      xcb_disconnect(connection);
	      return 1;
	    }
	  
	  /* Get the length of the property's value */
	  len = prop_reply->bytes_after;
	  
	  /* Acquire the property's value, fully. */
	  prop_cookie = xcb_get_property(connection, 0, screen->root, *atoms, XCB_GET_PROPERTY_TYPE_ANY, 0, len);
	  prop_reply = xcb_get_property_reply(connection, prop_cookie, &error);
	  
	  if (error)
	    {
	      /* If we were not successful lets print an error
		 message, free the property and property list
		 and close the connection to the display. */
	      fprintf(stderr, "Screen root window property value query returned %i\n", error->error_code);
	      free(prop_reply);
	      free(list_reply);
	      xcb_disconnect(connection);
	      return 1;
	    }
	  
	  /* Encode the property's value hexadecimally */
	  {
	    /* Allocate memories on the stack to fill with property's
	       value in with hexadecimal encoding and NUL-termination. */
	    char* value = alloca((2 * len + 1) * sizeof(char));
	    /* Get the property's value. */
	    char* value_ = xcb_get_property_value(prop_reply);
	    int i;
	    
	    /* Recode */
	    for (i = 0; i < len; i++)
	      {
		*(value + i * 2 + 0) = "0123456789abcdef"[(*(value_ + i) >> 4) & 15];
		*(value + i * 2 + 1) = "0123456789abcdef"[(*(value_ + i) >> 0) & 15];
	      }
	    /* NUL-terminate */
	    *(value + 2 * len) = 0;
	    
	    /* Print screen, monitor and profile. */
	    printf("%i: %i: %s\n", screen_i, monitor, value);
	  }
	  
	  /* Free the property resources. */
	  free(prop_reply);
	}
      
      /* Free the list is properties. */
      free(list_reply);
    }
  
  /* Flush standard output to be sure that everything was printed,
     should not be necessary, but it is best to be on the safe side. */
  fflush(stdout);
  
  /* Free resources */
  
  /* Close connection to the display. */
  xcb_disconnect(connection);
  return 0;
}

