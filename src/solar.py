#!/usr/bin/env python3

# Copyright © 2014  Mattias Andrée (maandree@member.fsf.org)
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
# 
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

# This module implements algorithms for calculating information about the Sun.

from solar_python import *


def sun(latitude, longitude, t = None, low = -6.0, high = 3.0):
    '''
    Get the visibility of the Sun
    
    @param   latitude:float   The latitude component of your GPS coordinate
    @param   longitude:float  The longitude component of your GPS coordinate
    @param   t:float?         The time in Julian Centuries, `None` for current time
    @param   low:float        The 100 % night limit elevation of the Sun (highest when not visible)
    @param   high:float       The 100 % day limit elevation of the Sun (lowest while fully visible)
    @return  :float           The visibilty of the Sun, 0 during the night, 1 during the day,
                              between 0 and 1 during twilight. Other values will not occur
    '''
    t = julian_centuries() if t is None else t
    e = solar_elevation(latitude, longitude, t)
    e = (e - low) / (high - low)
    return min(max(0, e), 1)


def ptime(t):
    '''
    Print a time stamp in human-readable local time
    
    This function is intended for testing
    
    @param  t  The time stamp in Julian Centuries
    '''
    import datetime
    print(str(datetime.datetime.fromtimestamp(int(julian_centuries_to_epoch(t)))))

