#!/usr/bin/env python3
copyright = '''
Copyright © 2014  Mattias Andrée (maandree@member.fsf.org)

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''
import os
import sys
import time
import signal
import datetime
import threading

from argparser import *


PROGRAM_NAME = 'blueshift'
PROGRAM_VERSION = '1.13'


## Set global variables
global DATADIR, i_size, o_size, r_curve, g_curve, b_curve, clip_result, reset, panicgate
global periodically, wait_period, fadein_time, fadeout_time, fadein_steps, fadeout_steps
global monitor_controller, running, continuous_run, panic, _globals_, conf_storage, parser
global signal_SIGTERM, signal_SIGUSR1, signal_SIGUSR2


from aux import *
from icc import *
from solar import *
from curve import *
from colour import *
from monitor import *
from backlight import *
from blackbody import *


config_file = None
'''
:str  The configuration file to load
'''


periodically = None
'''
:(int, int, int, int, int, int, int, float?)?→void  Place holder for periodically invoked function

Invoked periodically

If you want to control at what to invoke this function next time
you can set the value of the global variable `wait_period` to the
number of seconds to wait before invoking this function again.
The value does not need to be an integer.

@param   year:int     The year
@param   month:int    The month, 1 = January, 12 = December
@param   day:int      The day, minimum value is 1, probable maximum value is 31 (*)
@param   hour:int     The hour, minimum value is 0, maximum value is 23
@param   minute:int   The minute, minimum value is 0, maximum value is 59
@param   second:int   The second, minimum value is 0, probable maximum value is 60 (**)
@param   weekday:int  The weekday, 1 = Monday, 7 = Sunday
@param   fade:float?  Blueshift can use this function to fade into a state when it start
                      or exits. `fade` can either be negative, zero or positive or `None`,
                      but the magnitude of value cannot exceed 1. When Blueshift starts,
                      this function will be invoked multiple with the time parameters
                      of the time it is invoked and each time `fade` will increase towards
                      1, starting at 0, when the value is 1, the settings should be applied
                      to 100 %. After this this function will be invoked once again with
                      `fade` being `None`. When Blueshift exits the same behaviour is used
                      except, `fade` decrease towards -1 but start slightly below 0, when
                      -1 is reached all settings should be normal. Then Blueshift will NOT
                      invoke this function with `fade` being `None`, instead it will by
                      itself revert all settings and quit.

(*)  Can be exceeded if the calendar system is changed, like in 1712-(02)Feb-30
(**) See https://en.wikipedia.org/wiki/Leap_second
'''

wait_period = 60
'''
:float  The number of seconds to wait before invoking `periodically` again
'''

ttymode = not (('DISPLAY' in os.environ) and (':' in os.environ['DISPLAY']))
'''
:bool  Whether blueshift is running in a TTY, determined by the DISPLAY environment variable
'''

monitor_controller = (lambda : drm()) if ttymode else (lambda : randr())
'''
:()→void  Function used by Blueshift on exit to apply reset colour curves, if using preimplemented `reset`
'''

fadein_time = 2
'''
:float?  The number of seconds used to fade in on start, `None` for no fading
'''

fadeout_time = 2
'''
:float?  The number of seconds used to fade out on exit, `None` for no fading
'''

fadein_steps = 40
'''
:int  The number of steps in the fade in phase, if any
'''

fadeout_steps = 40
'''
:int  The number of steps in the fade out phase, if any
'''

panicgate = False
'''
:bool  `True` if translition into initial state should be skipped
'''

running = True
'''
:bool  `True` while to program has not received a terminate signal
'''

panic = False
'''
:bool  `True` if the program has received two terminate signals
'''

uses_adhoc_opts = False
'''
:bool  `True` if the configuration script parses the ad-hoc settings
'''

conf_opts = None
'''
:list<str>  This list will never be `None` and it will always have at least
            one element. This list is filled with options passed to the
            configurations, with the first element being the configuration file
'''

conf_storage = {}
'''
:dict<?, ?>  A place for you to store information that is required to survive
             a configuration reload
'''

sleep_condition = threading.Condition()
'''
:Condition  Condition used to make interruptable sleeps
'''



def reset():
    '''
    Invoked to reset the displays
    '''
    start_over()
    monitor_controller()



def signal_SIGALRM(signum, frame):
    '''
    Signal handler for SIGALRM
    
    @param  signum  The signal number, 0 if called from the program itself
    @param  frame   Ignore, it will probably be `None`
    '''
    with sleep_condition:
        sleep_condition.notify()


def signal_SIGTERM(signum, frame):
    '''
    Signal handler for SIGTERM
    
    @param  signum  The signal number, 0 if called from the program itself
    @param  frame   Ignore, it will probably be `None`
    '''
    global trans_delta, panic, running
    running = False
    if trans_delta > 0:
        panic = True
    trans_delta = 1
    with sleep_condition:
        sleep_condition.notify()


_globals_, _locals_ = globals(), dict(locals())
for key in _locals_:
    _globals_[key] = _locals_[key]
def signal_SIGUSR1(signum, frame):
    '''
    Signal handler for SIGUSR1
    
    @param  signum  The signal number, 0 if called from the program itself
    @param  frame   Ignore, it will probably be `None`
    '''
    code = None
    with open(config_file, 'rb') as script:
        code = script.read()
    code = code.decode('utf8', 'error') + '\n'
    code = compile(code, config_file, 'exec')
    exec(code, _globals_)


trans_delta = -1
def signal_SIGUSR2(signum, frame):
    '''
    Signal handler for SIGUSR2
    
    @param  signum  The signal number, 0 if called from the program itself
    @param  frame   Ignore, it will probably be `None`
    '''
    global trans_delta, panicgate
    panicgate = False
    if trans_delta == 0:
        trans_delta = 1
    else:
        trans_delta = -trans_delta
    with sleep_condition:
        sleep_condition.notify()


def continuous_run():
    '''
    Invoked to run continuously if `periodically` is not `None`
    '''
    global running, wait_period, fadein_time, fadeout_time, fadein_steps, fadeout_steps, trans_delta, p, sleep, panic
    def p(t, fade = None):
        try:
            wd = t.isocalendar()[2]
            periodically(t.year, t.month, t.day, t.hour, t.minute, t.second, wd, fade)
        except KeyboardInterrupt:
            signal_SIGTERM(0, None)
    def sleep(seconds):
        if not seconds == 0:
            try:
                with sleep_condition:
                    signal.setitimer(signal.ITIMER_REAL, seconds)
                    sleep_condition.wait()
            except KeyboardInterrupt:
                signal_SIGTERM(0, None)
            except:
                try:
                    time.sleep(seconds) # setitimer may not be supported
                except KeyboardInterrupt:
                    signal_SIGTERM(0, None)
    
    ## Catch signals
    def signal_(sig, fun):
        try:
            signal.signal(sig, fun)
        except ValueError:
            pass # not supported by the operating system
    signal_(signal.SIGTERM, signal_SIGTERM)
    signal_(signal.SIGUSR1, signal_SIGUSR1)
    signal_(signal.SIGUSR2, signal_SIGUSR2)
    signal_(signal.SIGALRM, signal_SIGALRM)
    
    ## Create initial transition
    trans_delta = -1
    trans_alpha = 1
    
    while running:
        if trans_delta == 0:
            ## Run periodically
            p(datetime.datetime.now(), None)
            if running:
                sleep(wait_period)
        elif trans_delta < 0:
            ## Fade in
            if fadein_steps <= 0:
                fadein_time = None
            if not ((fadein_time is None) or panicgate):
                if trans_alpha == 0:
                    p(datetime.datetime.now(), 1 - trans_alpha)
                    sleep(fadein_time / fadein_steps)
                trans_alpha -= 1 / fadein_steps
            if (trans_alpha <= 0) or (fadein_time is None) or panicgate:
                trans_alpha = 0
                trans_delta = 0
            p(datetime.datetime.now(), 1 - trans_alpha)
            if fadein_time is not None:
                sleep(fadein_time / fadein_steps)
        else:
            ## Fade out
            if fadeout_steps <= 0:
                fadeout_time = None
            if not (fadeout_time is None):
                trans_alpha += 1 / fadeout_steps
            if (trans_alpha >= 1) or (fadeout_time is None):
                trans_alpha = 1
            p(datetime.datetime.now(), -1 + trans_alpha)
            if trans_alpha == 1:
                try:
                    with sleep_condition:
                        sleep_condition.wait()
                except KeyboardInterrupt:
                    signal_SIGTERM(0, None)
            else:
                if fadeout_time is not None:
                    sleep(fadeout_time / fadeout_steps)
    
    ## Fade out
    if fadeout_steps <= 0:
        fadeout_time = None
    if not (fadeout_time is None):
        while not panic:
            trans_alpha += 1 / fadeout_steps
            if (trans_alpha >= 1) or (fadeout_time is None):
                trans_alpha = 1
                panic = True
            p(datetime.datetime.now(), -1 + trans_alpha)
            sleep(fadeout_time / fadeout_steps)
    
    ## Reset
    reset()


## Read command line arguments
parser = ArgParser('Colour temperature controller',
                   sys.argv[0] + ' [options] [-- configuration-options]',
                   'Blueshift adjusts the colour temperature of your\n'
                   'monitor according to brightness outside to reduce\n'
                   'eye strain and make it easier to fall asleep when\n'
                   'going to bed. IT can also be used to increase the\n'
                   'colour temperature and make the monitor bluer,\n'
                   'this helps you focus on your work.',
                   None, True, ArgParser.standard_abbreviations())

dn = '\nUse twice or daytime and nighttime respectively'
parser.add_argumented(['-c', '--configurations'], 0, 'FILE', 'Select configuration file')
parser.add_argumentless(['-p', '--panic-gate', '--panicgate'], 0, 'Skip transition into initial settings')
parser.add_argumented(['-g', '--gamma'], 0, 'RGB|R:G:B', 'Set gamma correction' + dn)
parser.add_argumented(['-b', '--brightness'], 0, 'RGB|R:G:B', 'Set brightness using sRGB' + dn)
parser.add_argumented(['+b', '++brightness'], 0, 'Y', 'Set brightness using CIE xyY' + dn)
parser.add_argumented(['-t', '--temperature'], 0, 'TEMP', 'Set colour temperature' + dn)
parser.add_argumented(['-l', '--location'], 0, 'LAT:LON', 'Select your GPS location\n'
                                                          'Measured in degrees, negative for south or west')
parser.add_argumentless(['-r', '--reset'], 0, 'Reset to default settings')
parser.add_argumented(['-o', '--output', '--crtc'], 0, 'CRTCS',
                      'Select CRTC to apply changes to\nComma separated or multiple options\n'
                      'It is best to start one instance per monitor with colour calibration')
parser.add_argumentless(['-h', '-?', '--help'], 0, 'Print this help information')
parser.add_argumentless(['-C', '--copying', '--copyright'], 0, 'Print copyright information')
parser.add_argumentless(['-W', '--warranty'], 0, 'Print non-warranty information')
parser.add_argumentless(['-v', '--version'], 0, 'Print program name and version')

parser.parse()
parser.support_alternatives()

if parser.opts['--help'] is not None:
    parser.help()
    sys.exit(0)
elif parser.opts['--copyright'] is not None:
    print(copyright[1 : -1])
    sys.exit(0)
elif parser.opts['--warranty'] is not None:
    print('This program is distributed in the hope that it will be useful,')
    print('but WITHOUT ANY WARRANTY; without even the implied warranty of')
    print('MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the')
    print('GNU Affero General Public License for more details.')
    sys.exit(0)
elif parser.opts['--version'] is not None:
    print('%s %s' % (PROGRAM_NAME, PROGRAM_VERSION))
    sys.exit(0)

a = lambda opt : opt[0] if opt is not None else None
config_file = a(parser.opts['--configurations'])
panicgate = parser.opts['--panicgate'] is not None
doreset = parser.opts['--reset'] is not None
location = a(parser.opts['--location'])
gammas = parser.opts['--gamma']
rgb_brightnesses = parser.opts['--brightness']
cie_brightnesses = parser.opts['++brightness']
temperatures = parser.opts['--temperature']
output = parser.opts['--output']
if output is None:
    output = []
used_adhoc = any([doreset, location, gammas, rgb_brightnesses, cie_brightnesses, temperatures, output])

## Verify option correctness
a = lambda opt : 0 if parser.opts[opt] is None else len(parser.opts[opt])
for opt in ('--configurations', '--panicgate', '--reset', '--location'):
    if a(opt) > 1:
        print('%s can only be used once' % opt)
        sys.exit(1)
for opt in ('--gamma', '--brightness', '++brightness', '--temperature'):
    if a(opt) > 2:
        print('%s can only be used up to two times' % opt)
        sys.exit(1)

g, l = globals(), dict(locals())
for key in l:
    g[key] = l[key]
settings = [gammas, rgb_brightnesses, cie_brightnesses, temperatures]
if (config_file is None) and any([doreset, location] + settings):
    ## Use one time configurations
    code, pathname = None, None
    for p in sys.path:
        p += '/adhoc.py'
        if os.path.exists(p):
            pathname = p
            exit
    if pathname is not None:
        with open(pathname, 'rb') as script:
            code = script.read()
    else:
        import zipimport
        importer = zipimport.zipimporter(sys.argv[0])
        code = importer.get_data('adhoc.py')
        pathname = sys.argv[0] + '/adhoc.py'
    code = code.decode('utf-8', 'error') + '\n'
    code = compile(code, pathname, 'exec')
    exec(code, g)
else:
    ## Load extension and configurations via blueshiftrc
    if config_file is None:
        for file in ('$XDG_CONFIG_HOME/%/%rc', '$HOME/.config/%/%rc', '$HOME/.%rc', '$~/.config/%/%rc', '$~/.%c', '/etc/%rc'):
            file = file.replace('%', 'blueshift')
            for arg in ('XDG_CONFIG_HOME', 'HOME'):
                if '$' + arg in file:
                    if arg in os.environ:
                        file = file.replace('$' + arg, os.environ[arg].replace('$', '\0'))
                    else:
                        file = None
                        break
            if file is not None:
                if file.startswith('$~'):
                    import pwd
                    file = pwd.getpwuid(os.getuid()).pw_dir + file[2:]
                file = file.replace('\0', '$')
                if os.path.exists(file):
                    config_file = file
                    break
    conf_opts = [config_file] + parser.files
    if config_file is not None:
        code = None
        with open(config_file, 'rb') as script:
            code = script.read()
        code = code.decode('utf-8', 'error') + '\n'
        code = compile(code, config_file, 'exec')
        exec(code, g)
    else:
        print('No configuration file found')
        sys.exit(1)
    
    ## Warn about ad-hoc settings
    if not uses_adhoc_opts:
        if used_adhoc:
            print('%s: warning: --configurations can only be combined with --panicgate' % sys.argv[0])
        parser = None

## Run periodically if configured to
if periodically is not None:
    continuous_run()

## Close C bindings to free resource and close connections
close_c_bindings()

