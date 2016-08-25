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

# This module implements support for ICC profiles

import os
from subprocess import Popen, PIPE

from curve import *



LIBEXECDIR = 'bin'
'''
:str  Path to executable libraries, '/usr/libexec' is standard
'''



def load_icc(pathname):
    '''
    Load ICC profile from a file
    
    @param   pathname:str  The ICC profile file
    @return  :()→void      Function to invoke, parameterless, to apply the ICC profile to the colour curves
    '''
    with open(pathname, 'rb') as file:
        return parse_icc(file.read())


def get_current_icc(display = None):
    '''
    Get all currently applied ICC profiles as profile applying functions
    
    @param   display:str?                                      The display to use, `None` for the current one
    @return  list<(screen:int, monitor:int, profile:()→void)>  List of used profiles
    '''
    return [(screen, monitor, parse_icc(profile)) for screen, monitor, profile in get_current_icc_raw(display)]


def get_current_icc_raw(display = None):
    '''
    Get all currently applied ICC profiles as raw profile data
    
    @param   display:str?                                      The display to use, `None` for the current one
    @return  list<(screen:int, monitor:int, profile:bytes())>  List of used profiles
    '''
    # Generate command line arguments to execute
    command = [LIBEXECDIR + os.sep + 'blueshift_iccprofile']
    if display is not None:
        command.append(display)
    # Spawn the libexec blueshift_iccprofile
    process = Popen(command, stdout = PIPE)
    # Wait for the child process to exit and gather its output to stdout
    lines = process.communicate()[0].decode('utf-8', 'error').split('\n')
    # Ensure the tha process has exited
    while process.returncode is None:
        process.wait()
    # Throw exception if the child process failed
    if process.returncode != 0:
        raise Exception('blueshift_iccprofile exited with value %i' % process.returncode)
    rc = []
    # Get the screen, output and profile for each monitor with an _ICC_PROFILE(_n) atom set
    for s, m, p in [line.split(': ') for line in lines if not line == '']:
        # Convert the program from hexadecminal encoding to raw octet encoding
        p = bytes([int(p[i : i + 2], 16) for i in range(0, len(p), 2)])
        # List the profile
        rc.append((int(s), int(m), p))
    return rc


def parse_icc(content):
    '''
    Parse ICC profile from raw data
    
    @param   content:bytes  The ICC profile data
    @return  :()→void       Function to invoke, parameterless, to apply the ICC profile to the colour curves
    '''
    # Magic number for dual-byte precision lookup table based profiles
    MLUT_TAG = 0x6d4c5554
    # Magic number for gamma–brightness–contrast based profiles
    # and for variable precision lookup table profiles
    VCGT_TAG = 0x76636774
    
    def fcurve(R_curve, G_curve, B_curve):
        '''
        Apply an ICC profile mapping
        
        @param  R_curve:list<float>  Lookup table for the red channel
        @param  G_curve:list<float>  Lookup table for the green channel
        @param  B_curve:list<float>  Lookup table for the blue channel
        '''
        for curve, icc in curves(R_curve, G_curve, B_curve):
            for i in range(i_size):
                # Nearest neighbour
                y = int(curve[i] * (len(icc) - 1) + 0.5)
                # Trunction to actual neighbour
                y = min(max(0, y), len(icc) - 1)
                # Apply mapping
                curve[i] = icc[y]
    
    # Integers in ICC profiles are encoded with the most significant byte first
    int_ = lambda bs : sum([v << (i * 8) for i, v in enumerate(reversed(bs))])
    
    def read(n):
        '''
        Read a set of bytes for the encoded ICC profile
        
        @param   n:int       The number of bytes to read
        @return  :list<int>  The next `n` bytes of the profile
        '''
        if len(content) < n:
            raise Exception('Premature end of file: %s' % pathname)
        rc, content[:] = content[:n], content[n:]
        return rc
    
    # Convert profile encoding format for bytes to integer list
    content = list(content)
    # Skip the first 128 bytes
    read(128)
    # Get the number of bytes
    n_tags, ptr = int_(read(4)), 128 + 4
    # Create array for the lookup tables to create
    R_curve, G_curve, B_curve = [], [], []
    
    for i_tag in range(n_tags):
        # Get profile encoding type, offset to the profile and the encoding size of its data
        (tag_name, tag_offset, tag_size), ptr = [int_(read(4)) for _ in range(3)], ptr + 3 * 4
        # XXX should I not jump to the data now instead of inside the if statements' bodies?
        if tag_name == MLUT_TAG:
            ## The profile is encododed as an dual-byte precision lookup table
            # Jump to the profile data
            read(tag_offset - ptr)
            # Get the lookup table for the red channel,
            for _ in range(256):  R_curve.append(int_(read(2)) / 65535)
            # for the green channel
            for _ in range(256):  G_curve.append(int_(read(2)) / 65535)
            # and for the blue channel.
            for _ in range(256):  B_curve.append(int_(read(2)) / 65535)
            return lambda : fcurve(R_curve, G_curve, B_curve)
        elif tag_name == VCGT_TAG:
            ## The profile is encoded as with gamma, brightness and contrast values
            # or as a variable precision lookup table profile
            # Jump to the profile data
            read(tag_offset - ptr)
            # VCGT profiles starts where their magic number
            tag_name = int_(read(4))
            if not tag_name == VCGT_TAG:
                break
            # Skip four bytes
            read(4)
            # and get the actual encoding type
            gamma_type = int_(read(4))
            if gamma_type == 0:
                ## The profile is encoded as a variable precision lookup table
                (n_channels, n_entries, entry_size) = [int_(read(2)) for _ in range(3)]
                if tag_size == 1584:
                    (n_channels, n_entries, entry_size) = 3, 256, 2
                if not n_channels == 3:
                    # Assuming sRGB, can only be an correct assumption if there are exactly three channels
                    break
                # Calculate the divisor for mapping to [0, 1]
                divisor = (256 ** entry_size) - 1
                # Values are encoded in integer form with `entry_size` bytes
                int__ = lambda : int_(read(entry_size)) / divisor
                # Get the lookup table for the red channel,
                for _ in range(n_entries):  R_curve.append(int__())
                # for the green channel
                for _ in range(n_entries):  G_curve.append(int__())
                # and for the blue channel.
                for _ in range(n_entries):  B_curve.append(int__())
                return lambda : fcurve(R_curve, G_curve, B_curve)
            elif gamma_type == 1:
                ## The profile is encoded with gamma, brightness and contrast values
                # Get the gamma, brightness and contrast for the red channel,
                (r_gamma, r_min, r_max) = [int_(read(4)) / 65535 for _ in range(3)]
                # green channel
                (g_gamma, g_min, g_max) = [int_(read(4)) / 65535 for _ in range(3)]
                # and blue channel.
                (b_gamma, b_min, b_max) = [int_(read(4)) / 65535 for _ in range(3)]
                def f():
                    '''
                    Apply the gamma, brightness and contrast
                    '''
                    # Apply gamma
                    gamma(r_gamma, g_gamma, b_gamma)
                    # before brightness and contrast
                    rgb_limits(r_min, r_max, g_min, g_max, b_min, b_max)
                return f
            break
        # XXX should I not jump to (tag_offset + tag_size - ptr) here
        #     and not break the loops when unknown?
    
    raise Exception('Unsupported ICC profile file')


def make_icc_interpolation(profiles):
    '''
    An interpolation function for ICC profiles
    
    @param   profiles:list<()→void>                  Profile applying functions
    @return  :(timepoint:float, alpha:float)→void()  A function that applies an interpolation of the profiles,
                                                     it takes to arguments: the timepoint and the filter
                                                     alpha. The timepoint is normally a [0, 1] floating point
                                                     of the dayness level, this means that you only have two
                                                     ICC profiles, but you have multiple profiles, in such
                                                     case profile #⌊timepoint⌋ and profile #(⌊timepoint⌋ + 1)
                                                     (modulus the number of profiles) are interpolated with
                                                     (timepoint - ⌊timepoint⌋) weight to the second profile.
                                                     The filter alpha is a [0, 1] floating point of the degree
                                                     to which the profile should be applied.
    '''
    def f(t, a):
        # Get floor and ceiling profiles and weight
        (pro0, pro1), t = [profiles[(int(t) + 0) % len(profiles)] for i in range(2)], t % 1
        if (pro0 is pro1) and (a == 1):
            # If the floor and ceiling are the same profile,
            # and the alpha is 1, than we can just simple apply
            # one without any interpolation
            pro0()
            return
        # But otherwise, we will need to save the current curves
        r_, g_, b_ = r_curve[:], g_curve[:], b_curve[:]
        # reset the curves
        start_over()
        # and apply on of the profiles
        pro0()
        # so that we can get the mapping of one of the profiles.
        r0, g0, b0 = r_curve[:], g_curve[:], b_curve[:]
        # After which we can get the last encoding value
        n = len(r0) - 1
        rgb = None
        if pro0 is pro1:
            # Now, if the floor and ceiling profiles are than same profile,
            # then we can use just one of then interpolat between it and a clean adjustment.
            rgb = [[v * a + i * (1 - a) / n for i, v in enumerate(c0)] for c0 in (r0, g0, b0)]
        else:
            # Otherwise we need to clear the curves from the floor profile's adjustments
            start_over()
            # and apply the ceiling profile
            pro1()
            # so that we can that profile's adjustments.
            # Than we pair the floor and ceilings profile for each channel.
            r01, g01, b01 = (r0, r_curve[:]), (g0, g_curve[:]), (b0, b_curve[:])
            # Now that we have two profiles, when we interpolate between them and a clean
            # state, we first interpolate the profiles and the interpolate between that
            # interpolation and a clean adjustment.
            interpol = lambda i, v0, v1 : (v0 * (1 - t) + v1 * t) * a + i * (1 - a) / n
            rgb = [[interpol(i, v0, v1) for i, (v0, v1) in enumerate(zip(*c01))] for c01 in (r01, g01, b01)]
        # Now that we have read the profiles, it is time to restore the curves to the
        # state they were in,
        r_curve[:], g_curve[:], b_curve[:] = r_, g_, b_
        # and apply the interpolated profile adjustments on top of it.
        for curve, icc in curves(*rgb):
            for i in range(i_size):
                # Nearest neighbour
                y = int(curve[i] * (len(icc) - 1) + 0.5)
                # Trunction to actual neighbour
                y = min(max(0, y), len(icc) - 1)
                # Apply mapping
                curve[i] = icc[y]
    return f

