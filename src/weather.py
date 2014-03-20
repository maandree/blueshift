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

from subprocess import Popen, PIPE


def weather(station):
    '''
    Get a brief weather report
    
    @param   station:str    The station's International Civil Aviation Organization airport code
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
    url = 'http://weather.noaa.gov/pub/data/observations/metar/decoded/%s.TXT'
    url %= station.upper()
    proc = Popen(['wget', url, '-O', '-'], stdout = PIPE, stderr = PIPE)
    output = proc.communicate()[0]
    if not proc.returncode == 0:
        return None
    output = output.decode('utf-8', 'replace').split('\n')
    output = [line.lower().split(': ') for line in output if ': ' in line]
    output = dict([(line[0], ': '.join(line[1:])) for line in output])
    sky_conditions = 'clear' if 'sky conditions' not in output else output['sky conditions']
    visibility = None
    try:
        if 'visibility' in output:
            visibility = output['visibility'].split(':')[0]
            visibility = visibility.replace(' mile(s)', '')
            visibility = visibility.replace(' miles', '')
            visibility = visibility.replace(' mile', '')
            visibility_eq = 0
            if visibility.startswith('greater than '):
                visibility_eq = 1
                visibility = visibility[len('greater than '):]
            if visibility.startswith('less than '):
                visibility_eq = -1
                visibility = visibility[len('less than '):]
            if len(list(filter(lambda c : not (('0' <= c <= '9') or (c in ' /')), visibility))) == 0:
                visibility = sum([eval(v) for v in visibility.split(' ')])
                visibility = (visibility_eq, visibility * 1.609)
            else:
                visibility = None
    except:
        visibility = None
    weather = '' if 'weather' not in output else output['weather']
    weather = weather.replace(',', ';').replace(' with ', ';')
    weather = weather.replace(' in the vicinity', '')
    weather = weather.replace(' observed', '')
    weather = weather.replace(' during the past hour', '')
    weather = [w.replace(';', '').strip() for w in weather.split(';') if not w == '']
    return (sky_conditions, visibility, weather)

