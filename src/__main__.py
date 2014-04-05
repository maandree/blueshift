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

have_argparser = True
try:
    from argparser import *
except:
    sys.stderr.buffer.write('Warning: failed to load module \'argparser\',\n'.encode('utf-8'))
    sys.stderr.buffer.write('         command line options will not be parsed.\n'.encode('utf-8'))
    sys.stderr.buffer.flush()
    have_argparser = False



PROGRAM_NAME = 'blueshift'
'''
:str  The name of the program
'''

PROGRAM_VERSION = '1.18'
'''
:str  The version of the program
'''



## Set process title
def setproctitle(title):
    '''
    Set process title
    
    @param  title:str  The title of the process
    '''
    import ctypes
    try:
        # Create strng buffer with title
        title = title.encode(sys.getdefaultencoding(), 'replace')
        title = ctypes.create_string_buffer(title)
        if 'linux' in sys.platform:
            # Set process title on Linux
            libc = ctypes.cdll.LoadLibrary('libc.so.6')
            libc.prctl(15, ctypes.byref(title), 0, 0, 0)
        elif 'bsd' in sys.platform:
            # Set process title on at least FreeBSD
            libc = ctypes.cdll.LoadLibrary('libc.so.7')
            libc.setproctitle(ctypes.create_string_buffer(b'-%s'), title)
    except:
        pass
setproctitle(sys.argv[0])



## Set global variables
global i_size, o_size, r_curve, g_curve, b_curve, clip_result, reset, panicgate, reset_on_error
global periodically, wait_period, fadein_time, fadeout_time, fadein_steps, fadeout_steps
global monitor_controller, running, continuous_run, panic, _globals_, conf_storage, parser
global signal_SIGTERM, signal_SIGUSR1, signal_SIGUSR2, DATADIR, LIBDIR, LIBEXECDIR


## Open all modules that the configuration
## scripts may want to use so that they can
## be used without knowing the name of the
## module. After all, we may want to move
## functions are around without scripts
## breaking on us.
from aux import *
from icc import *
from solar import *
from curve import *
from colour import *
from monitor import *
from weather import *
from backlight import *
from blackbody import *
from interpolation import *



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

@param  year:int     The year
@param  month:int    The month, 1 = January, 12 = December
@param  day:int      The day, minimum value is 1, probable maximum value is 31 (*)
@param  hour:int     The hour, minimum value is 0, maximum value is 23
@param  minute:int   The minute, minimum value is 0, maximum value is 59
@param  second:int   The second, minimum value is 0, probable maximum value is 60 (**)
@param  weekday:int  The weekday, 1 = Monday, 7 = Sunday
@param  fade:float?  Blueshift can use this function to fade into a state when it start
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

trans_delta = -1
'''
:int  In what direction are with transitioning?
'''

reset_on_error = True
'''
:bool  Whether to reset the colour curves if the configuration script
       runs into an exception that it did not handle
'''


## Combine our globals and locals for the
## configuration script to use
_globals_, _locals_ = globals(), dict(locals())
for key in _locals_:
    _globals_[key] = _locals_[key]


def reset():
    '''
    Invoked to reset the displays
    '''
    # Reset colour curves
    start_over()
    # and flush adjustments
    monitor_controller()



def signal_SIGALRM(signum, frame):
    '''
    Signal handler for SIGALRM
    
    This is to time out interruptable sleeps
    
    @param  signum  The signal number, 0 if called from the program itself
    @param  frame   Ignore, it will probably be `None`
    '''
    # Break any sleep
    with sleep_condition:
        sleep_condition.notify()


def signal_SIGTERM(signum, frame):
    '''
    Signal handler for SIGTERM
    
    This is used to exit the program cleanly
    
    @param  signum  The signal number, 0 if called from the program itself
    @param  frame   Ignore, it will probably be `None`
    '''
    global trans_delta, panic, running
    # Request that the program should exit
    running = False
    # If we are already fading into clean adjustments,
    # probably because we have already got a request,
    # but perhaps because we are beginning to temporarily
    # disable the program:
    if trans_delta > 0:
        # Request that the program exit immediate,
        # but first clear adjustments.
        panic = True
    # Request fading into clean adjustmetns
    trans_delta = 1
    # Break any sleep
    with sleep_condition:
        sleep_condition.notify()


def signal_SIGUSR1(signum, frame):
    '''
    Signal handler for SIGUSR1
    
    This is used to reload configuration scripts
    
    @param  signum  The signal number, 0 if called from the program itself
    @param  frame   Ignore, it will probably be `None`
    '''
    code = None
    # Open the configuration script file,
    with open(config_file, 'rb') as script:
        # and read it.
        code = script.read()
    # Decode it, assume it is in UTF-8, and append
    # an line ending in case the the last line is
    # not empty, which would give us an exception.
    code = code.decode('utf8', 'error') + '\n'
    # Compile the script,
    code = compile(code, config_file, 'exec')
    # and run it, with it have the same
    # globals as this module, so that it can
    # not only use want we have defined, but
    # also redefine it for us.
    exec(code, _globals_)


def signal_SIGUSR2(signum, frame):
    '''
    Signal handler for SIGUSR2
    
    This is used to temporarily disable, and
    enable from such disabling of, the program
    
    @param  signum  The signal number, 0 if called from the program itself
    @param  frame   Ignore, it will probably be `None`
    '''
    global trans_delta, panicgate
    # Do no longer skip fadein transitions
    panicgate = False
    if trans_delta == 0:
        # Fade out if not already fading
        trans_delta = 1
    else:
        # Otherwise reverse the direction of the transition
        trans_delta = -trans_delta
    # Break any sleep
    with sleep_condition:
        sleep_condition.notify()


def continuous_run():
    '''
    Invoked to run continuously if `periodically` is not `None`
    '''
    global running, wait_period, fadein_time, fadeout_time, reset_on_error
    global fadein_steps, fadeout_steps, trans_delta, p, sleep, panic
    
    def p(t, fade = None):
        '''
        Refrest the adjustments
        
        @param  :datetime  The current local time
        @param  :float?    The transition state, see specifications for `periodically`
        '''
        try:
            # Extract the current weekday,
            wd = t.isocalendar()[2]
            # and invoke the function used to refresh adjustments.
            periodically(t.year, t.month, t.day, t.hour, t.minute, t.second, wd, fade)
        except KeyboardInterrupt:
            # Emulate `kill -TERM` on Control+c
            signal_SIGTERM(0, None)
    def sleep(seconds):
        '''
        Delay execution for a given number of seconds,
        or until it is request that we stop sleeping.
        
        @param  seconds:float  The number of seconds to sleep
        '''
        # Sleep only if the sleep duration is existent
        if not seconds == 0:
            try:
                with sleep_condition:
                    # Set a sleep timer,
                    signal.setitimer(signal.ITIMER_REAL, seconds)
                    # and with for it or for something else to
                    # request that we stop sleeping.
                    sleep_condition.wait()
            except KeyboardInterrupt:
                # Emulate `kill -TERM` on Control+c
                signal_SIGTERM(0, None)
            except:
                try:
                    # setitimer may not be supported,
                    # in such case, use a regular sleep
                    time.sleep(seconds)
                except KeyboardInterrupt:
                    # Emulate `kill -TERM` on Control+c
                    signal_SIGTERM(0, None)
    def now():
        '''
        Get the current local time
        
        This wrapping is done because keyboard interruptions
        affect `datetime.datetime.now`
        
        @return  :datetime  The current local time (respects summer time)
        '''
        # Retry at any time we get a keyboard interruption
        while True:
            try:
                # Get the current local time (respects summer time)
                return datetime.datetime.now()
            except KeyboardInterrupt:
                # Emulate `kill -TERM` on Control+c
                signal_SIGTERM(0, None)
    
    ## Catch signals
    def signal_(sig, fun):
        '''
        Trap a signal if the signal is supported by the operating system
        
        @param  sig:int                             The signal
        @param  fun:(signal:int, framestack:)→void  The function to run then the signal is trapped
        '''
        try:
            # Set up the signal trapping
            signal.signal(sig, fun)
        except ValueError:
            # Not supported by the operating system
            pass
    # Signal for stopping the program
    signal_(signal.SIGTERM, signal_SIGTERM)
    # Signal for reloading the configuration script
    signal_(signal.SIGUSR1, signal_SIGUSR1)
    # Signal for temporarily disable/enable the program
    signal_(signal.SIGUSR2, signal_SIGUSR2)
    # Signal used for the interruptable sleeps
    signal_(signal.SIGALRM, signal_SIGALRM)
    
    ## Create initial transition
    # Fade in
    trans_delta = -1
    # from clean state.
    trans_alpha = 1
    
    ## Used to test if fading should still be used
    with_fadein  = lambda : (fadein_steps  > 0) and (fadein_time  is not None) and not panicgate
    with_fadeout = lambda : (fadeout_steps > 0) and (fadeout_time is not None)
    
    try:
        ## Run until we get a signal to exit
        # When the program start we are fading in,
        # than we run in normal periodical state.
        # But if we get a SIGUSR2 signal we start
        # fading out until we get another at which
        # point we start fading in. When we get a
        # SIGUSR2 we set `panicgate` to be false.
        while running:
            if trans_delta == 0:
                ## Run periodically
                # Apply adjustments
                p(now(), None)
                # and, assuming that we should not exit,
                if running:
                    # sleep for a time interval selected
                    # by the configuration script.
                    sleep(wait_period)
            elif trans_delta < 0:
                ## Fade in
                # If we are using fading,
                if with_fadein():
                    # and just started
                    if trans_alpha == 0:
                        # Apply fully clean adjustments,
                        p(now(), 1 - trans_alpha)
                        # and and sleep for a short period.
                        sleep(fadein_time / fadein_steps)
                    # Then step towards adjusted state
                    trans_alpha -= 1 / fadein_steps
                # If we are not fading, which might actually
                # have beend should from `periodically`, which
                # is invoked by `p`,
                if not with_fadein():
                    # The jump to adjusted state and
                    # stop transitioning
                    trans_alpha = trans_delta = 0
                # Then apply adjusetents
                p(now(), 1 - trans_alpha)
                # And if we are using fading at this point,
                if with_fadein():
                    # wait for a short period.
                    sleep(fadein_time / fadein_steps)
            else:
                ## Fade out
                if with_fadeout():
                    # Step towards clean adjustments if we are using fading
                    trans_alpha += 1 / fadeout_steps
                # If we have clean adjustments (or hyperclean), or
                # if we do not using fading
                if (trans_alpha >= 1) or not with_fadeout():
                    # set the adjustments to clean.
                    trans_alpha = 1
                # Apply adjustments. If `trans_alpha` is 0, we have `fade = -1`
                # which means that we are fading away from adjustements but are
                # still at 100 % adjustments, moving towards `fade = 0` we are
                # removing the adjustments gradually.
                p(now(), -1 + trans_alpha)
                # If we have reached a fully clean adjustment state,
                if trans_alpha == 1:
                    try:
                        # then sleep until we gate a wakeup signal,
                        # which would be at the next SIGUSR2.
                        with sleep_condition:
                            sleep_condition.wait()
                    except KeyboardInterrupt:
                        # Emulate `kill -TERM` on Control+c
                        signal_SIGTERM(0, None)
                else:
                    # Otherwise, if are are using fading
                    if with_fadeout():
                        # we sleep for a short period.
                        sleep(fadeout_time / fadeout_steps)
    
        ## Fade out
        if with_fadeout():
            # If we should fade, fade will we have not got
            # two SIGTERM signals or keyboard interrupts
            while not panic:
                # Step towards clean adjustments
                trans_alpha += 1 / fadeout_steps
                # If we have clean adjustments (or hyperclean),
                if trans_alpha >= 1:
                    # set the adjustments to clean (in case they where hyperclean)
                    trans_alpha = 1
                    # and signal that want should stop after this stop.
                    panic = True
                # Apply adjustments. If `trans_alpha` is 0, we have `fade = -1`
                # which means that we are fading away from adjustements but are
                # still at 100 % adjustments, moving towards `fade = 0` we are
                # removing the adjustments gradually.
                p(now(), -1 + trans_alpha)
                # Stop if we should no longer fade,
                if not with_fadeout():
                    break
                # before we sleep. If we did not break
                # would would run into errors.
                sleep(fadeout_time / fadeout_steps)
        
        ## Mark that we ant to reset the colour curves
        reset_on_error = True
    finally:
        ## Reset when done, or on error if not stated otherwise
        if reset_on_error:
            reset()


## Read command line arguments
parser = None
if have_argparser:
    # Create parser
    parser = ArgParser('Colour temperature controller',
                       sys.argv[0] + ' [options] [-- configuration-options]',
                       'Blueshift adjusts the colour temperature of your\n'
                       'monitor according to brightness outside to reduce\n'
                       'eye strain and make it easier to fall asleep when\n'
                       'going to bed. It can also be used to increase the\n'
                       'colour temperature and make the monitor bluer,\n'
                       'this helps you focus on your work.',
                       None, True, ArgParser.standard_abbreviations())
    
    # Populate parser with possible options
    dn = '\nUse twice or daytime and nighttime respectively'
    parser.add_argumented(['-c', '--configurations'], 0, 'FILE', 'Select configuration file')
    parser.add_argumentless(['-p', '--panic-gate', '--panicgate'], 0, 'Skip transition into initial settings')
    parser.add_argumented(['-g', '--gamma'], 0, 'RGB|R:G:B', 'Set gamma correction' + dn)
    parser.add_argumented(['-b', '--brightness'], 0, 'RGB|R:G:B', 'Set brightness using sRGB' + dn)
    parser.add_argumented(['+b', '++brightness'], 0, 'Y', 'Set brightness using CIE xyY' + dn)
    parser.add_argumented(['-t', '--temperature'], 0, 'TEMP', 'Set colour temperature' + dn)
    parser.add_argumented(['+t', '++temperature'], 0, 'TEMP', 'Set colour temperature using CIE xyY' + dn)
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
    
    # Parse options
    parser.parse()
    parser.support_alternatives()

    # Check for no-action options
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
else:
    # Argparser was not available
    class FauxParser:
        '''
        Just a pretend-instance of an argparser parser
        '''
        def __init__(self):
            '''
            Constructor
            '''
            self.opts = {}
            self.files = []
            for o in ('--configurations', '--panicgate', '--reset', '--location', '--gamma',
                      '--brightness', '++brightness', '--temperature', '++temperature', '--output'):
                self.opts[o] = None
    parser = FauxParser()

# Get used options
a = lambda opt : opt[0] if opt is not None else None
config_file = a(parser.opts['--configurations'])
panicgate = parser.opts['--panicgate'] is not None
doreset = parser.opts['--reset'] is not None
location = a(parser.opts['--location'])
gammas = parser.opts['--gamma']
rgb_brightnesses = parser.opts['--brightness']
cie_brightnesses = parser.opts['++brightness']
rgb_temperatures = parser.opts['--temperature']
cie_temperatures = parser.opts['++temperature']
output = parser.opts['--output']
if output is None:
    output = []
# Are ad-hoc mode options used?
used_adhoc = any([doreset, location, gammas, rgb_brightnesses, cie_brightnesses,
                  rgb_temperatures, cie_temperatures, output])

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
settings = [gammas, rgb_brightnesses, cie_brightnesses, rgb_temperatures, cie_temperatures]
if (config_file is None) and any([doreset, location] + settings):
    ## Use one time configurations
    import importlib
    # Load and execute adhoc.py with the same
    # globals as this module, so that it can
    # not only use want we have defined, but
    # also redefine it for us.
    exec(importlib.find_loader('adhoc').get_code('adhoc'), g)
else:
    ## Load extension and configurations via blueshiftrc
    # No configuration script has been selected explicitly,
    # so select one automatically if the we are not running
    # in ad-hoc mode.
    if config_file is None:
        # Possible auto-selected configuration scripts,
        # earlier ones have precedence, we can only select one.
        for file in ('$XDG_CONFIG_HOME/%/%rc', '$HOME/.config/%/%rc', '$HOME/.%rc', '$~/.config/%/%rc', '$~/.%c', '/etc/%rc'):
            # Expand short-hands
            file = file.replace('/', os.sep).replace('%', 'blueshift')
            # Expand environment variables
            for arg in ('XDG_CONFIG_HOME', 'HOME'):
                # Environment variables are prefixed with $
                if '$' + arg in file:
                    if arg in os.environ:
                        # To be sure that do so no treat a $ as a variable prefix
                        # incorrectly we replace any $ in the value of the variable
                        # with NUL which is not a value pathname character.
                        file = file.replace('$' + arg, os.environ[arg].replace('$', '\0'))
                    else:
                        file = None
                        break
            # Proceed if there where no errors
            if file is not None:
                # With use $~ (instead of ~) for the user's proper home
                # directroy. HOME should be defined, but it could be missing.
                # It could also be set to another directory.
                if file.startswith('$~'):
                    import pwd
                    # Get the home (also known as initial) directory
                    # of the real user, and the rest of the path
                    file = pwd.getpwuid(os.getuid()).pw_dir + file[2:]
                # Now that we are done we can change back any NUL to $:s
                file = file.replace('\0', '$')
                # If the file we exists,
                if os.path.exists(file):
                    # select it,
                    config_file = file
                    # and stop trying files with lower precedence.
                    break
    # As the zeroth argument for the configuration script,
    # add the configurion script file. Just like the zeroth
    # command line argument is the invoked command.
    conf_opts = [config_file] + parser.files
    if config_file is not None:
        code = None
        # Read configuration script file
        with open(config_file, 'rb') as script:
            code = script.read()
        # Decode configurion script file and add a line break
        # at the end to ensure that the last line is empty.
        # If it is not, we will get errors.
        code = code.decode('utf-8', 'error') + '\n'
        # Compile the configuration script,
        code = compile(code, config_file, 'exec')
        # and run it, with it have the same
        # globals as this module, so that it can
        # not only use want we have defined, but
        # also redefine it for us.
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

