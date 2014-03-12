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



int main(int argc, char** argv)
{
  (void) argc;
  (void) argv;
  
  
  printf("Card count: %i\n", blueshift_drm_card_count());
  
  blueshift_drm_open(0);
  blueshift_drm_update();
  printf("CRTC count: %i\n", blueshift_drm_crtc_count());
  printf("Connector count: %i\n", blueshift_drm_connector_count());
  
  blueshift_drm_close();
  
  return 0;
}

