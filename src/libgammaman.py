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

# This module is responsible for keeping track of resources for
# the monitor module.

import libgamma


cache = {}
'''
Resource cache
'''


def get_method(name):
    '''
    Translate an adjustment method name into an ID
    
    @param   name:str?  The adjustment method's name
    @return  :int       The adjustment method's ID
    '''
    method = { 'randr'   : libgamma.LIBGAMMA_METHOD_X_RANDR
             , 'vidmode' : libgamma.LIBGAMMA_METHOD_X_VIDMODE
             , 'drm'     : libgamma.LIBGAMMA_METHOD_LINUX_DRM
             , 'w32gdi'  : libgamma.LIBGAMMA_METHOD_W32_GDI
             , 'quartz'  : libgamma.LIBGAMMA_METHOD_QUARTZ_CORE_GRAPHICS
             , 'dummy'   : libgamma.LIBGAMMA_METHOD_DUMMY
             , None      : None
             }
    method = method[name] if name in method else None
    if name is None:
        method = libgamma.list_methods(0)[0]
    elif method is None:
        raise Exception('Invalid method: %s' % name)
    elif not libgamma.is_method_available(method):
        raise Exception('Invalid method: %s' % name)
    return method


def get_display(display, method):
    '''
    Get a display
    
    @param   display:str?       The display ID
    @param   method:int         The adjustment method
    @return  :libgamma.Display  Display object
    '''
    if display is None:
        display = libgamma.method_default_site(method)
    if method not in cache:
        cache[method] = {}
    cache_displays = cache[method]
    if display not in cache_displays:
        site = libgamma.Site(method, display)
        cache_displays[display] = site
        site.cache_screens = {}
    return cache_displays[display]


def get_screen(screen, display, method):
    '''
    Get a screen
    
    @param   screen:int        The screen index
    @param   display:str?      The display ID
    @param   method:int        The adjustment method
    @return  :libgamma.Screen  Screen object
    '''
    display = get_display(display, method)
    cache_screens = display.cache_screens
    if screen not in cache_screens:
        partition = libgamma.Partition(display, screen)
        cache_screens[screen] = partition
        partition.cache_crtcs = {}
    return cache_screens[screen]


def get_crtc(crtc, screen, display, method):
    '''
    Get a CRTC
    
    @param   crtc:int        The CRTC index
    @param   screen:int      The screen index
    @param   display:str?    The display ID
    @param   method:int      The adjustment method
    @return  :libgamma.CRTC  CRTC object
    '''
    screen = get_screen(screen, display, method)
    cache_crtcs = screen.cache_crtcs
    if crtc not in cache_crtcs:
        monitor = libgamma.CRTC(screen, crtc)
        cache_crtcs[crtc] = monitor
        (monitor.info, _) = monitor.information(~0)
    return cache_crtcs[crtc]


def close():
    '''
    Release all resources
    '''
    global cache
    del cache
    cache = {}

