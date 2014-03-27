#!/usr/bin/env python3

# Copyright © 2014  Mattias Andrée (maandree@member.fsf.org)
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

# The module implements support for retrieval of weather reports

from subprocess import Popen, PIPE


def weather(station, downloader = None):
    '''
    Get a brief weather report
    
    Airports should publish METAR (Meteorological Aerodrome Report) reports at XX:20 and XX:50,
    it can presumable take some time before the collection server we use (weather.noaa.gov) have
    received it. Additionally some airports do not update while closed, and updates while closed
    are less accurate.
    
    @param   station:str                      The station's International Civil Aviation
                                              Organization airport code
    @param   downloader:(url:str)?→list<str>  A function that, with an URL as input, returns
                                              a command to download the file at the URL to stdout
    @return  :(sky:str, visiblity:(:int, :float)?, weather:list<str>)?
                            The sky condition, visiblity and weather. Sky condition values include
                            ‘clear’, ‘mostly clear’, ‘partly cloudy’, ‘mostly cloudy’, ‘overcast’
                            and ‘obscured’. The visibility consists of two parameters: the first
                            on indicates the the visiblity is a upper bound if the value is -1,
                            a lower bound if +1, and approximate if 0; the second parameter is the
                            visibility in kilometers. If the visibility is unknown the value will
                            be `None`. The weather is a list that can, and often is, empty. `None`
                            is return if observation data cannot be downloaded.
    '''
    ## URI of METAR
    url = 'http://weather.noaa.gov/pub/data/observations/metar/decoded/%s.TXT'
    url %= station.upper()
    ## Download METAR
    # Use wget if not specified
    if downloader is None:
        downloader = lambda u : ['wget', u, '-O', '-']
    proc = Popen(downloader(url), stdout = PIPE, stderr = PIPE)
    ## Wait for download to finish and fetch output
    output = proc.communicate()[0]
    # Ignore output if it was not successful
    if not proc.returncode == 0:
        return None
    ## Create field table from
    output = output.decode('utf-8', 'replace').split('\n')
    output = [line.lower().split(': ') for line in output if ': ' in line]
    output = dict([(line[0], ': '.join(line[1:])) for line in output])
    ## Get sky condition, assume clear (although often not) if omitted
    sky_conditions = 'clear' if 'sky conditions' not in output else output['sky conditions']
    ## Get visibility range
    visibility = None
    try:
        if 'visibility' in output:
            # Remove tail digit
            visibility = output['visibility'].split(':')[0]
            # Remove unit, it is always miles the decoded part
            visibility = visibility.replace(' mile(s)', '')
            visibility = visibility.replace(' miles', '')
            visibility = visibility.replace(' mile', '')
            # Range is assumed approximate if not specified
            visibility_eq = 0
            if visibility.startswith('greater than '):
                # Range is a lower bound
                visibility_eq = 1
                visibility = visibility[len('greater than '):]
            if visibility.startswith('less than '):
                # Range is an upper bound
                visibility_eq = -1
                visibility = visibility[len('less than '):]
            if len(list(filter(lambda c : not (('0' <= c <= '9') or (c in ' /.')), visibility))) == 0:
                # Parse mixed numeral or decimal form
                visibility = sum([eval(v) for v in visibility.split(' ')])
                # Pack boundary information and range (converted to kilometers)
                visibility = (visibility_eq, visibility * 1.609)
            else:
                visibility = None
    except:
        ## `eval` failed (probably)
        visibility = None
    ## Get weather
    weather = '' if 'weather' not in output else output['weather']
    ## Unify conjnuctions
    weather = weather.replace(',', ';').replace(' with ', ';')
    ## Remove undesired details
    # Not important as we are not pilots, we are probably far away
    weather = weather.replace(' in the vicinity', '')
    # Duration is not important for use either
    weather = weather.replace(' during the past hour', '')
    # Unimportant detail
    weather = weather.replace(' observed', '')
    ## Split at conjunction
    weather = [w.replace(';', '').strip() for w in weather.split(';') if not w == '']
    return (sky_conditions, visibility, weather)

