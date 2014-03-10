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

from subprocess import Popen, PIPE

from curve import *


def load_icc(pathname):
    '''
    Load ICC profile from a file
    
    @param   pathname:str  The ICC profile file
    @return  :()→void       Function to invoke, parameterless, to apply the ICC profile to the colour curves
    '''
    content = None
    with open(pathname, 'rb') as file:
        content = file.read()
    return content


def get_current_icc():
    '''
    Get all currently applied ICC profiles as profile applying functions
    
    @return  list<(screen:int, monitor:int, profile:()→void)>  List of used profiles
    '''
    return [(screen, monitor, parse_icc(profile)) for screen, monitor, profile in get_current_icc_raw()]


def get_current_icc_raw():
    '''
    Get all currently applied ICC profiles as raw profile data
    
    @return  list<(screen:int, monitor:int, profile:bytes())>  List of used profiles
    '''
    process = Popen([LIBEXECDIR + "/blueshift_iccprofile"], stdout = PIPE)
    lines = process.communicate()[0].decode('utf-8', 'error').split('\n')
    while process.returncode is None:
        process.wait()
    if process.returncode != 0:
        raise Exception('blueshift_iccprofile exited with value %i' % process.returncode)
    rc = []
    for line in lines:
        if len(line) == 0:
            continue
        (s, m, p) = lines.split(': ')
        p = bytes([int(p[i : i + 2], 16) for i in range(0, len(p), 2)])
        rc.append((s, m, p))
    return rc


def parse_icc(content):
    '''
    Parse ICC profile from raw data
    
    @param   content:bytes  The ICC profile data
    @return  :()→void       Function to invoke, parameterless, to apply the ICC profile to the colour curves
    '''
    MLUT_TAG = 0x6d4c5554
    VCGT_TAG = 0x76636774
    
    def fcurve(R_curve, G_curve, B_curve):
        for curve, icc in curves(R_curve, G_curve, B_curve):
            for i in range(i_size):
                y = int(curve[i] * (len(icc) - 1) + 0.5)
                y = min(max(0, y), len(icc) - 1)
                curve[i] = icc[y]
    
    int_ = lambda bs : sum([bs[len(bs) - 1 - i] << (8 * i) for i in range(len(bs))])
    def read(n):
        if len(content) < n:
            raise Except("Premature end of file: %s" % pathname)
        rc, content[:] = content[:n], content[n:]
        return rc
    
    content = list(content)
    read(128)
    
    R_curve, G_curve, B_curve = [], [], []
    n_tags, ptr = int_(read(4)), 128 + 4
    for i_tag in range(n_tags):
        tag_name   = int_(read(4))
        tag_offset = int_(read(4))
        tag_size   = int_(read(4))
        ptr += 3 * 4
        if tag_name == MLUT_TAG:
            read(tag_offset - ptr)
            for i in range(256):  R_curve.append(int_(read(2)) / 65535)
            for i in range(256):  G_curve.append(int_(read(2)) / 65535)
            for i in range(256):  B_curve.append(int_(read(2)) / 65535)
            return lambda : fcurve(R_curve, G_curve, B_curve)
        elif tag_name == VCGT_TAG:
            read(tag_offset - ptr)
            tag_name = int_(read(4))
            if not tag_name == VCGT_TAG:
                break
            read(4)
            gamma_type = int_(read(4))
            if gamma_type == 0:
                n_channels = int_(read(2))
                n_entries  = int_(read(2))
                entry_size = int_(read(2))
                if tag_size == 1584:
                    n_channels, n_entries, entry_size = 3, 256, 2
                if not n_channels == 3: # assuming sRGB
                    break
                int__ = lambda m : int_(read(m)) / ((256 ** m) - 1)
                for i in range(n_entries):  R_curve.append(int__(entry_size))
                for i in range(n_entries):  G_curve.append(int__(entry_size))
                for i in range(n_entries):  B_curve.append(int__(entry_size))
                return lambda : fcurve(R_curve, G_curve, B_curve)
            elif gamma_type == 1:
                r_gamma = int_(read(4)) / 65535
                r_min   = int_(read(4)) / 65535
                r_max   = int_(read(4)) / 65535
                g_gamma = int_(read(4)) / 65535
                g_min   = int_(read(4)) / 65535
                g_max   = int_(read(4)) / 65535
                b_gamma = int_(read(4)) / 65535
                b_min   = int_(read(4)) / 65535
                b_max   = int_(read(4)) / 65535
                def f():
                    gamma(r_gamma, g_gamma, b_gamma)
                    rgb_limits(r_min, r_max, g_min, g_max, b_min, b_max)
                return f
            break
    
    raise Exception("Unsupported ICC profile file")

