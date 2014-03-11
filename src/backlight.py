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
# GNU Affero General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import os
import sys
from subprocess import Popen


def list_backlights():
    '''
    List backlight controllers
    
    @return  list<str>  List of all backlight controllers on the system
    '''
    return os.listdir('/sys/class/backlight')


class Backlight:
    '''
    Backlight controller
    
    @variable  maxmimum:int  The maximum value, after minimum value modification
    '''
    
    def __init__(self, controller, adjbacklight = True, minimum = 0):
        '''
        Constructor
        
        @param  controller:str     The name or path of the backlight controller
        @param  adjbacklight:bool  Whether to the `adjbacklight` commmand when adjusting
        @param  minimum:int        Artificially raise the minimum from zero to avoid the
                                   backlight from getting stuck at zero when reached,
                                   as happens on some controllers
        '''
        self.__controller = controller
        if '/' not in controller:
            self.__controller = '/sys/class/backlight/%s' % controller
        
        with open('%s/max_brightness' % self.__controller, 'rb') as file:
            self.maximum = int(file.read().decode('utf-8', 'replace')[:-1]) - minimum
        
        self.__minimum = minimum
        self.__adjbacklight = adjbacklight
    
    
    @property
    def actual(self):
        '''
        Get the actual brightness
        
        @return  :int  The brightness, can be below zero if the minimum value was modified at contruction
        '''
        with open('%s/actual_brightness' % self.__controller, 'rb') as file:
            return int(file.read().decode('utf-8', 'replace')[:-1]) - self.__minimum
    
    
    @property
    def brightness(self):
        '''
        Get the brightness
        
        @return  :int  The brightness, can be below zero if the minimum value was modified at contruction
        '''
        with open('%s/brightness' % self.__controller, 'rb') as file:
            return int(file.read().decode('utf-8', 'replace')[:-1]) - self.__minimum
    
    
    @brightness.setter
    def brightness(self, value):
        '''
        Set the brightness
        
        @param  value:int  The brightness, inside the range [0, `self.maxmimum`], can be below zero,
                           but should not be below zero, if the minimum value was modified at contruction
        '''
        if not self.__adjbacklight:
            with open('%s/brightness' % self.__controller, 'wb') as file:
                file.write(('%i\n' % (value + self.__minimum)).encode('utf-8'))
                file.flush()
        else:
            cmd = ['adjbacklight', self.__controller, '--set', str(value + self.__minimum)]
            Popen(cmd, stdout = sys.stdout, stderr = sys.stderr).wait()

