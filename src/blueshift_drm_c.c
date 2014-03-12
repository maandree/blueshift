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
#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <unistd.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <fcntl.h>
#include <alloca.h>

#ifndef O_CLOEXEC
  #define O_CLOEXEC  02000000
#endif

/* Requires video group */
#include <xf86drm.h>
#include <xf86drmMode.h>



/**
 * File descriptor for the DRM connection
 */
static int drm_fd;

/**
 * DRM mode resources
 */
static drmModeRes* drm_res = NULL;

/**
 * Connector information
 */
static drmModeConnector* connector = NULL;



/**
 * Get the number of cards present on the system
 * 
 * @return  The number of cards present on the system
 */
int blueshift_drm_card_count()
{
  long maxlen = strlen(DRM_DIR_NAME) + strlen(DRM_DEV_NAME) + 10;
  char* pathname = alloca(maxlen * sizeof(char));
  int count = 0;
  struct stat attr;
  
  for (;;)
    {
      sprintf(pathname, DRM_DEV_NAME, DRM_DIR_NAME, count);
      if (stat(pathname, &attr))
	break;
      count++;
    }
  
  return count;
}


/**
 * Open connection to a graphics card
 * 
 * @param   card  The index of the graphics card
 * @return        Zero on success
 */
int blueshift_drm_open(int card)
{
  long maxlen = strlen(DRM_DIR_NAME) + strlen(DRM_DEV_NAME) + 10;
  char* pathname = alloca(maxlen * sizeof(char));
  
  sprintf(pathname, DRM_DEV_NAME, DRM_DIR_NAME, card);
  
  drm_fd = open(pathname, O_RDWR | O_CLOEXEC);
  if (drm_fd < 0)
    {
      perror("open");
      return 1;
    }
  
  return 0;
}


/**
 * Close connection to the graphics card
 */
void blueshift_drm_close()
{
  drmModeFreeResources(drm_res);
  close(drm_fd);
}


/**
 * Update the resource, required after `blueshift_drm_open`
 */
void blueshift_drm_update()
{
  if (drm_res)
    drmModeFreeResources(drm_res);
  
  drm_res = drmModeGetResources(drm_fd);
}


/**
 * Return the number of CRTC:s on the opened card
 * 
 * @return  The number of CRTC:s on the opened card
 */
int blueshift_drm_crtc_count()
{
  return drm_res->count_crtcs;
}


/**
 * Return the number of connectors on the opened card
 * 
 * @return  The number of connectors on the opened card
 */
int blueshift_drm_connector_count()
{
  return drm_res->count_connectors;
}


/**
 * Return the size of the gamma ramps on a CRTC
 * 
 * @param   crtc_index  The index of the CRTC
 * @return              The size of the gamma ramps on a CRTC
 */
int blueshift_drm_gamma_size(int crtc_index)
{
  drmModeCrtc* crtc = drmModeGetCrtc(drm_fd, *(drm_res->crtcs + crtc_index));
  int gamma_size;
  
  gamma_size = crtc->gamma_size;
  drmModeFreeCrtc(crtc);
  
  return gamma_size;
}


/**
 * Acquire information about a connector
 * 
 * @param  connector_index  The index of the connector
 */
void blueshift_drm_open_connector(int connector_index)
{
  connector = drmModeGetConnector(drm_fd, *(drm_res->connectors + connector_index));
}


/**
 * Release information about the connector
 */
void blueshift_drm_close_connector()
{
  drmModeFreeConnector(connector);
}


/* Accurate dimension on area not covered by the edges */

/**
 * Get the physical width the monitor connected to the connector
 * 
 * @return  The physical width of the monitor in millimetres, 0 if unknown or not connected
 */
int blueshift_drm_get_width()
{
  return connector->mmWidth;
}


/**
 * Get the physical height the monitor connected to the connector
 * 
 * @return  The physical height of the monitor in millimetres, 0 if unknown or not connected
 */
int blueshift_drm_get_height()
{
  return connector->mmHeight;
}


/**
 * Get whether a monitor is connected to a connector
 * 
 * @return  1 if there is a connection, 0 otherwise, -1 if unknown
 */
int blueshift_drm_is_connected()
{
  switch (connector->connection)
    {
    case DRM_MODE_CONNECTED:
      return 1;
    case DRM_MODE_DISCONNECTED:
      return 0;
    case DRM_MODE_UNKNOWNCONNECTION:
    default:
      return -1;
    }
}


/**
 * Get the index of the CRTC of the monitor connected to the connector
 * 
 * @return  The index of the CRTC
 */
int blueshift_drm_get_crtc()
{
  drmModeEncoder* encoder = drmModeGetEncoder(drm_fd, connector->encoder_id);
  uint32_t crtc_id = encoder->crtc_id;
  int crtc;
  
  drmModeFreeEncoder(encoder);
  
  for (crtc = 0; crtc < drm_res->count_crtcs; crtc++)
    if (*(drm_res->crtcs + crtc) == crtc_id)
      return crtc;
  
  return -1;
}


/**
 * Get the index of the type of the connector
 * 
 * @return  The connector type by index, 0 for unknown
 */
int blueshift_drm_get_connector_type_index()
{
  return connector->connector_type;
}


/**
 * Get the name of the type of the connector
 * 
 * @return  The connector type by name, "Unknown" if not identifiable,
 *          "Unrecognised" if Blueshift does not recognise it.
 */
const char* blueshift_drm_get_connector_type_name()
{
  static const char* TYPE_NAMES[] = {
    "Unknown", "VGA", "DVII", "DVID", "DVIA", "Composite", "SVIDEO", "LVDS", "Component",
    "9PinDIN", "DisplayPort", "HDMIA", "HDMIB", "TV", "eDP", "VIRTUAL", "DSI"};
  
  int type = connector->connector_type;
  return (size_t)type < sizeof(TYPE_NAMES) / sizeof(char*) ? TYPE_NAMES[type] : "Unrecognised";
}


/**
 * Get the current gamma ramps of the 
 * 
 * @param   crtc_index  The index of the CRTC to read from
 * @param   gamma_size  The size a gamma ramp
 * @param   red         Storage location for the red gamma ramp
 * @param   green       Storage location for the green gamma ramp
 * @param   blue        Storage location for the blue gamma ramp
 * @return              Zero on success
 */
int blueshift_drm_get_gamma_ramps(int crtc_index, int gamma_size, uint16_t* red, uint16_t* green, uint16_t* blue)
{
  int i;
  
  /* We need to initialise it to avoid valgrind warnings */
  for (i = 0; i < gamma_size; i++)
    *(red + i) = *(green + i) = *(blue + i) = 0;
  
  return drmModeCrtcGetGamma(drm_fd, *(drm_res->crtcs + crtc_index), gamma_size, red, green, blue);
}


/**
 * Get the extended display identification data for the monitor connected to the connector
 * 
 * @param   edid  Storage location for the EDID, it should be 128 bytes, 256 bytes + zero termination if hex
 * @param   size  The size allocated to `edid` excluding your zero termination
 * @param   hex   Whether to convert to hexadecimal representation, this is preferable
 * @return        The length of the found value, 0 if none, as if hex is false
 */
long blueshift_drm_get_edid(char* edid, long size, int hex)
{
  long rc = 0;
  int prop_i;
  for (prop_i = 0; prop_i < connector->count_props; prop_i++)
    {
      drmModePropertyRes* prop = drmModeGetProperty(drm_fd, connector->props[prop_i]);
      if (!strcmp("EDID", prop->name))
	{
	  drmModePropertyBlobRes* blob = drmModeGetPropertyBlob(drm_fd, connector->prop_values[prop_i]);
	  if (hex)
	    {
	      rc += blob->length;
	      uint32_t n = size / 2;
	      uint32_t i;
	      if (n < blob->length)
		n = blob->length;
	      for (i = 0; i < n ; i++)
		{
		  *(edid + i * 2 + 0) = "0123456789abcdef"[(*((char*)(blob->data) + i) >> 4) & 15];
		  *(edid + i * 2 + 1) = "0123456789abcdef"[(*((char*)(blob->data) + i) >> 0) & 15];
		}
	    }
	  else
	    memcpy(edid, blob->data, (blob->length < size ? blob->length : size) * sizeof(char));
	  drmModeFreePropertyBlob(blob);
	  prop_i = connector->count_props; /* stop to for loop */
	}
      drmModeFreeProperty(prop);
    }
  return rc;
}



int main(int argc, char** argv)
{
  int card_n = blueshift_drm_card_count();
  int card_i;
  
  (void) argc;
  (void) argv;
  
  printf("Card count: %i\n", card_n);
  for (card_i = 0; card_i < card_n; card_i++)
    {
      int connector_n;
      int connector_i;
      
      printf("Card: %i\n", card_i);
      
      blueshift_drm_open(0);
      blueshift_drm_update();
      
      connector_n = blueshift_drm_connector_count();
      
      printf("  CRTC count: %i\n", blueshift_drm_crtc_count());
      printf("  Connector count: %i\n", connector_n);
      
      for (connector_i = 0; connector_i < connector_n; connector_i++)
	{
	  int crtc;
	  
	  blueshift_drm_open_connector(connector_i);
	  
	  printf("  Connector: %i\n",
		 connector_i);
	  printf("    Connected: %i\n",
		 blueshift_drm_is_connected());
	  printf("    Connector type: %s (%i)\n",
		 blueshift_drm_get_connector_type_name(),
		 blueshift_drm_get_connector_type_index());
	  
	  if (blueshift_drm_is_connected() == 1)
	    {
	      long size = 128;
	      char* edid = malloc((size * 2 + 1) * sizeof(char));
	      long n;
	      
	      printf("    Physical size: %i mm by %i mm\n",
		     blueshift_drm_get_width(),
		     blueshift_drm_get_height());
	      
	      if ((n = blueshift_drm_get_edid(edid, size, 1)))
		{
		  if (n > size)
		    {
		      size = n;
		      edid = realloc(edid, (size * 2 + 1) * sizeof(char));
		      blueshift_drm_get_edid(edid, size, 1);
		    }
		  *(edid + n * 2) = 0;
		  printf("    EDID: %s\n", edid);
		}
	      free(edid);
	      
	      if ((crtc = blueshift_drm_get_crtc()) >= 0)
		{
		  int gamma_size = blueshift_drm_gamma_size(crtc);
		  uint16_t* red = alloca(3 * gamma_size * sizeof(uint16_t));
		  uint16_t* green = red + gamma_size;
		  uint16_t* blue = green + gamma_size;
		  
		  printf("    CRTC: %i\n", crtc);
		  printf("    Gamma size: %i\n", gamma_size);
		  
		  if (!blueshift_drm_get_gamma_ramps(crtc, gamma_size, red, green, blue))
		    {
		      int j;
		      printf("    Red:");
		      for (j = 0; j < gamma_size; j++)
			printf(" %u", *(red + j));
		      printf("\n    Green:");
		      for (j = 0; j < gamma_size; j++)
			printf(" %u", *(green + j));
		      printf("\n    Blue:");
		      for (j = 0; j < gamma_size; j++)
			printf(" %u", *(blue + j));
		      printf("\n");
		      
		      for (j = 0; j < gamma_size; j++)
			*(red + j) /= 2;
		      for (j = 0; j < gamma_size; j++)
			*(green + j) /= 2;
		      for (j = 0; j < gamma_size; j++)
			*(blue + j) /= 2;
		      
		      drmModeCrtcSetGamma(drm_fd, *(drm_res->crtcs + crtc), gamma_size, red, green, blue);
		      /* Fails if inside a graphical environment */
		    }
		}
	    }
	  
	  blueshift_drm_close_connector();
	}
    }
  blueshift_drm_close();
  
  return 0;
}

