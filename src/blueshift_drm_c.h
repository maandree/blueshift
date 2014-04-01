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
#ifndef BLUESHIFT_DRM_C_H
#define BLUESHIFT_DRM_C_H


#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <unistd.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <fcntl.h>
#include <alloca.h>

#ifndef O_CLOEXEC
#  define O_CLOEXEC  02000000
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
 * Free all resources, but you need to close all connections first
 */
void blueshift_drm_close(void);

/**
 * Get the number of cards present on the system
 * 
 * @return  The number of cards present on the system
 */
int blueshift_drm_card_count(void);

/**
 * Open connection to a graphics card
 * 
 * @param   card_index  The index of the graphics card
 * @return              -1 on failure, otherwise an identifier for the connection to the card
 */
int blueshift_drm_open_card(int card_index);

/**
 * Update the resource, required after `blueshift_drm_open_card`
 * 
 * @param  connection  The identifier for the connection to the card
 */
void blueshift_drm_update_card(int connection);

/**
 * Close connection to the graphics card
 * 
 * @param  connection  The identifier for the connection to the card
 */
void blueshift_drm_close_card(int connection);

/**
 * Return the number of CRTC:s on the opened card
 * 
 * @param   connection  The identifier for the connection to the card
 * @return              The number of CRTC:s on the opened card
 */
int blueshift_drm_crtc_count(int connection);

/**
 * Return the number of connectors on the opened card
 * 
 * @param   connection  The identifier for the connection to the card
 * @return              The number of connectors on the opened card
 */
int blueshift_drm_connector_count(int connection);

/**
 * Return the size of the gamma ramps on a CRTC
 * 
 * @param   connection  The identifier for the connection to the card
 * @param   crtc_index  The index of the CRTC
 * @return              The size of the gamma ramps on a CRTC
 */
int blueshift_drm_gamma_size(int connection, int crtc_index);

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
int blueshift_drm_get_gamma_ramps(int connection, int crtc_index, int gamma_size, uint16_t* red, uint16_t* green, uint16_t* blue);

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
int blueshift_drm_set_gamma_ramps(int connection, int crtc_index, int gamma_size, uint16_t* red, uint16_t* green, uint16_t* blue);

/**
 * Acquire information about a connector
 * 
 * @param  connection       The identifier for the connection to the card
 * @param  connector_index  The index of the connector
 */
void blueshift_drm_open_connector(int connection, int connector_index);

/**
 * Release information about a connector
 * 
 * @param  connection       The identifier for the connection to the card
 * @param  connector_index  The index of the connector
 */
void blueshift_drm_close_connector(int connection, int connector_index);

/**
 * Get the physical width the monitor connected to a connector
 * 
 * @param   connection       The identifier for the connection to the card
 * @param   connector_index  The index of the connector
 * @return                   The physical width of the monitor in millimetres, 0 if unknown or not connected
 */
int blueshift_drm_get_width(int connection, int connector_index);

/**
 * Get the physical height the monitor connected to a connector
 * 
 * @param   connection       The identifier for the connection to the card
 * @param   connector_index  The index of the connector
 * @return                   The physical height of the monitor in millimetres, 0 if unknown or not connected
 */
int blueshift_drm_get_height(int connection, int connector_index);

/**
 * Get whether a monitor is connected to a connector
 * 
 * @param   connection       The identifier for the connection to the card
 * @param   connector_index  The index of the connector
 * @return                   1 if there is a connection, 0 otherwise, -1 if unknown
 */
int blueshift_drm_is_connected(int connection, int connector_index);

/**
 * Get the index of the CRTC of the monitor connected to a connector
 * 
 * @param   connection       The identifier for the connection to the card
 * @param   connector_index  The index of the connector
 * @return                   The index of the CRTC
 */
int blueshift_drm_get_crtc(int connection, int connector_index);

/**
 * Get the index of the type of a connector
 * 
 * @param   connection       The identifier for the connection to the card
 * @param   connector_index  The index of the connector
 * @return                   The connector type by index, 0 for unknown
 */
int blueshift_drm_get_connector_type_index(int connection, int connector_index);

/**
 * Get the name of the type of a connector
 * 
 * @param   connection       The identifier for the connection to the card
 * @param   connector_index  The index of the connector
 * @return                   The connector type by name, "Unknown" if not identifiable,
 *                           "Unrecognised" if Blueshift does not recognise it.
 */
const char* blueshift_drm_get_connector_type_name(int connection, int connector_index);

/**
 * Get the extended display identification data for the monitor connected to a connector
 * 
 * @param   connection       The identifier for the connection to the card
 * @param   connector_index  The index of the connector
 * @param   edid             Storage location for the EDID, it should be 128 bytes, 256 bytes + zero termination if hex
 * @param   size             The size allocated to `edid` excluding your zero termination
 * @param   hexadecimal      Whether to convert to hexadecimal representation, this is preferable
 * @return                   The length of the found value, 0 if none, as if hex is false
 */
long blueshift_drm_get_edid(int connection, int connector_index, char* edid, long size, int hexadecimal);



#endif

