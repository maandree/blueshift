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
 * Resources for an open connection to a graphics card
 */
typedef struct _card_connection
{
  /**
   * File descriptor for the connection
   */
  int fd;
  
  /**
   * Card resources
   */
  drmModeRes* res;
  
  /**
   * Resources for open connectors
   */
   drmModeConnector** connectors;
  
} card_connection;


/**
 * Mapping from card connection identifiers to card connection resources
 */
static card_connection* card_connections = NULL;

/**
 * Next card connection identifiers
 */
static long card_connection_ptr = 0;

/**
 * Size of the storage allocated for card connection resouces
 */
static long card_connection_size = 0;

/**
 * Card connection identifier reuse stack
 */
static long* card_connection_reusables = NULL;

/**
 * The head of `card_connection_reusables`
 */
static long card_connection_reuse_ptr = 0;

/**
 * The allocation size of `card_connection_reusables`
 */
static long card_connection_reuse_size = 0;



/**
 * Free all resources, but your need to close all connections first
 */
void blueshift_drm_close()
{
  if (card_connections)
    free(card_connections);
  
  if (card_connection_reusables)
    free(card_connection_reusables);
  
  card_connections = NULL;
  card_connection_ptr = 0;
  card_connection_size = 0;
  card_connection_reusables = NULL;
  card_connection_reuse_ptr = 0;
  card_connection_reuse_size = 0;
}


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
  struct stat _attr;
  
  for (;;)
    {
      sprintf(pathname, DRM_DEV_NAME, DRM_DIR_NAME, count);
      if (stat(pathname, &_attr))
	break;
      count++;
    }
  
  return count;
}


/**
 * Open connection to a graphics card
 * 
 * @param   card_index  The index of the graphics card
 * @return              -1 on failure, otherwise an identifier for the connection to the card
 */
int blueshift_drm_open_card(int card_index)
{
  long maxlen = strlen(DRM_DIR_NAME) + strlen(DRM_DEV_NAME) + 10;
  char* pathname = alloca(maxlen * sizeof(char));
  int fd;
  int rc;
  
  sprintf(pathname, DRM_DEV_NAME, DRM_DIR_NAME, card_index);
  
  fd = open(pathname, O_RDWR | O_CLOEXEC);
  if (fd < 0)
    {
      perror("open");
      return -1;
    }
  
  if (card_connection_reuse_ptr)
    rc = *(card_connection_reusables + --card_connection_reuse_ptr);
  else
    {
      if (card_connection_size == 0)
	card_connections = malloc((card_connection_size = 8) * sizeof(card_connection));
      else if (card_connection_ptr == card_connection_size)
	card_connections = realloc(card_connections, (card_connection_size <<= 1) * sizeof(card_connection));
      rc = card_connection_ptr++;
    }
  
  (card_connections + rc)->fd = fd;
  (card_connections + rc)->res = NULL;
  (card_connections + rc)->connectors = NULL;
  
  return rc;
}


/**
 * Update the resource, required after `blueshift_drm_open_card`
 * 
 * @param  connection  The identifier for the connection to the card
 */
void blueshift_drm_update_card(int connection)
{
  card_connection* card = card_connections + connection;
  
  if (card->res)
    drmModeFreeResources(card->res);
  
  card->res = drmModeGetResources(card->fd);
}


/**
 * Close connection to the graphics card
 * 
 * @param  connection  The identifier for the connection to the card
 */
void blueshift_drm_close_card(int connection)
{
  card_connection* card = card_connections + connection;
  
  drmModeFreeResources(card->res);
  if (card->connectors)
    free(card->connectors);
  close(card->fd);
  
  if (connection + 1 == card_connection_reuse_ptr)
    card_connection_reuse_ptr--;
  else
    {
      if (card_connection_reuse_size == 0)
	card_connection_reusables = malloc((card_connection_reuse_size = 8) * sizeof(long));
      else if (card_connection_reuse_ptr == card_connection_reuse_size)
	card_connection_reusables = realloc(card_connection_reusables, (card_connection_reuse_size <<= 1) * sizeof(long));
      *(card_connection_reusables + card_connection_reuse_ptr++) = connection;
    }
}


/**
 * Return the number of CRTC:s on the opened card
 * 
 * @param   connection  The identifier for the connection to the card
 * @return              The number of CRTC:s on the opened card
 */
int blueshift_drm_crtc_count(int connection)
{
  return (card_connections + connection)->res->count_crtcs;
}


/**
 * Return the number of connectors on the opened card
 * 
 * @param   connection  The identifier for the connection to the card
 * @return              The number of connectors on the opened card
 */
int blueshift_drm_connector_count(int connection)
{
  return (card_connections + connection)->res->count_connectors;
}


/**
 * Return the size of the gamma ramps on a CRTC
 * 
 * @param   connection  The identifier for the connection to the card
 * @param   crtc_index  The index of the CRTC
 * @return              The size of the gamma ramps on a CRTC
 */
int blueshift_drm_gamma_size(int connection, int crtc_index)
{
  card_connection* card = card_connections + connection;
  drmModeCrtc* crtc = drmModeGetCrtc(card->fd, *(card->res->crtcs + crtc_index));
  int gamma_size = crtc->gamma_size;
  
  drmModeFreeCrtc(crtc);
  return gamma_size;
}


/**
 * Get the current gamma ramps of a monitor
 * 
 * @param   connection  The identifier for the connection to the card
 * @param   crtc_index  The index of the CRTC to read from
 * @param   gamma_size  The size a gamma ramp
 * @param   red         Storage location for the red gamma ramp
 * @param   green       Storage location for the green gamma ramp
 * @param   blue        Storage location for the blue gamma ramp
 * @return              Zero on success
 */
int blueshift_drm_get_gamma_ramps(int connection, int crtc_index, int gamma_size, uint16_t* red, uint16_t* green, uint16_t* blue)
{
  card_connection* card = card_connections + connection;
  
  /* We need to initialise it to avoid valgrind warnings */
  memset(red,   0, gamma_size * sizeof(uint16_t));
  memset(green, 0, gamma_size * sizeof(uint16_t));
  memset(blue,  0, gamma_size * sizeof(uint16_t));
  
  return drmModeCrtcGetGamma(card->fd, *(card->res->crtcs + crtc_index), gamma_size, red, green, blue);
}


/**
 * Set the gamma ramps of the of a monitor
 * 
 * @param   connection  The identifier for the connection to the card
 * @param   crtc_index  The index of the CRTC to read from
 * @param   gamma_size  The size a gamma ramp
 * @param   red         The red gamma ramp
 * @param   green       The green gamma ramp
 * @param   blue        The blue gamma ramp
 * @return              Zero on success
 */
int blueshift_drm_set_gamma_ramps(int connection, int crtc_index, int gamma_size, uint16_t* red, uint16_t* green, uint16_t* blue)
{
  card_connection* card = card_connections + connection;
  
  /* Fails if inside a graphical environment */
  return drmModeCrtcSetGamma(card->fd, *(card->res->crtcs + crtc_index), gamma_size, red, green, blue);
}


/**
 * Acquire information about a connector
 * 
 * @param  connection       The identifier for the connection to the card
 * @param  connector_index  The index of the connector
 */
void blueshift_drm_open_connector(int connection, int connector_index)
{
  card_connection* card = card_connections + connection;
  
  if (card->connectors == NULL)
    card->connectors = malloc(card->res->count_connectors * sizeof(drmModeConnector*));
  *(card->connectors + connector_index) = drmModeGetConnector(card->fd, *(card->res->connectors + connector_index));
}


/**
 * Release information about a connector
 * 
 * @param  connection       The identifier for the connection to the card
 * @param  connector_index  The index of the connector
 */
void blueshift_drm_close_connector(int connection, int connector_index)
{
  drmModeFreeConnector(*((card_connections + connection)->connectors + connector_index));
}


/**
 * Get the physical width the monitor connected to a connector
 * 
 * @param   connection       The identifier for the connection to the card
 * @param   connector_index  The index of the connector
 * @return                   The physical width of the monitor in millimetres, 0 if unknown or not connected
 */
int blueshift_drm_get_width(int connection, int connector_index)
{
  /* Accurate dimension on area not covered by the edges */
  return (card_connections + connection)->connectors[connector_index]->mmWidth;
}


/**
 * Get the physical height the monitor connected to a connector
 * 
 * @param   connection       The identifier for the connection to the card
 * @param   connector_index  The index of the connector
 * @return                   The physical height of the monitor in millimetres, 0 if unknown or not connected
 */
int blueshift_drm_get_height(int connection, int connector_index)
{
  /* Accurate dimension on area not covered by the edges */
  return (card_connections + connection)->connectors[connector_index]->mmHeight;
}


/**
 * Get whether a monitor is connected to a connector
 * 
 * @param   connection       The identifier for the connection to the card
 * @param   connector_index  The index of the connector
 * @return                   1 if there is a connection, 0 otherwise, -1 if unknown
 */
int blueshift_drm_is_connected(int connection, int connector_index)
{
  switch ((card_connections + connection)->connectors[connector_index]->connection)
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
 * Get the index of the CRTC of the monitor connected to a connector
 * 
 * @param   connection       The identifier for the connection to the card
 * @param   connector_index  The index of the connector
 * @return                   The index of the CRTC
 */
int blueshift_drm_get_crtc(int connection, int connector_index)
{
  card_connection* card = card_connections + connection;
  drmModeEncoder* encoder = drmModeGetEncoder(card->fd, card->connectors[connector_index]->encoder_id);
  uint32_t crtc_id = encoder->crtc_id;
  drmModeRes* res = card->res;
  int crtc;
  int n;
  
  drmModeFreeEncoder(encoder);
  
  n = res->count_crtcs;
  for (crtc = 0; crtc < n; crtc++)
    if (*(res->crtcs + crtc) == crtc_id)
      return crtc;
  
  return -1;
}


/**
 * Get the index of the type of a connector
 * 
 * @param   connection       The identifier for the connection to the card
 * @param   connector_index  The index of the connector
 * @return                   The connector type by index, 0 for unknown
 */
int blueshift_drm_get_connector_type_index(int connection, int connector_index)
{
  return (card_connections + connection)->connectors[connector_index]->connector_type;
}


/**
 * Get the name of the type of a connector
 * 
 * @param   connection       The identifier for the connection to the card
 * @param   connector_index  The index of the connector
 * @return                   The connector type by name, "Unknown" if not identifiable,
 *                           "Unrecognised" if Blueshift does not recognise it.
 */
const char* blueshift_drm_get_connector_type_name(int connection, int connector_index)
{
  static const char* TYPE_NAMES[] = {
    "Unknown", "VGA", "DVII", "DVID", "DVIA", "Composite", "SVIDEO", "LVDS", "Component",
    "9PinDIN", "DisplayPort", "HDMIA", "HDMIB", "TV", "eDP", "VIRTUAL", "DSI"};
  
  int type = ((card_connections + connection)->connectors[connector_index])->connector_type;
  return (size_t)type < sizeof(TYPE_NAMES) / sizeof(char*) ? TYPE_NAMES[type] : "Unrecognised";
}


/**
 * Get the extended display identification data for the monitor connected to a connector
 * 
 * @param   connection       The identifier for the connection to the card
 * @param   connector_index  The index of the connector
 * @param   edid             Storage location for the EDID, it should be 128 bytes, 256 bytes + zero termination if hex
 * @param   size             The size allocated to `edid` excluding your zero termination
 * @param   hex              Whether to convert to hexadecimal representation, this is preferable
 * @return                   The length of the found value, 0 if none, as if hex is false
 */
long blueshift_drm_get_edid(int connection, int connector_index, char* edid, long size, int hex)
{
  card_connection* card = card_connections + connection;
  drmModeConnector* connector = *(card->connectors + connector_index);
  int fd = card->fd;
  long rc = 0;
  int prop_n = connector->count_props;
  int prop_i;
  
  for (prop_i = 0; prop_i < prop_n; prop_i++)
    {
      drmModePropertyRes* prop = drmModeGetProperty(fd, connector->props[prop_i]);
      if (!strcmp("EDID", prop->name))
	{
	  drmModePropertyBlobRes* blob = drmModeGetPropertyBlob(fd, connector->prop_values[prop_i]);
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
  int* cards = alloca(card_n * sizeof(int*));
  int card_i;
  
  (void) argc;
  (void) argv;
  
  printf("Card count: %i\n", card_n);
  for (card_i = 0; card_i < card_n; card_i++)
    {
      *(cards + card_i) = blueshift_drm_open_card(card_i);
      blueshift_drm_update_card(*(cards + card_i));
    }
  
  for (card_i = 0; card_i < card_n; card_i++)
    {
      int card = *(cards + card_i);
      int connector_n;
      int connector_i;
      
      printf("Card: %i\n", card_i);
      
      connector_n = blueshift_drm_connector_count(card);
      
      printf("  CRTC count: %i\n", blueshift_drm_crtc_count(card));
      printf("  Connector count: %i\n", connector_n);
      
      for (connector_i = 0; connector_i < connector_n; connector_i++)
	{
	  blueshift_drm_open_connector(card, connector_i);
	  
	  printf("  Connector: %i\n", connector_i);
	  printf("    Connected: %i\n", blueshift_drm_is_connected(card, connector_i));
	  printf("    Connector type: %s (%i)\n",
		 blueshift_drm_get_connector_type_name(card, connector_i),
		 blueshift_drm_get_connector_type_index(card, connector_i));
	  
	  if (blueshift_drm_is_connected(card, connector_i) == 1)
	    {
	      long size = 128;
	      char* edid;
	      long n;
	      int crtc;
	      
	      printf("    Physical size: %i mm by %i mm\n",
		     blueshift_drm_get_width(card, connector_i),
		     blueshift_drm_get_height(card, connector_i));
	      
	      edid = malloc((size * 2 + 1) * sizeof(char));
	      if ((n = blueshift_drm_get_edid(card, connector_i, edid, size, 1)))
		{
		  if (n > size)
		    {
		      size = n;
		      edid = realloc(edid, (size * 2 + 1) * sizeof(char));
		      blueshift_drm_get_edid(card, connector_i, edid, size, 1);
		    }
		  *(edid + n * 2) = 0;
		  printf("    EDID: %s\n", edid);
		}
	      free(edid);
	      
	      if ((crtc = blueshift_drm_get_crtc(card, connector_i)) >= 0)
		{
		  int gamma_size = blueshift_drm_gamma_size(card, crtc);
		  uint16_t* red = alloca(3 * gamma_size * sizeof(uint16_t));
		  uint16_t* green = red + gamma_size;
		  uint16_t* blue = green + gamma_size;
		  
		  printf("    CRTC: %i\n", crtc);
		  printf("    Gamma size: %i\n", gamma_size);
		  
		  if (!blueshift_drm_get_gamma_ramps(card, crtc, gamma_size, red, green, blue))
		    {
		      int i;
		      printf("    Red:");
		      for (i = 0; i < gamma_size; i++)
			printf(" %u", *(red + i));
		      printf("\n    Green:");
		      for (i = 0; i < gamma_size; i++)
			printf(" %u", *(green + i));
		      printf("\n    Blue:");
		      for (i = 0; i < gamma_size; i++)
			printf(" %u", *(blue + i));
		      printf("\n");
		      
		      for (i = 0; i < gamma_size; i++)
			*(red + i) /= 2;
		      for (i = 0; i < gamma_size; i++)
			*(green + i) /= 2;
		      for (i = 0; i < gamma_size; i++)
			*(blue + i) /= 2;
		      
		      blueshift_drm_set_gamma_ramps(card, crtc, gamma_size, red, green, blue);
		    }
		}
	    }
	}
    }
  
  for (card_i = 0; card_i < card_n; card_i++)
    {
      int card = *(cards + card_i);
      int connector_n = blueshift_drm_connector_count(card);
      int connector_i;
      
      for (connector_i = 0; connector_i < connector_n; connector_i++)
	blueshift_drm_close_connector(card, connector_i);
      
      blueshift_drm_close_card(card);
    }
  
  blueshift_drm_close();
  return 0;
}

