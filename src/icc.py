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


def load_icc(pathname):
    '''
    Load ICC profile from a file
    
    @param   pathname  The ICC profile file
    @return            Function to invoke, parameterless, to apply the ICC profile to the colour curves
    '''
    MLUT_TAG = 0x6d4c5554
    VCGT_TAG = 0x76636774
    
    def make_f(R_curve, G_curve, B_curve):
        pass ## TODO
    
    int_ = lambda bs : sum([bs[len(bs) - 1 - i] << (8 * i) for i in range(len(bs))])
    def read(n):
        if len(content) < n:
            raise Except("Premature end of file: %s" % pathname)
        rc, content[:] = content[:n], content[n:]
        return rc
    
    content = None
    with open(pathname, 'rb') as file:
        content = file.read()
    content = list(content)
    read(128)
    
    n_tags, ptr = int_(read(4)), 128 + 4
    for i_tag in range(n_tags):
        tag_name   = int_(read(4))
        tag_offset = int_(read(4))
        tag_size   = int_(read(4))
        ptr += 3 * 4
        if tag_name == MLUT_TAG:
            read(tag_offset - ptr)
            R_curve, G_curve, B_curve = [], [], []
            for i in range(256):  R_curve.append(int_(read(2)))
            for i in range(256):  G_curve.append(int_(read(2)))
            for i in range(256):  B_curve.append(int_(read(2)))
            return make_f(R_curve, G_curve, B_curve)
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
                int__ = lambda m : float(int(int_(read(m)) * 8 ** (2 - m)))
                for i in range(n_entries):  R_curve.append(int__(entry_size))
                for i in range(n_entries):  G_curve.append(int__(entry_size))
                for i in range(n_entries):  B_curve.append(int__(entry_size))
                return make_f(R_curve, G_curve, B_curve)
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

