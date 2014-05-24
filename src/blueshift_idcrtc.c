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
#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <inttypes.h>
#include <alloca.h>

#include <xcb/xcb.h>
#include <xcb/randr.h>



/**
 * The major version of RANDR the program expects
 */
#define RANDR_VERSION_MAJOR  1

/**
 * The minor version of RANDR the program expects
 */
#define RANDR_VERSION_MINOR  3



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
 #pragma GCC diagnostic push
 #pragma GCC diagnostic ignored "-Wstack-protector"
int main(int argc, char** argv)
{
 #pragma GCC diagnostic pop
  char* display = NULL;
  xcb_randr_query_version_cookie_t version_cookie;
  xcb_randr_query_version_reply_t* randr_version;
  xcb_screen_iterator_t iter;
  int screen_count;
  int screen_i;
  int i;
  
  
  /* Get X connection */
  
  /* This acquires a connection to the
     X display indicated by the DISPLAY
     environ variable, or as indicated 
     by the first command line argument
     if existent. */
  if (argc > 1)
    display = *(argv + 1);
  connection = xcb_connect(display, NULL);
  
  
  /* Check RandR protocol version */
  
  /* Check that the version of RandR is supported. */
  version_cookie = xcb_randr_query_version(connection, RANDR_VERSION_MAJOR, RANDR_VERSION_MINOR);
  randr_version = xcb_randr_query_version_reply(connection, version_cookie, &error);
  
  if (error || (randr_version == NULL))
    {
      /* If not possible, print an error message and
         close the connection to the display. */
      fprintf(stderr, "RandR version query returned %i\n", error ? error->error_code : -1);
      xcb_disconnect(connection);
      return 1;
    }
  
  if (randr_version->major_version != RANDR_VERSION_MAJOR || randr_version->minor_version < RANDR_VERSION_MINOR)
    {
      /* If the version did not match, print a warning, */
      fprintf(stderr, "Unsupported RandR version, got %u.%u, expected %u.%u\n",
	      randr_version->major_version, randr_version->minor_version,
	      RANDR_VERSION_MAJOR, RANDR_VERSION_MINOR);
      /* free the version information resources, */
      free(randr_version);
      /* and close the connection to the display. */
      xcb_disconnect(connection);
      return 1;
    }
  
  /* Free the version information resources. */
  free(randr_version);
  
  
  /* Get screen information */
  
  /* Acquire a list of all screens in the display, */
  iter = xcb_setup_roots_iterator(xcb_get_setup(connection));
  /* count the list. */
  screen_count = iter.rem;
  
  /* Print the number available screens. */
  printf("Screen count: %i\n", screen_count);
  for (screen_i = 0; screen_i < screen_count; screen_i++)
    {
      /* For each screen */
      xcb_screen_t* screen = iter.data;
      xcb_randr_get_screen_resources_current_cookie_t res_cookie;
      xcb_randr_get_screen_resources_current_reply_t* res_reply;
      xcb_randr_output_t* outputs;
      xcb_randr_crtc_t* crtcs;
      int output_i;
      
      /* We have acquired the screen, go to next in preperation for next iteration. */
      xcb_screen_next(&iter);
      
      /* Print the screen index. */
      printf("Screen: %i\n", screen_i);
      
      /* Acquire information about the screen. */
      res_cookie = xcb_randr_get_screen_resources_current(connection, screen->root);
      res_reply = xcb_randr_get_screen_resources_current_reply(connection, res_cookie, &error);
      
      if (error)
	{
	  /* On error print an error message and close the connection to the display. */
	  fprintf(stderr, "RandR screen resource query returned %i\n", error->error_code);
	  xcb_disconnect(connection);
	  return 1;
	}
      
      /* Print the CRTC count, */
      printf("  CRTC count: %i\n", res_reply->num_crtcs);
      /* and the output count. */
      printf("  Output count: %i\n", res_reply->num_outputs);
      /* There are as many outputs as there are
         connectors, that is, the number of
	 monitors that you could potentially
         plugg into the graphics cards that
         are associated with the screen, even
         if that many are not supported. But
         there are only as many CRTC:s as
         there are monitors actually plugged
         in and supported. */
      
      
      /* Get output information */
      
      /* Extract output list. */
      outputs = xcb_randr_get_screen_resources_current_outputs(res_reply);
      /* Extract CRTC list. */
      crtcs = xcb_randr_get_screen_resources_current_crtcs(res_reply);
      /* For each output */
      for (output_i = 0; output_i < res_reply->num_outputs; output_i++)
        {
	  xcb_randr_get_output_info_cookie_t out_cookie;
	  xcb_randr_get_output_info_reply_t* out_reply;
	  uint8_t* name;
	  int name_len;
	  
	  /* Acquire information about the output. */
	  out_cookie = xcb_randr_get_output_info(connection, outputs[output_i], res_reply->config_timestamp);
	  out_reply = xcb_randr_get_output_info_reply(connection, out_cookie, &error);
	  
	  if (error)
	    {
	      /* On error print an error message, release the screen resources,
		 and close the connection to the display. */
	      fprintf(stderr, "RandR output query returned %i\n", error->error_code);
	      free(res_reply);
	      xcb_disconnect(connection);
	      return 1;
	    }
	  
	  /* Print the index, in the scope of the screen, of the output. */
	  printf("  Output: %i\n", output_i);
	  
	  /* We use indention not for computer-readability, but
	     exclusively for human-readability, especially for
	     debugging. */
	  
	  /* Extract the output name from the data structure that holds it. */
	  name = xcb_randr_get_output_info_name(out_reply);
	  /* As well as the length of the name; it is not NUL-termianted. */
	  name_len = out_reply->name_len;
	  
	  /* Print the output name, we specified length, so that
	     printf does not attempt to read outside the name,
	     as it is not NUL-terminated. */
	  printf("    Name: %.*s\n", name_len, name);
	  
	  /* Check connection status */
	  switch (out_reply->connection)
	    {
	    case XCB_RANDR_CONNECTION_CONNECTED:
	      /* If connectioned, do stuff! */
	      {
		xcb_randr_list_output_properties_cookie_t prop_cookie;
		xcb_randr_list_output_properties_reply_t* prop_reply;
		xcb_atom_t* atoms;
		xcb_atom_t* atoms_end;
		int crtc_i;
		
		/* Print that the connector is used. */
		printf("    Connection: connected\n");
		/* And print what dimensions RandR thinks the monitor has,
		   physically in millimeters, however common that it is
		   extremely wrong as it does not read it from the extended
		   display identication data, but tries to calculate it. */
		printf("    Size: %i %i\n", out_reply->mm_width, out_reply->mm_height);
		
		/* Iterate over all CRTC:s, */
		for (crtc_i = 0; crtc_i < res_reply->num_crtcs; crtc_i++)
		  /* and look for a CRTC with the same ID, */
		  if (crtcs[crtc_i] == out_reply->crtc)
		    {
		      /* and print that CRTC:s index. */
		      printf("    CRTC: %i\n", crtc_i);
		      break;
		    }
		
		/* Acquire a list of all properties of the output. */
		prop_cookie = xcb_randr_list_output_properties(connection, outputs[output_i]);
		prop_reply = xcb_randr_list_output_properties_reply(connection, prop_cookie, &error);
		
		if (error)
		  {
		    /* On error print an error message, */
		    fprintf(stderr, "RandR output property query returned %i\n", error->error_code);
		    /* and free that output and screen information resources, */
		    free(out_reply);
		    free(res_reply);
		    /* and then close the connection to the display. */
		    xcb_disconnect(connection);
		    return 1;
		  }
		
		
		/* Get output atoms */
		
		/* Extract the properties form the data structure that holds them, */
		atoms = xcb_randr_list_output_properties_atoms(prop_reply);
		/* and get the last one so that we can iterate over them nicely. */
		atoms_end = atoms + xcb_randr_list_output_properties_atoms_length(prop_reply);
		
		/* For each property */
		for (; atoms != atoms_end; atoms++)
		  {
		    xcb_get_atom_name_cookie_t atom_name_cookie;
		    xcb_get_atom_name_reply_t* atom_name_reply;
		    char* atom_name;
		    char* atom_name_;
		    int atom_name_len;
		    
		    /* Acquire the atom name. */
		    atom_name_cookie = xcb_get_atom_name(connection, *atoms);
		    atom_name_reply = xcb_get_atom_name_reply(connection, atom_name_cookie, &error);
		    
		    if (error)
		      {
			/* On error print an error message, */
			fprintf(stderr, "RandR atom name query returned %i\n", error->error_code);
			/* and release the property list, */
			free(prop_reply);
			/* the output information resources */
			free(out_reply);
			/* and the screen information resources. */
			free(res_reply);
			/* And then close the connection to the display. */
			xcb_disconnect(connection);
			return 1;
		      }
		    
		    /* Extract the atom name from the data structure that holds it. */
		    atom_name_ = xcb_get_atom_name_name(atom_name_reply);
		    /* As well as the length of the name; it is not NUL-termianted.*/
		    atom_name_len = xcb_get_atom_name_name_length(atom_name_reply);
		    
		    /* NUL-terminate the atom name. */
		    atom_name = alloca(((size_t)atom_name_len + 1U) * sizeof(char));
		    memcpy(atom_name, atom_name_, (size_t)atom_name_len * sizeof(char));
		    *(atom_name + atom_name_len) = 0;
		    /* (It is allocated on the stack, so it should not be free:d.) */
		    
		    
		    /* Get output identifier */
		    
		    /* Look for the the property named EDID. */
		    if (!strcmp(atom_name, "EDID"))
		      {
			xcb_randr_get_output_property_cookie_t atom_cookie;
			xcb_randr_get_output_property_reply_t* atom_reply;
			int length;
			unsigned char* atom_data_;
			char* atom_data;
			
			/* Acquire the property's value, we know that it is either 128 or 256 byte long. */
			atom_cookie = xcb_randr_get_output_property(connection, outputs[output_i], *atoms,
								    XCB_GET_PROPERTY_TYPE_ANY, 0, 256, 0, 0);
			
			atom_reply = xcb_randr_get_output_property_reply(connection, atom_cookie, &error);
			
			/* (*) EDID version 1.0 through 1.4 define it as 128 bytes long,
			       but version 2.0 define it as 256 bytes long. However,
			       version 2.0 is rare(?) and has been deprecated and replaced
			       by version 1.3 (I guess that is with a new version epoch,
			       but I do not know.) */ 
			
			if (error)
			  {
			    /* On error print an error message, */
			    fprintf(stderr, "RandR atom data query returned %i\n", error->error_code);
			    /* and release the property name, */
			    free(atom_name_reply);
			    /* release the property list, */
			    free(prop_reply);
			    /* the output information resources */
			    free(out_reply);
			    /* and the screen information resources. */
			    free(res_reply);
			    /* And then close the connection to the display. */
			    xcb_disconnect(connection);
			    return 1;
			  }
			
			/* Extract the property's value, */
			atom_data_ = xcb_randr_get_output_property_data(atom_reply);
			/* and its actual length. */
			length = xcb_randr_get_output_property_data_length(atom_reply);
			
			/* Convert to hexadecimal representation. */
			atom_data = alloca((2U * (size_t)length + 1U) * sizeof(char));
			for (i = 0; i < length; i++)
			  {
			    *(atom_data + i * 2 + 0) = "0123456789abcdef"[(*(atom_data_ + i) >> 4) & 15];
			    *(atom_data + i * 2 + 1) = "0123456789abcdef"[(*(atom_data_ + i) >> 0) & 15];
			  }
			/* NUL-terminate. */
			*(atom_data + 2 * length) = 0;
			
			/* Print the property's name and values. */
			printf("    %s: %s\n", atom_name, atom_data);
			
			/* Free the proprty value. */
			free(atom_reply);
		      }
		    
		    /* Free the name of the atom. */
		    free(atom_name_reply);
		  }
		
		/* Free the list of properties. */
		free(prop_reply);
	      }
	      break;
	      
	    case XCB_RANDR_CONNECTION_DISCONNECTED:
	      /* If disconnected, print that and continue to next output. */
	      printf("    Connection: disconnected\n");
	      break;
	      
	    case XCB_RANDR_CONNECTION_UNKNOWN:
	    default:
	      /* If the connection status is unkown, print that and continue to next output. */
	      printf("    Connection: unknown\n");
	      break;
	    }
	  
	  /* Free the output information resources. */
	  free(out_reply);
	}
      
      /* Free the screen information resources. */
      free(res_reply);
    }
  
  
  /* Free resources **/
  
  /* Close the connection to the display.*/
  xcb_disconnect(connection);
  return 0;
}

