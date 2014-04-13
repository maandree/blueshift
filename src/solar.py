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
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

# This module implements algorithms for calculating information about the Sun.

import math
import time



SOLAR_ELEVATION_SUNSET_SUNRISE = 0.0
'''
:float  The Sun's elevation at sunset and sunrise, measured in degrees
'''

SOLAR_ELEVATION_CIVIL_DUSK_DAWN = -6.0
'''
:float  The Sun's elevation at civil dusk and civil dawn, measured in degrees
'''

SOLAR_ELEVATION_NAUTICAL_DUSK_DAWN = -12.0
'''
:float  The Sun's elevation at nautical dusk and nautical dawn, measured in degrees
'''

SOLAR_ELEVATION_ASTRONOMICAL_DUSK_DAWN = -18.0
'''
:float  The Sun's elevation at astronomical dusk and astronomical dawn, measured in degrees
'''

SOLAR_ELEVATION_RANGE_TWILIGHT = (-18.0, 0.0)
'''
:(float, float)  The Sun's lowest and highest elevation during all periods of twilight, measured in degrees
'''

SOLAR_ELEVATION_RANGE_CIVIL_TWILIGHT = (-6.0, 0.0)
'''
:(float, float)  The Sun's lowest and highest elevation during civil twilight, measured in degrees
'''

SOLAR_ELEVATION_RANGE_NAUTICAL_TWILIGHT = (-12.0, -6.0)
'''
:(float, float)  The Sun's lowest and highest elevation during nautical twilight, measured in degrees
'''

SOLAR_ELEVATION_RANGE_ASTRONOMICAL_TWILIGHT = (-18.0, -12.0)
'''
:(float, float)  The Sun's lowest and highest elevation during astronomical twilight, measured in degrees
'''



def sun(latitude, longitude, t = None, low = -6.0, high = 3.0):
    '''
    Get the visibility of the Sun
    
    @param   latitude:float   The latitude component of your GPS coordinate
    @param   longitude:float  The longitude component of your GPS coordinate
    @param   t:float?         The time in Julian Centuries, `None` for current time
    @param   low:float        The 100 % night limit elevation of the Sun (highest when not visible)
    @param   high:float       The 100 % day limit elevation of the Sun (lowest while fully visible)
    @return  :float           The visibilty of the sun, 0 during the night, 1 during the day,
                              between 0 and 1 during twilight. Other values will not occur.
    '''
    t = julian_centuries() if t is None else t
    e = solar_elevation(latitude, longitude, t)
    e = (e - low) / (high - low)
    return min(max(0, e), 1)



# The following functions are used to calculate the result for `sun`
# (most of them) but could be used for anything else. There name is
# should tell you enough, `t` (and `noon`) is in Julian centuries
# except for in the convertion methods


def julian_day_to_epoch(t):
    '''
    Converts a Julian Day timestamp to a POSIX time timestamp
    
    @param   t:float  The time in Julian Days
    @return  :float   The time in POSIX time
    '''
    return (t - 2440587.5) * 86400.0


def epoch_to_julian_day(t):
    '''
    Converts a POSIX time timestamp to a Julian Day timestamp
    
    @param   t:float  The time in POSIX time
    @return  :float   The time in Julian Days
    '''
    return t / 86400.0 + 2440587.5


def julian_day_to_julian_centuries(t):
    '''
    Converts a Julian Day timestamp to a Julian Centuries timestamp
    
    @param   t:float  The time in Julian Days
    @return  :float   The time in Julian Centuries
    '''
    return (t - 2451545.0) / 36525.0


def julian_centuries_to_julian_day(t):
    '''
    Converts a Julian Centuries timestamp to a Julian Day timestamp
    
    @param   t:float  The time in Julian Centuries
    @return  :float   The time in Julian Days
    '''
    return t * 36525.0 + 2451545.0


def epoch_to_julian_centuries(t):
    '''
    Converts a POSIX time timestamp to a Julian Centuries timestamp
    
    @param   t:float  The time in POSIX time
    @return  :float   The time in Julian Centuries
    '''
    return julian_day_to_julian_centuries(epoch_to_julian_day(t))


def julian_centuries_to_epoch(t):
    '''
    Converts a Julian Centuries timestamp to a POSIX time timestamp
    
    @param   t:float  The time in Julian Centuries
    @return  :float   The time in POSIX time
    '''
    return julian_day_to_epoch(julian_centuries_to_julian_day(t))


def epoch():
    '''
    Get current POSIX time
    
    @return  :float  The current POSIX time
    '''
    return time.time()


def julian_day():
    '''
    Get current Julian Day time
    
    @return  :float  The current Julian Day time
    '''
    return epoch_to_julian_day(epoch())


def julian_centuries():
    '''
    Get current Julian Centuries time (100 Julian days since J2000)
    
    @return  :float  The current Julian Centuries time
    '''
    return epoch_to_julian_centuries(epoch())


def radians(deg):
    '''
    Convert an angle from degrees to radians
    
    @param   deg:float  The angle in degrees
    @return  :float     The angle in radians
    '''
    return deg * math.pi / 180


def degrees(rad):
    '''
    Convert an angle from radians to degrees
    
    @param   rad:float  The angle in radians
    @return  :float     The angle in degrees
    '''
    return rad * 180 / math.pi


def sun_geometric_mean_longitude(t):
    '''
    Calculates the Sun's geometric mean longitude
    
    @param   t:float  The time in Julian Centuries
    @return  :float   The Sun's geometric mean longitude in radians
    '''
    return radians((0.0003032 * t ** 2 + 36000.76983 * t + 280.46646) % 360)
    # CANNIBALISERS and TIME TRAVELERS:
    #     The result of this function should always be positive, this
    #     means that after division modulo 360 but before `radians`,
    #     you will need to add 360 if the value is negative. This can
    #     only happen if `t` is negative, which can only happen for
    #     date times before 2000-(01)Jan-01 12:00:00 par division modulo
    #     implementations with the signess of atleast the left operand.


def sun_geometric_mean_anomaly(t):
    '''
    Calculates the Sun's geometric mean anomaly
    
    @param   t:float  The time in Julian Centuries
    @return  :float   The Sun's geometric mean anomaly in radians
    '''
    return radians(-0.0001537 * t ** 2 + 35999.05029 * t + 357.52911)


def earth_orbit_eccentricity(t):
    '''
    Calculates the Earth's orbit eccentricity
    
    @param   t:float  The time in Julian Centuries
    @return  :float   The Earth's orbit eccentricity
    '''
    return -0.0000001267 * t ** 2 - 0.000042037 * t + 0.016708634


def sun_equation_of_centre(t):
    '''
    Calculates the Sun's equation of the centre, the difference between
    the true anomaly and the mean anomaly
    
    @param   t:float  The time in Julian Centuries
    @return  :float   The Sun's equation of the centre, in radians
    '''
    a = sun_geometric_mean_anomaly(t)
    rc = math.sin(1 * a) * (-0.000014 * t ** 2 - 0.004817 * t + 1.914602)
    rc += math.sin(2 * a) * (-0.000101 * t + 0.019993)
    rc += math.sin(3 * a) * 0.000289
    return radians(rc)


def sun_real_longitude(t):
    '''
    Calculates the Sun's real longitudinal position
    
    @param   t:float  The time in Julian Centuries
    @return  :float   The longitude, in radians
    '''
    rc = sun_geometric_mean_longitude(t)
    return rc + sun_equation_of_centre(t)


def sun_apparent_longitude(t):
    '''
    Calculates the Sun's apparent longitudinal position
    
    @param   t:float  The time in Julian Centuries
    @return  :float   The longitude, in radians
    '''
    rc = degrees(sun_real_longitude(t)) - 0.00569
    rc -= 0.00478 * math.sin(radians(-1934.136 * t + 125.04))
    return radians(rc)


def mean_ecliptic_obliquity(t):
    '''
    Calculates the mean ecliptic obliquity of the Sun's apparent motion without variation correction
    
    @param   t:float  The time in Julian Centuries
    @return  :float   The uncorrected mean obliquity, in radians
    '''
    rc = 0.001813 * t ** 3 - 0.00059 * t ** 2 - 46.815 * t + 21.448
    rc = 26 + rc / 60
    rc = 23 + rc / 60
    return radians(rc)


def corrected_mean_ecliptic_obliquity(t):
    '''
    Calculates the mean ecliptic obliquity of the Sun's apparent motion with variation correction
    
    @param   t:float  The time in Julian Centuries
    @return  :float   The mean obliquity, in radians
    '''
    rc = -1934.136 * t + 125.04
    rc = 0.00256 * math.cos(radians(rc))
    rc += degrees(mean_ecliptic_obliquity(t))
    return radians(rc)


def solar_declination(t):
    '''
    Calculates the Sun's declination
    
    @param   t:float  The time in Julian Centuries
    @return  :float   The Sun's declination, in radians
    '''
    rc = math.sin(corrected_mean_ecliptic_obliquity(t))
    rc *= math.sin(sun_apparent_longitude(t))
    return math.asin(rc)


def equation_of_time(t):
    '''
    Calculates the equation of time, the discrepancy between apparent and mean solar time
    
    @param   t:float  The time in Julian Centuries
    @return  :float   The equation of time, in degrees
    '''
    l = sun_geometric_mean_longitude(t)
    e = earth_orbit_eccentricity(t)
    m = sun_geometric_mean_anomaly(t)
    y = corrected_mean_ecliptic_obliquity(t)
    y = math.tan(y / 2) ** 2
    rc = y * math.sin(2 * l)
    rc += (4 * y * math.cos(2 * l) - 2) * e * math.sin(m)
    rc -= 0.5 * y ** 2 * math.sin(4 * l)
    rc -= 1.25 * e ** 2 * math.sin(2 * m)
    return 4 * degrees(rc)


def hour_angle_from_elevation(latitude, declination, elevation):
    '''
    Calculates the solar hour angle from the Sun's elevation
    
    @param   longitude:float    The longitude in degrees eastwards from Greenwich, negative for westwards
    @param   declination:float  The declination, in degrees
    @param   hour_angle:float   The suns elevation, in degrees
    @return  :float             The solar hour angle, in degrees
    '''
    if elevation == 0:
        return 0
    rc = math.cos(abs(elevation))
    rc -= math.sin(radians(latitude)) * math.sin(declination)
    rc /= math.cos(radians(latitude)) * math.cos(declination)
    rc = math.acos(rc)
    return -rc if (rc < 0) == (elevation < 0) else rc;


def elevation_from_hour_angle(latitude, declination, hour_angle):
    '''
    Calculates the Sun's elevation from the solar hour angle
    
    @param   longitude:float    The longitude in degrees eastwards from Greenwich, negative for westwards
    @param   declination:float  The declination, in degrees
    @param   hour_angle:float   The solar hour angle, in degrees
    @return  :float             The suns elevation, in degrees
    '''
    rc = math.cos(radians(latitude))
    rc *= math.cos(hour_angle) * math.cos(declination)
    rc += math.sin(radians(latitude)) * math.sin(declination)
    return math.asin(rc)


def time_of_solar_noon(t, longitude):
    '''
    Calculates the time of the closest solar noon
    
    @param   t:float          A time close to the seeked time, in Julian Centuries
    @param   longitude:float  The longitude in degrees eastwards from Greenwich, negative for westwards
    @return  :float           The time, in Julian Centuries, of the closest solar noon
    '''
    t, rc = julian_centuries_to_julian_day(t), longitude
    for (k, m) in ((-360, 0), (1440, -0.5)):
        rc = julian_day_to_julian_centuries(t + m + rc / k)
        rc = 720 - 4 * longitude - equation_of_time(rc)
    return rc


def time_of_solar_elevation(t, noon, latitude, longitude, elevation):
    '''
    Calculates the time the Sun has a specified apparent elevation at a geographical position
    
    @param   t:float          A time close to the seeked time, in Julian Centuries
    @param   noon:float       The time of the closest solar noon
    @param   latitude:float   The latitude in degrees northwards from the equator, negative for southwards
    @param   longitude:float  The longitude in degrees eastwards from Greenwich, negative for westwards
    @param   elevation:float  The solar elevation, in degrees
    @return  :float           The time, in Julian Centuries, of the specified elevation
    '''
    rc = noon
    rc, et = solar_declination(rc), equation_of_time(rc)
    rc = hour_angle_from_elevation(latitude, rc, elevation)
    rc = 720 - 4 * (longitude + degrees(rc)) - et
    
    rc = julian_day_to_julian_centuries(julian_centuries_to_julian_day(t) + rc / 1440)
    rc, et = solar_declination(rc), equation_of_time(rc)
    rc = hour_angle_from_elevation(latitude, rc, elevation)
    rc = 720 - 4 * (longitude + degrees(rc)) - et
    return rc


def solar_elevation_from_time(t, latitude, longitude):
    '''
    Calculates the Suns elevation as apparent from a geographical position
    
    @param   t:float          The time in Julian Centuries
    @param   latitude:float   The latitude in degrees northwards from the equator, negative for southwards
    @param   longitude:float  The longitude in degrees eastwards from Greenwich, negative for westwards
    @return  :float           The suns apparent at the specified time as seen from the specified position,
                              measured in degrees
    '''
    rc = julian_centuries_to_julian_day(t)
    rc = (rc - float(int(rc + 0.5)) - 0.5) * 1440
    rc = 720 - rc - equation_of_time(t)
    rc = radians(rc / 4 - longitude)
    return elevation_from_hour_angle(latitude, solar_declination(t), rc)


def solar_elevation(latitude, longitude, t = None):
    '''
    Calculates the Suns elevation as apparent from a geographical position
    
    @param   latitude:float   The latitude in degrees northwards from the equator, negative for southwards
    @param   longitude:float  The longitude in degrees eastwards from Greenwich, negative for westwards
    @param   t:float?         The time in Julian Centuries, `None` for the current time
    @return  :float           The suns apparent at the specified time as seen from the specified position,
                              measured in degrees
    '''
    rc = julian_centuries() if t is None else t
    rc = solar_elevation_from_time(rc, latitude, longitude)
    return degrees(rc)

