Important!
----------

Blueshift is a bit broken in newer versions of X.
If Blueshift is not working in X for you, you may
need to change `i_size = 2 ** 8` in sr/curves.py
to `i_size = 2 ** 10`. However, this will break
Blueshift in the TTY, so may want to change it to
2 ** 10 conditionally. A proper fix is on its way.

---

**Request for contribution:**

If anyone have a multi-graphics card setup,
testing of multiple graphics cards with DRM
(in Linux TTY) is required.

---

Blueshift
---------

Inspired by Redshift, Blueshift adjusts the colour
temperature of your monitor according to brightness
outside to reduce eye strain and make it easier to
fall asleep when going to bed. It can also be used
to increase the colour temperature and make the
monitor bluer, this helps you focus on your work.

Blueshift is not user friendly and it is not meant
to be, although its user friendlyness is increasing.
Blueshift does offer limited use of command line
options to apply settings, but it is really meant
for you to have configuration files (written in
Python 3) where all the policies are implemented,
Blueshift is only meant to provide the mechanism for
modifying the colour curves.

Blueshift provides no safe guards from making your screen
unreadable (this feature [the lack of a feature] is
used in the sleepmode example) or otherwise miscoloured;
and Blueshift will never, officially, be tested on any
proprietary operating system. It may however add
theoretical support and be tested on Free Software clones
(for example ReactOS). Blueshift is fully extensible so it
is possible to make extensions that make it usable under
unsupported systems, the base code is written in Python
3 without calls to any system dependent functions (with
exception for fallbacks.) This is not necessarily true
for configuration script examples and optional features.

If Blueshift does not work for you for any of these
reasons, you should take a look at Redshift. The main
reason for using Blueshift over Redshift is to add
adjustments that they implemented in Redshift or
using very customised behaviour, such as the example
configurations scripts sleepmode, xmobar and xmonad.

Unique features
---------------

- Blueshift can cancel out effects of sigmoid curves.
This type of calibration is very difficult to get right
but is required to perfectly calibrate LCD monitors.

- Blueshift is not limited to curve operations over sRGB,
but have also support for curve operations over linear
RGB and CIE xyY. This is useful for example for more
accurate brightness modifying filters.

These two types of calibrations can be built in to lookup
tables, which ICC profiles normally uses, in other software
if it is done manually.

- Blueshift can modify the colour curves for monitors
without a display server like X or Wayland. This is done
by using Direct Rendering Manager. (This has of course
been ported to Redshift.)


Installing
----------

#### Manually

    make PREFIX=/usr/local LIBEXEC=/libexec/blueshift
    sudo make PREFIX=/usr/local LIBEXEC=/libexec/blueshift install
    sudo install-info /usr/local/share/info/{blueshift.info,dir}

See `DEPENDENCIES` for dependencies, and `Makefile` for
additional installation options.

On error make sure you do not have `--as-needed` in `LDFLAGS`.

#### Arch Linux, Parabola GNU/Linux

Blueshift is available in the Arch User Repository,
under the name `blueshift`.

