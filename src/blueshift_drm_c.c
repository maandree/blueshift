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
#include <limits.h>
#include <alloca.h>

#include <xf86drm.h>
#include <xf86drmMode.h>

#ifndef PATH_MAX
  #define PATH_MAX  4096
#endif

/* Requires video group */


/**
 * Get the number of cards present on the system
 * 
 * @return  The number of cards present on the system
 */
long card_count()
{
  char* pathname = alloca(PATH_MAX * sizeof(char));
  long len = strlen("/dev/dri/card");
  long count = 0;
  struct stat attr;
  
  memcpy(pathname, "/dev/dri/card", len);
  
  for (;;)
    {
      sprintf(pathname + len, "%li", count);
      if (stat(pathname, &attr))
	break;
      count++;
    }
  
  return count;
}


int main(int argc, char** argv)
{
  (void) argc;
  (void) argv;
  
  
  printf("%li\n", card_count());
  
  return 0;
}

