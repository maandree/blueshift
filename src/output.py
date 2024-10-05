#!/usr/bin/env python3

# Copyright © 2014, 2015, 2016, 2017  Mattias Andrée (m@maandree.se)
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

# This module is responsible for access to the monitors.

import math

from colour import *
from blackbody import *



class Tristate:
    '''
    Ternary values
    
    @constant  NO:int
    @constant  MAYBE:int
    @constant  YES:int
    '''
    NO    = 0
    MAYBE = 1
    YES   = 2

class Lifespan:
    '''
    The lifespan of a gamma adjustment, for cooperative gamma
    
    @constant  UNTIL_DEATH:int    Remove adjustment when connection to server closes or
                                  when explicitly removed
    @constant  UNTIL_REMOVAL:int  Only remove adjustment once it is requested explicitly
    @constant  REMOVE:int         Request that the adjustment be removed now
    '''
    UNTIL_DEATH = 0
    '''
    :int  Remove adjustment when connection to server closes or when explicitly removed
    '''
    
    UNTIL_REMOVAL = 1
    '''
    :int  Only remove adjustment once it is requested explicitly
    '''
    
    REMOVE = 2
    '''
    :int  Request that the adjustment be removed now
    '''

class EDID:
    '''
    Parsed EDID data
    
    @variable  manufacturer_id:str?                    The manufacturer's ID
    @variable  manufacturer_product_code:int?          Manufacturer specific product code
    @variable  serial_number:int?                      Serial number
    @variable  manufacture_week:int?                   Week of manifacture
    @variable  manufacture_year:int?                   Year of manifacture
    @variable  model_year:int?                         Year of model
    @variable  edid_version:(major:int, minor:int)?    EDID version
    @variable  digital_input:bool?                     Whether the monitor takes digital input
    @variable  vesa_dfp_1x_tmds_crgb_compatible:bool?  Whether the monitor is VESA DFP 1.x TMDS CRGB, 1 pixel
                                                       per clock, up to 8 bits per color, MSB aligned compatible
    @variable  relative_white_level:float?             Voltage level for white relative to blank
    @variable  relative_sync_level:float?              Voltage level for separate relative to blank
    @variable  blank_to_black:bool?                    Whether blank to black setup is expected
    @variable  separate_sync_supported:bool?           Whether separate synchronisation is supported
    @variable  composite_sync_supported:bool?          Whether composite synchronisation is supported
    @variable  sync_on_green_supported:bool?           Whether synchronisation on green is supported
    @variable  vsync_pulse_serrated:bool?              Whether vertical synchronisation pulse is serrated
    @variable  width_mm:int?                           The width of the monitor's viewport in millimetres
    @variable  height_mm:int?                          The heiht of the monitor's viewport in millimetres
    @variable  display_gamma:float?                    The monitor's gamma
    @variable  dpms_standby_supported:bool?            Whether DPMS standby is supported
    @variable  dpms_suspend_supported:bool?            Whether DPMS suspend is supported
    @variable  dpms_active_off_supported:bool?         Whether DPMS active-off is supported
    @variable  digital_rgb_444_supported:bool?         Whether digital RGB 4:4:4 input is supported
    @variable  digital_ycrcb_444_supported:bool?       Whether digital YCrCb 4:4:4 input is supported
    @variable  digital_ycrcb_422_supported:bool?       Whether digital YCrCb 4:2:2 input is supported
    @variable  analogue_grey_mono_display:bool?        Whether the display is greyscale or monochrome and
                                                       takes analogue input
    @variable  analogue_rgb_display:bool?              Whether the display is coloured and uses an RGB
                                                       colour space and takes analogue input
    @variable  analogue_non_rgb_display:bool?          Whether the display is coloured and uses a non-RGB
                                                       colour model and takes analogue input
    @variable  srgb:bool?                              Whether the monitor uses sRGB
    @variable  preferred_timing_mode:bool?             For EDID 1.2-: Whether the preferred timing mode is
                                                       specified in descriptor block 1.
                                                       For EDID 1.3+: Whether the preferred timing mode
                                                       (specified in descriptor block 1) includes native
                                                       pixel format and refresh rate.
    @variable  gtf_supported:bool?                     Whether Generalized Timing Formula is supported with
                                                       default parameter values
    @variable  red_chroma:(x:float, y:float)?          The CIE xyY x and y values of the red primary colour
    @variable  green_chroma:(x:float, y:float)?        The CIE xyY x and y values of the green primary colour
    @variable  blue_chroma:(x:float, y:float)?         The CIE xyY x and y values of the blue primary colour
    @variable  white_chroma:(x:float, y:float)?        The CIE xyY x and y values of the white point
    '''
    def __init__(self, edid):
        '''
        Constructor
        
        @param  edid:str  The EDID in upper case hexadecimal representation
        '''
        self.manufacturer_id = None
        self.manufacturer_product_code = None
        self.serial_number = None
        self.manufacture_week = None
        self.manufacture_year = None
        self.model_year = None
        self.edid_version = None
        self.digital_input = None
        self.vesa_dfp_1x_tmds_crgb_compatible = None
        self.relative_white_level = None
        self.relative_sync_level = None
        self.blank_to_black = None
        self.separate_sync_supported = None
        self.composite_sync_supported = None
        self.sync_on_green_supported = None
        self.vsync_pulse_serrated = None
        self.width_mm = None
        self.height_mm = None
        self.display_gamma = None
        self.dpms_standby_supported = None
        self.dpms_suspend_supported = None
        self.dpms_active_off_supported = None
        self.digital_rgb_444_supported = None
        self.digital_ycrcb_444_supported = None
        self.digital_ycrcb_422_supported = None
        self.analogue_grey_mono_display = None
        self.analogue_rgb_display = None
        self.analogue_non_rgb_display = None
        self.srgb = None
        self.preferred_timing_mode = None
        self.gtf_supported = None
        self.red_chroma = None
        self.green_chroma = None
        self.blue_chroma = None
        self.white_chroma = None
        ## FOR LEGACY {
        self.__gamma_correction = ...
        ## }
        
        if edid[:len('00FFFFFFFFFFFF00')] == '00FFFFFFFFFFFF00' or len(edid) % 2 == 1:
            return
        edid = [int(edid[i * 2 : i * 2 + 2], 16) for i in range(len(edid) // 2)]
        if len(edid) < 128 or sum(edid[:128]) % 256 != 0:
            return
        
        self.manufacturer_id = [(edid[8] >> 2) & 0x0F, (edid[9] >> 4) | (edid[8] & 1) << 4, edid[9] & 0x0F]
        self.manufacturer_id = ''.join(chr(ord('@') + c) for c in self.manufacturer_id)
        self.manufacturer_product_code = edid[10] | (edid[11] << 8)
        self.serial_number = edid[12] | (edid[13] << 8) | (edid[14] << 16) | (edid[15] << 24)
        self.manufacture_week = edid[16] # inconsistent between manufacturers
        self.manufacture_year = 1990 + edid[17]
        if self.manufacture_week == 255:
            self.model_year = self.manufacture_year
            self.manufacture_week = None
            self.manufacture_year = None
        self.edid_version = (edid[18], edid[19])
        self.digital_input = (edid[20] & 0x80) == 0x80
        if self.digital_input:
            self.vesa_dfp_1x_tmds_crgb_compatible = (edid[20] & 1) == 1
        else:
            self.relative_white_level = (0.7, 0.714, 1, 0.7)[(edid >> 5) & 3]
            self.relative_sync_level = (-0.3, -0.286, -0.4, 0)[(edid >> 5) & 3]
            self.blank_to_black = (edid[20] & 16) == 16
            self.separate_sync_supported = (edid[20] & 8) == 8
            self.composite_sync_supported = (edid[20] & 4) == 4
            self.sync_on_green_supported = (edid[20] & 2) == 2
            self.vsync_pulse_serrated = (edid[20] & 1) == 1
        self.width_mm = edid[21] * 10
        self.height_mm = edid[22] * 10
        if edid[21] == 0 or edid[22] == 0:
            self.width_mm = self.height_mm = None
        self.display_gamma = None if edid[23] == 255 else edid[23] / 100 + 1
        self.dpms_standby_supported = (edid[24] & 128) == 128
        self.dpms_suspend_supported = (edid[24] & 64) == 64
        self.dpms_active_off_supported = (edid[24] & 32) == 32
        if self.digital_input:
            self.digital_rgb_444_supported = True
            self.digital_ycrcb_444_supported = (edid[24] & 8) == 8
            self.digital_ycrcb_422_supported = (edid[24] & 16) == 16
            self.analogue_grey_mono_display = False
            self.analogue_rgb_display = False
            self.analogue_non_rgb_display = False
        else:
            self.digital_rgb_444_supported = False
            self.digital_ycrcb_444_supported = False
            self.digital_ycrcb_422_supported = False
            self.analogue_grey_mono_display = ((edid[24] >> 3) & 3) == 0
            self.analogue_rgb_display = ((edid[24] >> 3) & 3) == 1
            self.analogue_non_rgb_display = ((edid[24] >> 3) & 3) == 2
        self.srgb = (edid[24] & 4) == 4
        self.preferred_timing_mode = (edid[24] & 2) == 2
        self.gtf_supported = (edid[24] & 1) == 1
        rx = (edid[27] << 2) | ((edid[25] >> 6) & 3)
        ry = (edid[28] << 2) | ((edid[25] >> 4) & 3)
        gx = (edid[29] << 2) | ((edid[25] >> 2) & 3)
        gy = (edid[30] << 2) | ((edid[25] >> 0) & 3)
        bx = (edid[31] << 2) | ((edid[26] >> 6) & 3)
        by = (edid[32] << 2) | ((edid[26] >> 4) & 3)
        wx = (edid[33] << 2) | ((edid[26] >> 2) & 3)
        wy = (edid[34] << 2) | ((edid[26] >> 0) & 3)
        self.red_chroma   = (rx / 1024, ry / 1024)
        self.green_chroma = (gx / 1024, gy / 1024)
        self.blue_chroma  = (bx / 1024, by / 1024)
        self.white_chroma = (wx / 1024, wy / 1024)
        # There are also mode lines and maybe extensions, but yeah...

    
    ## FOR LEGACY {
    @property
    def widthmm(self):
        if not EDID.warned_widthmm:
            EDID.warned_widthmm = True
            print('EDID.widthmm is deprecated, use EDID.width_mm instead', file = sys.stderr)
        return self.width_mm
    @widthmm.setter
    def widthmm(self, value):
        if not EDID.warned_widthmm:
            EDID.warned_widthmm = True
            print('EDID.widthmm is deprecated, use EDID.width_mm instead', file = sys.stderr)
        self.width_mm = value
    @property
    def heightmm(self):
        if not EDID.warned_heightmm:
            EDID.warned_heightmm = True
            print('EDID.heightmm is deprecated, use EDID.height_mm instead', file = sys.stderr)
        return self.height_mm
    @heightmm.setter
    def heightmm(self, value):
        if not EDID.warned_heightmm:
            EDID.warned_heightmm = True
            print('EDID.heightmm is deprecated, use EDID.height_mm instead', file = sys.stderr)
        self.height_mm = value
    @property
    def gamma(self):
        if not EDID.warned_gamma:
            EDID.warned_gamma = True
            print('EDID.gamma is deprecated, use EDID.display_gamma instead', file = sys.stderr)
        return self.display_gamma
    @gamma.setter
    def gamma(self, value):
        if not EDID.warned_gamma:
            EDID.warned_gamma = True
            print('EDID.gamma is deprecated, use EDID.display_gamma instead', file = sys.stderr)
        self.display_gamma = value
    @property
    def gamma_correction(self):
        if not EDID.warned_gamma_correction:
            EDID.warned_gamma_correction = True
            print('EDID.gamma_correction is deprecated', file = sys.stderr)
        if self.__gamma_correction is ...:
            if self.display_gamma is None:
                self.__gamma_correction = None
            else:
                self.__gamma_correction = self.display_gamma / 2.2
        return self.__gamma_correction
    @gamma_correction.setter
    def gamma_correction(self, value):
        if not EDID.warned_gamma_correction:
            EDID.warned_gamma_correction = True
            print('EDID.gamma_correction is deprecated', file = sys.stderr)
        self.__gamma_correction = value

EDID.warned_widthmm = False
EDID.warned_heightmm = False
EDID.warned_gamma = False
EDID.warned_gamma_correction = False
## }


class MultiCRTC:
    '''
    A group of CRTC:s organised for efficient gamma ramp adjustments
    '''
    def __init__(self, crtcs, interpolation = None):
        '''
        Constructor
        
        @param  crtc:iter<CTRC>  The CRTC:s
        @param  interpolation:(r:list<float>, g:list<float>, b:list<float>)→
                              (r:list<float>, g:list<float>, b:list<float>)?
                                 Function used to interpolate gamma ramps to new dimentions,
                                 `None` for the default interpolator, which is intentionally
                                 unspecified
        '''
        self.interpolation = interpolation
        self.layers = []
        for crtc in crtcs:
            self.add(crtc)
    
    
    def add(self, crtc):
        '''
        Add a CRTC
        
        @param  crtc:CRTC  The CRTC to add
        '''
        found = None
        for layer in self.layers:
            ref = layer[0][0][0]
            if crtc.red_gamma_size == ref.red_gamma_size:
                if crtc.green_gamma_size == ref.green_gamma_size:
                    if crtc.blue_gamma_size == ref.blue_gamma_size:
                        found = layer
                        break
        if not found:
            found = []
            self.layers.append(found)
        
        subfound = None
        for sublayer in found:
            ref = sublayer[0][0]
            if crtc.gamma_depth == ref.gamma_depth:
                subfound = sublayer
                break
        if not subfound:
            subfound = []
            found.append(subfound)
        
        subsubfound = None
        for subsublayer in subfound:
            ref = subsublayer[0]
            if crtc.backend == ref.backend:
                subsubfound = subsublayer
                break
        if not subsubfound:
            subsubfound = []
            subfound.append(subsubfound)
        
        subsubfound.append(crtc)
    
    
    def make_ramps(self, depth = -2):
        '''
        Create a gamma-ramp trio where each ramp is as large as the
        largest ramp, of the samp colour, of the CRTCs in the group
        
        @param   depth:int  The gamma depth, 8 for unsigned 8-bit integers,
                            16 for unsigned 16-bit integers, 32 for unsigned
                            32-bit integers, 64 for unsigned 64-bit integers,
                            -1 for single-precision floating-point values, and
                            -2 for double-precision floating-point values
        @return  :Ramps     A new gamma-ramp trio suited for the group
        '''
        size = [1, 1, 1]
        for layer in self.layers:
            crtc = layer[0][0][0]
            size[0] = max(size[0], crtc.red_gamma_size)
            size[1] = max(size[1], crtc.green_gamma_size)
            size[2] = max(size[2], crtc.blue_gamma_size)
        return Ramps(None, depth = depth, size = size)
    
    
    def set_gamma(self, ramps, priority = None, rule = None, lifespan = 1):
        '''
        Set the gamma ramps on all CRTC:s in the group
        
        @param  ramps:Ramps    The gamma ramps
        @param  priority:int?  The priority of the adjustment, `None` for the default.
                               Must be `None` (default) if cooperative gamma is not supported.
        @param  rule:str?      The rule of the adjustment, `None` for the default.
                               The rule is the last part of the adjustment's identifier,
                               if this is unique within the program, it should be universally
                               unique unless another program is intentionally make it not so.
                               Must be `None` (default) if cooperative gamma is not supported.
        @param  lifespan:int   The lifespan of the algorithm: `Lifespan.UNTIL_DEATH`,
                               `Lifespan.UNTIL_REMOVAL` (default), or `Lifespan.REMOVE`
        '''
        if lifespan == Lifespan.REMOVE:
            for layer in self.layers:
                for sublayer in layer:
                    for subsublayer in sublayer:
                        for crtc in subsublayer:
                            crtc.set_gamma(None, priority, rule, lifespan)
            return
        
        for layer in self.layers:
            ref = layer[0][0][0]
            refsize = (ref.red_gamma_size, ref.green_gamma_size, ref.blue_gamma_size)
            if refsize == (len(ramps.red), len(ramps.green), len(ramps.blue)):
                ramps_size = ramps
            else:
                ramps_size = Ramps.copy(ramps, refcrtc.depth, refsize)
            for sublayer in layer:
                ref = sublayer[0][0]
                refdepth = ref.gamma_depth
                if refdepth == ramps_size.depth:
                    ramps_depth = ramps_size
                else:
                    ramps_depth = Ramps.copy(ramps, refdepth, refsize)
                for subsublayer in sublayer:
                    ramps_backend = ramps_depth
                    for crtc in subsublayer:
                        ramps_backend = crtc.set_gamma(ramps_backend, priority, rule, lifespan)


class CRTC:
    '''
    A CRTC
    
    @function  restore:(self)?→void  Restore the CLUT:s to the (configured) system
                                     defaults, `None` if not supported
    
    @variable  screen:Screen          The screen
    @variable  edid:str?              The EDID in upper case hexadecimal representation
    @variable  red_gamma_size:int?    The number of stops in the red gamma ramp
    @variable  green_gamma_size:int?  The number of stops in the green gamma ramp
    @variable  blue_gamma_size:int?   The number of stops in the blue gamma ramp
    @variable  gamma_depth:int?       The gamma depth, 8 for unsigned 8-bit integers,
                                      16 for unsigned 16-bit integers, 32 for unsigned
                                      32-bit integers, 64 for unsigned 64-bit integers,
                                      -1 for single-precision floating-point values, and
                                      -2 for double-precision floating-point values
    @variable  gamma_support:int?     0 (`Tristate.NO`) if gamma adjustments are not supported,
                                      1 (`Tristate.MAYBE`) if gamma adjustments support is unknown,
                                      and 2 (`Tristate.YES`) if gamma adjustments are supported,
    @variable  subpixel_order:str?    The subpixel order:
                                      "RGB" for red at left, green in centre, and blue at right;
                                      "BGR" for red at right, green in centre, and blue at left;
                                      "vRGB" for red at top, green in middle, and blue at bottom;
                                      "vBGR" for red at bottom, green in middle, and blue at top;
                                      and "None" for no subpixel order (e.g. on most old to
                                      semi-old CRT:s)
    @variable  active:bool?           Whether the monitor is active
    @variable  connector_name:str?    The connector name
    @variable  connector_type:str?    The connector type
    @variable  ramps                  Gamma ramps, you should not use it directly (INTERNAL)
    @variable  cooperative:bool       Whether cooperative gamma is supported
    @variable  default_rule:str       The default cooperative gamma rule (part of the class (filter identifier))
    @variable  default_priority:int   The default cooperative gamma priority (filter order)
    
    You will also find the following variables in `.edid_data`, however, here they are as
    specified by the display server rather than as specified in the EDID. This means that
    they can be been corrected by the user or the display server. On the other hand, they
    can also be incorrect. For exampel, under X.org `.width_mm` and `.height_mm` are
    calculated from assumed properties and can be completely, and horribly, wrong.
    
    @variable  manufacturer_id:str?                    The manufacturer's ID
    @variable  manufacturer_product_code:int?          Manufacturer specific product code
    @variable  serial_number:int?                      Serial number
    @variable  manufacture_week:int?                   Week of manifacture
    @variable  manufacture_year:int?                   Year of manifacture
    @variable  model_year:int?                         Year of model
    @variable  edid_version:(major:int, minor:int)?    EDID version
    @variable  digital_input:bool?                     Whether the monitor takes digital input
    @variable  vesa_dfp_1x_tmds_crgb_compatible:bool?  Whether the monitor is VESA DFP 1.x TMDS CRGB, 1 pixel
                                                       per clock, up to 8 bits per color, MSB aligned compatible
    @variable  relative_white_level:float?             Voltage level for white relative to blank
    @variable  relative_sync_level:float?              Voltage level for separate relative to blank
    @variable  blank_to_black:bool?                    Whether blank to black setup is expected
    @variable  separate_sync_supported:bool?           Whether separate synchronisation is supported
    @variable  composite_sync_supported:bool?          Whether composite synchronisation is supported
    @variable  sync_on_green_supported:bool?           Whether synchronisation on green is supported
    @variable  vsync_pulse_serrated:bool?              Whether vertical synchronisation pulse is serrated
    @variable  width_mm:int?                           The width of the monitor's viewport in millimetres
    @variable  height_mm:int?                          The heiht of the monitor's viewport in millimetres
    @variable  display_gamma:float?                    The monitor's gamma
    @variable  dpms_standby_supported:bool?            Whether DPMS standby is supported
    @variable  dpms_suspend_supported:bool?            Whether DPMS suspend is supported
    @variable  dpms_active_off_supported:bool?         Whether DPMS active-off is supported
    @variable  digital_rgb_444_supported:bool?         Whether digital RGB 4:4:4 input is supported
    @variable  digital_ycrcb_444_supported:bool?       Whether digital YCrCb 4:4:4 input is supported
    @variable  digital_ycrcb_422_supported:bool?       Whether digital YCrCb 4:2:2 input is supported
    @variable  analogue_grey_mono_display:bool?        Whether the display is greyscale or monochrome and
                                                       takes analogue input
    @variable  analogue_rgb_display:bool?              Whether the display is coloured and uses an RGB
                                                       colour space and takes analogue input
    @variable  analogue_non_rgb_display:bool?          Whether the display is coloured and uses a non-RGB
                                                       colour model and takes analogue input
    @variable  srgb:bool?                              Whether the monitor uses sRGB
    @variable  preferred_timing_mode:bool?             For EDID 1.2-: Whether the preferred timing mode is
                                                       specified in descriptor block 1.
                                                       For EDID 1.3+: Whether the preferred timing mode
                                                       (specified in descriptor block 1) includes native
                                                       pixel format and refresh rate.
    @variable  gtf_supported:bool?                     Whether Generalized Timing Formula is supported with
                                                       default parameter values
    @variable  red_chroma:(x:float, y:float)?          The CIE xyY x and y values of the red primary colour
    @variable  green_chroma:(x:float, y:float)?        The CIE xyY x and y values of the green primary colour
    @variable  blue_chroma:(x:float, y:float)?         The CIE xyY x and y values of the blue primary colour
    @variable  white_chroma:(x:float, y:float)?        The CIE xyY x and y values of the white point
    '''
    def __init__(self):
        '''
        Constructor
        '''
        self.__edid_data = ...
        self.edid = None
        self.red_gamma_size = None
        self.green_gamma_size = None
        self.blue_gamma_size = None
        self.gamma_depth = None
        self.gamma_support = None
        self.subpixel_order = None
        self.active = None
        self.connector_name = None
        self.connector_type = None
        self.ramps = None
        self.cooperative = False
        self.default_rule = 'standard'
        self.default_priority = 1 << 59
        
        # Everything that is in the EDID class, in
        # case it is specified by the display server
        # and potentially configured by the user.
        self.manufacturer_id = None
        self.manufacturer_product_code = None
        self.serial_number = None
        self.manufacture_week = None
        self.manufacture_year = None
        self.model_year = None
        self.edid_version = None
        self.digital_input = None
        self.vesa_dfp_1x_tmds_crgb_compatible = None
        self.relative_white_level = None
        self.relative_sync_level = None
        self.blank_to_black = None
        self.separate_sync_supported = None
        self.composite_sync_supported = None
        self.sync_on_green_supported = None
        self.vsync_pulse_serrated = None
        self.width_mm = None
        self.height_mm = None
        self.display_gamma = None
        self.dpms_standby_supported = None
        self.dpms_suspend_supported = None
        self.dpms_active_off_supported = None
        self.digital_rgb_444_supported = None
        self.digital_ycrcb_444_supported = None
        self.digital_ycrcb_422_supported = None
        self.analogue_grey_mono_display = None
        self.analogue_rgb_display = None
        self.analogue_non_rgb_display = None
        self.srgb = None
        self.preferred_timing_mode = None
        self.gtf_supported = None
        self.red_chroma = None
        self.green_chroma = None
        self.blue_chroma = None
        self.white_chroma = None
    
    
    def make_ramps(self, depth = None):
        '''
        Create gamma ramps with the same size as the CRTC expects
        
        @param   depth:int?  The gamma depth, 8 for unsigned 8-bit integers,
                             16 for unsigned 16-bit integers, 32 for unsigned
                             32-bit integers, 64 for unsigned 64-bit integers,
                             -1 for single-precision floating-point values,
                             -2 for double-precision floating-point values, and
                             `None` for the gamma depth the CRTC expects
        @return  :Ramps      The created gamma ramps
        '''
        return Ramps(self, depth = depth)
    
    
    @property
    def edid_data(self):
        '''
        Get parsed EDID information for the CRTC
        
        @return  :EDID  Parsed EDID information
        '''
        if self.__edid_data is ...:
            self.__edid_data = None if self.edid is None else EDID(self.edid)
        return self.__edid_data


class Screen:
    '''
    A screen or graphics card
    
    @function  restore:(self)?→void      Restore the CLUT:s to the (configured) system defaults,
                                         `None` if not supported
    
    @variable  display:Display           The display
    @variable  crtcs:list<LibgammaCRTC>  The CRTC:s in the screen
    '''
    def __len__(self):
        '''
        Get the number of CRTC:s in the screen
        
        @return  :int  The number of CRTC:s in the screen
        '''
        return len(self.crtcs)
    
    
    def __getitem__(self, indices):
        '''
        Get CRTC:s in the screen
        
        @param   indices:int|slice  The index or index range of CRTC:s to return
        @return  :CRTC|list<CRTC>   The CRTC or CRTC:s with the specified indices
        '''
        return self.crtcs[indices]
    
    
    def __iter__(self):
        '''
        Iterator of the screen's CRTC:s
        
        @yield  :CRTC  CRTC in the screen
        '''
        for value in self[:]:
            yield value


class Display:
    '''
    A display
    
    @function  restore:(self)?→void          Restore the CLUT:s to the (configured) system defaults,
                                             `None` if not supported
    
    @variable  screens:list<LibgammaScreen>  The screens in the display
    @variable  crtcs:list<LibgammaCRTC>      The CRTC:s in the display
    @variable  cooperative:bool              Whether the adjustment method supports cooperative gamma
    '''
    def __len__(self):
        '''
        Get the number of screens in the display
        
        @return  :int  The number of screens in the display
        '''
        return len(self.crtcs)
    
    
    def __getitem__(self, indices):
        '''
        Get screens in the display
        
        @param   indices:int|slice  The index or index range of screens to return
        @return  :CRTC|list<CRTC>   The screen or screens with the specified indices
        '''
        return self.crtcs[indices]
    
    
    def __iter__(self):
        '''
        Iterator of the display's screens
        
        @yield  :Screen  Screen in the display
        '''
        for value in self[:]:
            yield value


class Ramps:
    '''
    Gamma ramps
    
    @variable  red:list<float>    The gamma ramp of the red channel
    @variable  green:list<float>  The gamma ramp of the green channel
    @variable  blue:list<float>   The gamma ramp of the blue channel
    @variable  depth:int          The gamma depth, 8 for unsigned 8-bit integers,
                                  16 for unsigned 16-bit integers, 32 for unsigned
                                  32-bit integers, 64 for unsigned 64-bit integers,
                                  -1 for single-precision floating-point values, and
                                  -2 for double-precision floating-point values
    @variable  maximum:float      The largest stop value
    '''
    def __init__(self, crtc, depth = None, size = None):
        '''
        Constructor
        
        @param  crtc:CRTC?  The CRTC the ramps should match, may
                            only be `None` if neither `depth` nor
                            `size` is `None`
        @param  depth:int?  The gamma depth, 8 for unsigned 8-bit integers,
                            16 for unsigned 16-bit integers, 32 for unsigned
                            32-bit integers, 64 for unsigned 64-bit integers,
                            -1 for single-precision floating-point values,
                            -2 for double-precision floating-point values, and
                            `None` for the gamma depth the CRTC expects
        @param  size:int|(red:int, green:int, blue:int)?
                            The size of the ramps, either an integer of the size that
                            is applied to all three channels, three integers with
                            the size of each channel, or `None` for the sizes the
                            CRTC expects
        '''
        if depth is None:
            depth = crtc.depth
        if size is not None and isinstance(size, int):
            size = (size, size, size)
        self.depth = depth
        self.maximum = 1 if depth < 0 else (1 << depth) - 1
        if depth > 0:
            def make_ramp(depth, size):
                return [int(x * self.maximum / (size - 1) + 0.5) for x in range(size)]
        else:
            def make_ramp(depth, size):
                return [x / (size - 1) for x in range(size)]
        self.red   = make_ramp(self.depth, crtc.red_gamma_size   if size is None else size[0])
        self.green = make_ramp(self.depth, crtc.green_gamma_size if size is None else size[1])
        self.blue  = make_ramp(self.depth, crtc.blue_gamma_size  if size is None else size[2])
    
    
    def copy(self, depth = None, size = None, interpolation = None):
        '''
        Create a copy, optionally with a new depth or size
        
        @param   depth:int?  The gamma depth in the copy, 8 for unsigned 8-bit integers,
                             16 for unsigned 16-bit integers, 32 for unsigned
                             32-bit integers, 64 for unsigned 64-bit integers,
                             -1 for single-precision floating-point values,
                             -2 for double-precision floating-point values, and
                             `None` for the gamma depth of the original (`self`)
        @param   size:int|(red:int, green:int, blue:int)?
                             The size of the copy, either an integer of the size that
                             is applied to all three channels, three integers with
                             the size of each channel, or `None` for the sizes of
                             the original
        @param   interpolation:(red:list<float>, green:list<float>, blue:list<float>)?→
                               (red:list<float>, green:list<float>, blue:list<float>)
                             Function used for interpolation used for resizing the
                             ramps. `None` for the default, which is intentionally
                             unspecified.
        @return  :Ramps      The copy
        '''
        if size is None:
            size = (len(self.red), len(self.green), len(self.blue))
        r = Ramps(None, self.depth if depth is None else depth, size)
        ramps = (self.red, self.green, self.blue)
        if len(self.red) == len(r.red) and len(self.green) == len(r.green) and len(self.blue) == len(r.blue):
            pass
        elif interpolation is None:
            import interpolation as interpol
            ramps = interpol.linearly_interpolate_ramp(*ramps, size = size)
        else:
            ramps = interpolation(*ramps, size = size)
        r.red[:]   = ramps[0]
        r.green[:] = ramps[1]
        r.blue[:]  = ramps[2]
        if r.maximum != self.maximum:
            for ramp in (r.red, r.green, r.blue):
                for i in range(len(ramp)):
                    ramp[i] = ramp[i] * r.maximum / self.maximum
        return r
    
    
    def __str__(self, compact = False):
        '''
        Create a string of the ramps that is useful for debugging
        
        @param   compact:bool  Whether to apply run-length compression when suitable
        @return  :str          A printable string
        '''
        if not compact:
            return '%s\n%s\n%s' % (repr(red), repr(green), repr(blue))
        rgb = ([], [], [])
        for r, w in zip((self.red, self.green, self.blue), rgb):
            last, count = None, 0
            for value in r:
                if self.depth > 0:
                    value = int(value + 0.5)
                if value == last:
                    count += 1
                else:
                    if last is not None:
                        if count > 1:
                            w.append(repr(last))
                        else:
                            w.append('%s {%i}' % (repr(last), count))
                    last = value
                    count = 1
            if last is not None:
                if count > 1:
                    w.append(repr(last))
                else:
                    w.append('%s {%i}' % (repr(last), count))
        return '[%s]\n[%s]\n[%s]' % (', '.join(rgb[0]), ', '.join(rgb[1]), ', '.join(rgb[2]))
    
    
    def __bool(self, r, g, b):
        if g is ...:  g = r
        if b is ...:  b = g
        ret = []
        if r:  ret.append(self.red)
        if g:  ret.append(self.green)
        if b:  ret.append(self.blue)
        return ret
    
    
    def __datum(self, r, g, b):
        if g is ...:  g = r
        if b is ...:  b = g
        ret = []
        if r is not None:  ret.append((self.red, r))
        if g is not None:  ret.append((self.green, g))
        if b is not None:  ret.append((self.blue, b))
        return ret
    
    
    def temperature(self, temperature, algorithm):
        '''
        Change colour temperature according to the CIE illuminant series D using CIE sRBG
        
        @param  temperature:float|str                    The blackbody temperature in kelvins, or a name
        @param  algorithm:(float)→(float, float, float)  Algorithm for calculating a white point, for example `cmf_10deg`
        '''
        self.rgb_temperature(temperature, algorithm)
    
    
    def rgb_temperature(self, temperature, algorithm):
        '''
        Change colour temperature according to the CIE illuminant series D using CIE sRBG
        
        @param  temperature:float|str                    The blackbody temperature in kelvins, or a name
        @param  algorithm:(float)→(float, float, float)  Algorithm for calculating a white point, for example `cmf_10deg`
        '''
        # Resolve colour temperature name
        temperature = kelvins(temperature)
        # Do nothing if the temperature is neutral
        if temperature == 6500:  return
        # Otherwise manipulate the colour curves
        self.rgb_brightness(*(algorithm(temperature)))
    
    
    def cie_temperature(self, temperature, algorithm):
        '''
        Change colour temperature according to the CIE illuminant series D using CIE xyY
        
        @param  temperature:float|str                    The blackbody temperature in kelvins, or a name
        @param  algorithm:(float)→(float, float, float)  Algorithm for calculating a white point, for example `cmf_10deg`
        '''
        # Resolve colour temperature name
        temperature = kelvins(temperature)
        # Do nothing if the temperature is neutral
        if temperature == 6500:  return
        # Otherwise manipulate the colour curves
        self.cie_brightness(*(algorithm(temperature)))
    
    
    def rgb_contrast(self, r, g = ..., b = ...):
        '''
        Apply contrast correction on the colour curves using sRGB
        
        In this context, contrast is a measure of difference between the whitepoint and blackpoint,
        if the difference is 0 than they are both grey
        
        @param  r:float?      The contrast parameter for the red curve
        @param  g:float|...?  The contrast parameter for the green curve, defaults to `r` if `...`
        @param  b:float|...?  The contrast parameter for the blue curve, defaults to `g` if `...`
        '''
        half = self.maximum / 2
        for (curve, level) in self.__value(r, g, b):
            if not level == 1.0:
                curve[:] = [(y - half) * level + half for y in curve]
    
    
    def cie_contrast(self, r, g = ..., b = ...):
        '''
        Apply contrast correction on the colour curves using CIE xyY
        
        In this context, contrast is a measure of difference between the whitepoint and blackpoint,
        if the difference is 0 than they are both grey
        
        @param  r:float?      The contrast parameter for the red curve
        @param  g:float|...?  The contrast parameter for the green curve, defaults to `r` if `...`
        @param  b:float|...?  The contrast parameter for the blue curve, defaults to `g` if `...`
        '''
        # Handle overloading
        if g is ...:  g = r
        if b is ...:  b = g
        # Check if we can reduce the overhead, we can if the adjustments are identical
        same = r == g == b
        # Check we need to do any adjustment
        if (not same) or (not r == 1.0):
            if same:
                if r is None:
                    return
                # Manipulate all curves in one step if their adjustments are identical
                for i in range(i_size):
                    # Convert to CIE xyY
                    (x, y, Y) = srgb_to_ciexyy(self.red[i]   / self.maximum,
                                               self.green[i] / self.maximum,
                                               self.blue[i]  / self.maximum)
                    # Manipulate illumination and convert back to sRGB
                    (r_, g_, b_) = ciexyy_to_srgb(x, y, (Y - 0.5) * r + 0.5)
                    if r:  self.red[i]   = r_ * self.maximum
                    if g:  self.green[i] = g_ * self.maximum
                    if b:  self.blue[i]  = b_ * self.maximum
            else:
                # Manipulate all curves individually if their adjustments are not identical
                for i in range(i_size):
                    # Convert to CIE xyY
                    (x, y, Y) = srgb_to_ciexyy(self.red[i]   / self.maximum,
                                               self.green[i] / self.maximum,
                                               self.blue[i]  / self.maximum)
                    # Manipulate illumination and convert back to sRGB
                    if r:  self.red[i]   = ciexyy_to_srgb(x, y, (Y - 0.5) * r + 0.5)[0] * self.maximum
                    if g:  self.green[i] = ciexyy_to_srgb(x, y, (Y - 0.5) * g + 0.5)[1] * self.maximum
                    if b:  self.blue[i]  = ciexyy_to_srgb(x, y, (Y - 0.5) * b + 0.5)[2] * self.maximum
    
    
    def rgb_brightness(self, r, g = ..., b = ...):
        '''
        Apply brightness correction on the colour curves using sRGB
        
        In this context, brightness is a measure of the whiteness of the whitepoint
        
        @param  r:float?      The brightness parameter for the red curve
        @param  g:float|...?  The brightness parameter for the green curve, defaults to `r` if `...`
        @param  b:float|...?  The brightness parameter for the blue curve, defaults to `g` if `...`
        '''
        for (curve, level) in curves(r, g, b):
            if not level == 1.0:
                curve[:] = [y * level for y in curve]
    
    
    def cie_brightness(self, r, g = ..., b = ...):
        '''
        Apply brightness correction on the colour curves using CIE xyY
        
        In this context, brightness is a measure of the whiteness of the whitepoint
        
        @param  r:float?      The brightness parameter for the red curve
        @param  g:float|...?  The brightness parameter for the green curve, defaults to `r` if `...`
        @param  b:float|...?  The brightness parameter for the blue curve, defaults to `g` if `...`
        '''
        # Handle overloading
        if g is ...:  g = r
        if b is ...:  b = g
        # Check if we can reduce the overhead, we can if the adjustments are identical
        same = r == g == b
        # Check we need to do any adjustment
        if (not same) or (not r == 1.0):
            if same:
                if r is None:
                    return
                # Manipulate all curves in one step if their adjustments are identical
                for i in range(i_size):
                    # Convert to CIE xyY
                    (x, y, Y) = srgb_to_ciexyy(self.red[i]   / self.maximum,
                                               self.green[i] / self.maximum,
                                               self.blue[i]  / self.maximum)
                    (r_, g_, b_) = ciexyy_to_srgb(x, y, Y * r)
                    if r:  self.red[i]   = r_ * self.maximum
                    if g:  self.green[i] = g_ * self.maximum
                    if b:  self.blue[i]  = b_ * self.maximum
            else:
                # Manipulate all curves individually if their adjustments are not identical
                for i in range(i_size):
                    # Convert to CIE xyY
                    (x, y, Y) = srgb_to_ciexyy(self.red[i]   / self.maximum,
                                               self.green[i] / self.maximum,
                                               self.blue[i]  / self.maximum)
                    # Manipulate illumination and convert back to sRGB
                    if r:  self.red[i]   = ciexyy_to_srgb(x, y, Y * r)[0] * self.maximum
                    if g:  self.green[i] = ciexyy_to_srgb(x, y, Y * g)[1] * self.maximum
                    if b:  self.blue[i]  = ciexyy_to_srgb(x, y, Y * b)[2] * self.maximum
    
    
    def linearise(self, r = True, g = ..., b = ...):
        '''
        Convert the curves from formatted in standard RGB to linear RGB
        
        @param  r:bool      Whether to convert the red colour curve
        @param  g:bool|...  Whether to convert the green colour curve, defaults to `r` if `...`
        @param  b:bool|...  Whether to convert the blue colour curve, defaults to `g` if `...`
        '''
        # Handle overloading
        if g is ...:  g = r
        if b is ...:  b = g
        # Convert colour space
        if not r and not g and not b:
            return
        for i in range(i_size):
            (r_, g_, b_) = standard_to_linear(self.red[i] / self.maximum,
                                              self.green[i] / self.maximum,
                                              self.blue[i] / self.maximum)
            if r:  self.red[i]   = r_ * self.maximum
            if g:  self.green[i] = g_ * self.maximum
            if b:  self.blue[i]  = b_ * self.maximum
    
    
    def standardise(self, r = True, g = ..., b = ...):
        '''
        Convert the curves from formatted in linear RGB to standard RGB
        
        @param  r:bool      Whether to convert the red colour curve
        @param  g:bool|...  Whether to convert the green colour curve, defaults to `r` if `...`
        @param  b:bool|...  Whether to convert the blue colour curve, defaults to `g` if `...`
        '''
        # Handle overloading
        if g is ...:  g = r
        if b is ...:  b = g
        # Convert colour space
        if not r and not g and not b:
            return
        for i in range(i_size):
            (r_, g_, b_) = linear_to_standard(self.red[i] / self.maximum,
                                              self.green[i] / self.maximum,
                                              self.blue[i] / self.maximum)
            if r:  self.red[i]   = r_ * self.maximum
            if g:  self.green[i] = g_ * self.maximum
            if b:  self.blue[i]  = b_ * self.maximum
    
    
    def gamma(self, r, g = ..., b = ...):
        '''
        Apply gamma correction on the colour curves
        
        @param  r:float?      The gamma parameter for the red colour curve
        @param  g:float|...?  The gamma parameter for the green colour curve, defaults to `r` if `...`
        @param  b:float|...?  The gamma parameter for the blue colour curve, defaults to `g` if `...`
        '''
        for (curve, level) in self.__value(r, g, b):
            if not level == 1.0:
                curve[:] = [(y / self.maximum) ** (1 / level) * self.maximum for y in curve]
    
    
    def negative(self, r = True, g = ..., b = ...):
        '''
        Reverse the colour curves (negative image with gamma preservation)
        
        @param  r:bool      Whether to invert the red colour curve
        @param  g:bool|...  Whether to invert the green colour curve, defaults to `r` if `...`
        @param  b:bool|...  Whether to invert the blue colour curve, defaults to `g` if `...`
        '''
        for curve in self.__bool(r, g, b):
            curve[:] = reversed(curve)
    
    
    def rgb_invert(self, r = True, g = ..., b = ...):
        '''
        Invert the colour curves (negative image with gamma invertion), using sRGB
        
        @param  r:bool      Whether to invert the red colour curve
        @param  g:bool|...  Whether to invert the green colour curve, defaults to `r` if `...`
        @param  b:bool|...  Whether to invert the blue colour curve, defaults to `g` if `...`
        '''
        for curve in self.__bool(r, g, b):
            curve[:] = [self.maximum - y for y in curve]
    
    
    def cie_invert(self, r = True, g = ..., b = ...):
        '''
        Invert the colour curves (negative image with gamma invertion), using CIE xyY
        
        @param  r:bool      Whether to invert the red colour curve
        @param  g:bool|...  Whether to invert the green colour curve, defaults to `r` if `...`
        @param  b:bool|...  Whether to invert the blue colour curve, defaults to `g` if `...`
        '''
        # Handle overloading
        if g is ...:  g = r
        if b is ...:  b = g
        # Manipulate the colour curves if any curve should be manipulated
        if r or g or b:
            for i in range(i_size):
                # Convert to CIE xyY
                (x, y, Y) = srgb_to_ciexyy(self.red[i]   / self.maximum,
                                           self.green[i] / self.maximum,
                                           self.blue[i]  / self.maximum)
                # Invert illumination and convert to back sRGB
                (r_, g_, b_) = ciexyy_to_srgb(x, y, 1 - Y)
                # Apply the new values on the selected channels
                if r:  self.red[i]   = r_ * self.maximum
                if g:  self.green[i] = g_ * self.maximum
                if b:  self.blue[i]  = b_ * self.maximum
    
    
    def sigmoid(self, r, g = ..., b = ...):
        '''
        Apply S-curve correction on the colour curves.
        This is intended for fine tuning LCD monitors,
        4.5 is good value start start testing at.
        You would probably like to use rgb_limits before
        this to adjust the black point as that is the
        only way to adjust the black point on many LCD
        monitors.
        
        @param  r:float?      The sigmoid parameter for the red colour curve
        @param  g:float|...?  The sigmoid parameter for the green colour curve, defaults to `r` if `...`
        @param  b:float|...?  The sigmoid parameter for the blue colour curve, defaults to `g` if `...`
        '''
        for (curve, level) in self.__value(r, g, b):
            for i in range(i_size):
                try:
                    curve[i] = (0.5 - math.log(self.maximum / curve[i] - 1) / level) * self.maximum
                except:
                    # Corner cases:
                    #   curve[i] = 0 → 0                       -- Division by zero
                    #   curve[i] = self.maximum → self.maximum -- Logarithm of zero
                    pass
    
    
    def rgb_limits(self, r_min, r_max, g_min = ..., g_max = ..., b_min = ..., b_max = ...):
        '''
        Changes the black point and the white point, using sRGB
        
        @param  r_min:float      The red component value of the black point
        @param  r_max:float      The red component value of the white point
        @param  g_min:float|...  The green component value of the black point, defaults to `r_min`
        @param  g_max:float|...  The green component value of the white point, defaults to `r_max`
        @param  b_min:float|...  The blue component value of the black point, defaults to `g_min`
        @param  b_max:float|...  The blue component value of the white point, defaults to `g_max`
        '''
        # Handle overloading
        if g_min is ...:  g_min = r_min
        if g_max is ...:  g_max = r_max
        if b_min is ...:  b_min = g_min
        if b_max is ...:  b_max = g_max
        # Manipulate the colour curves
        for (curve, (level_min, level_max)) in self.__values((r_min, r_max), (g_min, g_max), (b_min, b_max)):
            # But not if the adjustments are neutral
            if (level_min != 0) or (level_max != self.maximum):
                curve[:] = [y * (level_max - level_min) + level_min for y in curve]
    
    
    def cie_limits(self, r_min, r_max, g_min = ..., g_max = ..., b_min = ..., b_max = ...):
        '''
        Changes the black point and the white point, using CIE xyY
        
        @param  r_min:float      The red component value of the black point
        @param  r_max:float      The red component value of the white point
        @param  g_min:float|...  The green component value of the black point, defaults to `r_min`
        @param  g_max:float|...  The green component value of the white point, defaults to `r_max`
        @param  b_min:float|...  The blue component value of the black point, defaults to `g_min`
        @param  b_max:float|...  The blue component value of the white point, defaults to `g_max`
        '''
        # Handle overloading
        if g_min is ...:  g_min = r_min
        if g_max is ...:  g_max = r_max
        if b_min is ...:  b_min = g_min
        if b_max is ...:  b_max = g_max
        # Check if we can reduce the overhead, we can if the adjustments are identical
        same = (r_min == g_min == b_min) and (r_max == g_max == b_max)
        # Check we need to do any adjustment
        if (not same) or (not r_min == 0) or (not r_max == self.maximum):
            if same:
                # Manipulate all curves in one step if their adjustments are identical
                for i in range(i_size):
                    # Convert to CIE xyY
                    (x, y, Y) = srgb_to_ciexyy(self.red[i]   / self.maximum,
                                               self.green[i] / self.maximum,
                                               self.blue[i]  / self.maximum)
                    # Manipulate illumination
                    Y = Y * (r_max - r_min) + r_min
                    # Convert back to sRGB
                    (r_, g_, b_) = ciexyy_to_srgb(x, y, Y)
                    self.red[i]   = r_ * self.maximum
                    self.green[i] = g_ * self.maximum
                    self.blue[i]  = b_ * self.maximum
            else:
                # Manipulate all curves individually if their adjustments are not identical
                for i in range(i_size):
                    # Convert to CIE xyY
                    (x, y, Y) = srgb_to_ciexyy(self.red[i]   / self.maximum,
                                               self.green[i] / self.maximum,
                                               self.blue[i]  / self.maximum)
                    # Manipulate illumination and convert back to sRGB
                    self.red[i]   = ciexyy_to_srgb(x, y, Y * (r_max - r_min) + r_min)[0] * self.maximum
                    self.green[i] = ciexyy_to_srgb(x, y, Y * (g_max - g_min) + g_min)[1] * self.maximum
                    self.blue[i]  = ciexyy_to_srgb(x, y, Y * (b_max - b_min) + b_min)[2] * self.maximum
    
    
    def manipulate(self, r, g = ..., b = ...):
        '''
        Manipulate the colour curves using a (lambda) function
        
        @param  r:(float)?→float      Function to manipulate the red colour curve
        @param  g:(float)?→float|...  Function to manipulate the green colour curve, defaults to `r` if `...`
        @param  b:(float)?→float|...  Function to manipulate the blue colour curve, defaults to `g` if `...`
        
        `None` means that nothing is done for that subpixel
        
        The lambda functions thats a colour value and maps it to a new colour value.
        For example, if the red value 0.5 is already mapped to 0.25, then if the function
        maps 0.25 to 0.5, the red value 0.5 will revert back to being mapped to 0.5.
        '''
        for (curve, f) in self.__values(r, g, b):
            curve[:] = [f(y) for y in curve]
    
    
    def cie_manipulate(self, r, g = ..., b = ...):
        '''
        Manipulate the colour curves using a (lambda) function on the CIE xyY colour space
        
        @param  r:(float)?→float      Function to manipulate the red colour curve
        @param  g:(float)?→float|...  Function to manipulate the green colour curve, defaults to `r` if `...`
        @param  b:(float)?→float|...  Function to manipulate the blue colour curve, defaults to `g` if `...`
        
        `None` means that nothing is done for that subpixel
        
        The lambda functions thats a colour value and maps it to a new illumination value.
        For example, if the value 0.5 is already mapped to 0.25, then if the function
        maps 0.25 to 0.5, the value 0.5 will revert back to being mapped to 0.5.
        '''
        # Handle overloading
        if g is ...:  g = r
        if b is ...:  b = g
        # Check if we can reduce the overhead, we can if the adjustments are identical
        same = (r is g) and (g is b)
        if same:
            if r is None:
                return
            # Manipulate all curves in one step if their adjustments are identical
            for i in range(i_size):
                # Convert to CIE xyY
                (x, y, Y) = srgb_to_ciexyy(self.red[i]   / self.maximum,
                                           self.green[i] / self.maximum,
                                           self.blue[i]  / self.maximum)
                # Manipulate and convert by to sRGB
                (r_, g_, b_) = ciexyy_to_srgb(x, y, r(Y))
                self.red[i]   = r_ * self.maximum
                self.green[i] = g_ * self.maximum
                self.blue[i]  = b_ * self.maximum
        elif any(f is not None for f in (r, g, b)):
            # Manipulate all curves individually if their adjustments are not identical
            # if we are given a function for any curve
            for i in range(i_size):
                # Convert to CIE xyY
                (x, y, Y) = srgb_to_ciexyy(self.red[i]   / self.maximum,
                                           self.green[i] / self.maximum,
                                           self.blue[i]  / self.maximum)
                # Manipulate and convert by to sRGB for selected channels individually
                if r is not None:  self.red[i]   = ciexyy_to_srgb(x, y, r(Y))[0] * self.maximum
                if g is not None:  self.green[i] = ciexyy_to_srgb(x, y, g(Y))[1] * self.maximum
                if b is not None:  self.blue[i]  = ciexyy_to_srgb(x, y, b(Y))[2] * self.maximum
    
    
    def lower_resolution(self, rx_colours = None, ry_colours = None, gx_colours = ..., gy_colours = ..., bx_colours = ..., by_colours = ...):
        '''
        Emulates low colour resolution
        
        @param  rx_colours:int?      The number of colours to emulate on the red encoding axis
        @param  ry_colours:int?      The number of colours to emulate on the red output axis
        @param  gx_colours:int|...?  The number of colours to emulate on the green encoding axis, `rx_colours` if `...`
        @param  gy_colours:int|...?  The number of colours to emulate on the green output axis, `ry_colours` if `...`
        @param  bx_colours:int|...?  The number of colours to emulate on the blue encoding axis, `gx_colours` if `...`
        @param  by_colours:int|...?  The number of colours to emulate on the blue output axis, `gy_colours` if `...`
        
        Where `None` is used the default value will be used, for *x_colours:es that is `i_size`,
        and for *y_colours:es that is `o_size`
        '''
        # Handle overloading
        if gx_colours is ...:  gx_colours = rx_colours
        if gy_colours is ...:  gy_colours = ry_colours
        if bx_colours is ...:  bx_colours = gx_colours
        if by_colours is ...:  by_colours = gy_colours
        # Select default values where default is requested
        if rx_colours is None:  rx_colours = i_size
        if ry_colours is None:  ry_colours = o_size
        if gx_colours is None:  gx_colours = i_size
        if gy_colours is None:  gy_colours = o_size
        if bx_colours is None:  bx_colours = i_size
        if by_colours is None:  by_colours = o_size
        # Combine pair X and Y parameters for each channel
        r_colours = (rx_colours, ry_colours)
        g_colours = (gx_colours, gy_colours)
        b_colours = (bx_colours, by_colours)
        # Manipulate colour curves
        for i_curve, (x_colours, y_colours) in self.__values(r_colours, g_colours, b_colours):
            # But not if adjustment is neutral
            if (x_colours == i_size) and (y_colours == o_size):
                continue
            o_curve = [0] * i_size
            x_, y_, i_ = x_colours - 1, y_colours - 1, i_size - 1
            for i in range(i_size):
                # Scale encoding
                x = int(i * x_colours / i_size)
                x = int(x * i_ / x_)
                # Scale output
                y = int(i_curve[x] / self.maximum * y_ + 0.5)
                o_curve[i] = y / y_ * self.maximum
            i_curve[:] = o_curve
    
    
    def start_over(self, r = True, g = ..., b = ...):
        '''
        Reverts the curves to identity mappings
        
        @param  r:bool      Whether to reset the red colour curve
        @param  g:bool|...  Whether to reset the green colour curve, defaults to `r` if `...`
        @param  b:bool|...  Whether to reset the blue colour curve, defaults to `g` if `...`
        '''
        if self.depth > 0:
            def make_ramp(size):
                return [int(x * self.maximum / (size - 1) + 0.5) for x in range(size)]
        else:
            def make_ramp(size):
                return [x / (size - 1) for x in range(size)]
        for curve in self.__bool(r, g, b):
            curve[:] = make_ramp(len(curve))
    
    
    def clip_below(self, r = True, g = ..., b = ...):
        '''
        Clip all values below the actual minimum
        
        @param  r:bool      Whether to clip the red colour curve
        @param  g:bool|...  Whether to clip the green colour curve, defaults to `r` if `...`
        @param  b:bool|...  Whether to clip the blue colour curve, defaults to `g` if `...`
        '''
        for curve in self.__bool(r, g, b):
            curve[:] = [max(0, y) for y in curve]
    
    
    def clip_above(self, r = True, g = ..., b = ...):
        '''
        Clip all values above the actual maximum
        
        @param  r:bool      Whether to clip the red colour curve
        @param  g:bool|...  Whether to clip the green colour curve, defaults to `r` if `...`
        @param  b:bool|...  Whether to clip the blue colour curve, defaults to `g` if `...`
        '''
        for curve in self.__bool(r, g, b):
            curve[:] = [min(y, self.maximum) for y in curve]
    
    
    def clip(self, r = True, g = ..., b = ...):
        '''
        Clip all values below the actual minimum and above the actual maximum
        
        @param  r:bool      Whether to clip the red colour curve
        @param  g:bool|...  Whether to clip the green colour curve, defaults to `r` if `...`
        @param  b:bool|...  Whether to clip the blue colour curve, defaults to `g` if `...`
        '''
        for curve in self.__bool(r, g, b):
            curve[:] = [min(max(0, y), self.maximum) for y in curve]


class LibgammaCRTC(CRTC):
    '''
    A CRTC using the libgamma backend
    '''
    def __init__(self, screen, crtc):
        '''
        Constructor
        
        The user should not use this, but use `get_outputs` instead
        
        @param  screen:LibgammaScreen  The screen of the CRTC, using the libgamma backend
        @param  crtc:int               The index of the CRTC
        '''
        import libgamma
        CRTC.__init__(self)
        self.crtc = libgamma.CRTC(screen.screen, crtc)
        self.screen = screen
        if screen.display.caps.crtc_restore:
            self.restore = self.crtc.restore
        else:
            self.restore = None
        info = self.crtc.information(~0)[0]
        connector_types = {
            libgamma.LIBGAMMA_CONNECTOR_TYPE_9PinDIN     : '9PinDIN',
            libgamma.LIBGAMMA_CONNECTOR_TYPE_Component   : 'Component',
            libgamma.LIBGAMMA_CONNECTOR_TYPE_Composite   : 'Composite',
            libgamma.LIBGAMMA_CONNECTOR_TYPE_DSI         : 'DSI',
            libgamma.LIBGAMMA_CONNECTOR_TYPE_DVI         : 'DVI',
            libgamma.LIBGAMMA_CONNECTOR_TYPE_DVIA        : 'DVIA',
            libgamma.LIBGAMMA_CONNECTOR_TYPE_DVID        : 'DVID',
            libgamma.LIBGAMMA_CONNECTOR_TYPE_DVII        : 'DVII',
            libgamma.LIBGAMMA_CONNECTOR_TYPE_DisplayPort : 'DisplayPort',
            libgamma.LIBGAMMA_CONNECTOR_TYPE_HDMI        : 'HDMI',
            libgamma.LIBGAMMA_CONNECTOR_TYPE_HDMIA       : 'HDMIA',
            libgamma.LIBGAMMA_CONNECTOR_TYPE_HDMIB       : 'HDMIB',
            libgamma.LIBGAMMA_CONNECTOR_TYPE_LFP         : 'LFP',
            libgamma.LIBGAMMA_CONNECTOR_TYPE_LVDS        : 'LVDS',
            libgamma.LIBGAMMA_CONNECTOR_TYPE_SVIDEO      : 'SVIDEO',
            libgamma.LIBGAMMA_CONNECTOR_TYPE_TV          : 'TV',
            libgamma.LIBGAMMA_CONNECTOR_TYPE_VGA         : 'VGA',
            libgamma.LIBGAMMA_CONNECTOR_TYPE_VIRTUAL     : 'VIRTUAL',
            libgamma.LIBGAMMA_CONNECTOR_TYPE_eDP         : 'eDP'
        }
        subpixel_orders = {
            libgamma.LIBGAMMA_SUBPIXEL_ORDER_HORIZONTAL_BGR : 'BGR',
            libgamma.LIBGAMMA_SUBPIXEL_ORDER_HORIZONTAL_RGB : 'RGB',
            libgamma.LIBGAMMA_SUBPIXEL_ORDER_NONE           : 'None',
            libgamma.LIBGAMMA_SUBPIXEL_ORDER_VERTICAL_BGR   : 'vBGR',
            libgamma.LIBGAMMA_SUBPIXEL_ORDER_VERTICAL_RGB   : 'vRGB'
        }
        self.edid = None if info.edid_error else libgamma.behex_edid_uppercase(info.edid)
        self.width_mm = None if info.width_mm_error else info.width_mm
        self.height_mm = None if info.height_mm_error else info.height_mm
        self.red_gamma_size = None if info.gamma_size_error else info.red_gamma_size
        self.green_gamma_size = None if info.gamma_size_error else info.green_gamma_size
        self.blue_gamma_size = None if info.gamma_size_error else info.blue_gamma_size
        self.gamma_depth = None if info.gamma_depth_error else info.gamma_depth
        self.gamma_support = None if info.gamma_support_error else info.gamma_support
        self.subpixel_order = None if info.subpixel_order_error else info.subpixel_order
        if self.subpixel_order in subpixel_orders:
            self.subpixel_order = subpixel_orders[self.subpixel_order]
        self.active = None if info.active_error else info.active
        self.connector_name = None if info.connector_name_error else info.connector_name
        self.connector_type = None if info.connector_type_error else info.connector_type
        if self.connector_type in connector_types:
            self.connector_type = connector_types[self.connector_type]
        if not info.gamma_size_error and not info.gamma_depth_error:
            self.ramps = libgamma.GammaRamps(self.red_gamma_size, self.green_gamma_size,
                                             self.blue_gamma_size, depth = self.gamma_depth)
    
    
    @property
    def backend(self):
        '''
        The backend which is used to access the CLUT:s, is either the
        name of a library or the name of a display server or protocol
        
        @return  :str  The backend which is used to access the CLUT:s
        '''
        return 'libgamma'
    
    
    def get_gamma(self, low_priority = None, high_priority = None, coalesce = True):
        '''
        Get the gamma ramps on the CRTC or the table of applied adjustments
        
        @param  low_priority:int?   Do not return adjustments with lower priority than
                                    this value, `None` means that there is not lower bound.
                                    Must be `None` if cooperative gamma is not supported.
        @param  high_priority:int?  Do not return adjustments with higher priority than
                                    this value, `None` means that there is not upper bound.
                                    Must be `None` if cooperative gamma is not supported.
        @param  coalesce:bool       If `False` return the adjustment table, if `True`
                                    return the resulting ramps of all adjustments with a
                                    priority within [`low_priority`, `high_priority`].
                                    Must be `True` if cooperative gamma is not supported.
        @return  :Ramps|list<(class:str, priority:int, ramps:Ramps)>
                                    The resulting ramps (if `coalesce` is `True`, or the
                                    ramps if cooperative gamma is not supported) or
                                    a list, sorted by priority, of the adjustments (if
                                    `coalesce` is `False`), where each element is a tuple
                                    with the adjustment's identifier, priority, and ramps.
        '''
        if low_priority is not None or high_priority is not None or not coalesce:
            raise Exception('Cooperative gamma is not supported')
        self.crtc.get_gamma(self.ramps)
        return Ramps.copy(self.ramps)
    
    
    def set_gamma(self, ramps, priority = None, rule = None, lifespan = 1):
        '''
        Set the gamma ramps on the CRTC
        
        @param   ramps:Ramps    The gamma ramps
        @param   priority:int?  The priority of the adjustment, `None` for the default.
                                Must be `None` (default) if cooperative gamma is not supported.
        @param   rule:str?      The rule of the adjustment, `None` for the default.
                                The rule is the last part of the adjustment's identifier,
                                if this is unique within the program, it should be universally
                                unique unless another program is intentionally make it not so.
                                Must be `None` (default) if cooperative gamma is not supported.
        @param   lifespan:int   The lifespan of the algorithm: `Lifespan.UNTIL_DEATH`,
                                `Lifespan.UNTIL_REMOVAL` (default), or `Lifespan.REMOVE`
        @return                 The ramps which the adjustments are written to, this will
                                either be `ramps` or `self.ramps`
        '''
        import libgamma
        if priority is not None or rule is not None or lifespan != 1:
            raise Exception('Cooperative gamma is not supported')
        if ramps is self.ramps:
            self.crtc.set_gamma(ramps)
            return ramps
        match = ramps.depth == self.gamma_depth
        match = match and len(ramps.red) == self.red_gamma_size
        match = match and len(ramps.green) == self.green_gamma_size
        match = match and len(ramps.blue) == self.blue_gamma_size
        if not match:
            ramps = Ramps.copy(ramps, self.gamma_depth,
                               (self.red_gamma_size, self.green_gamma_size, self.blue_gamma_size))
        if isinstance(ramps, libgamma.GammaRamps):
            self.crtc.set_gamma(ramps)
            return
        for i in range(len(ramps.red)):
            self.ramps.red[i] = ramps.red[i]
        for i in range(len(ramps.green)):
            self.ramps.green[i] = ramps.green[i]
        for i in range(len(ramps.blue)):
            self.ramps.blue[i] = ramps.blue[i]
        self.crtc.set_gamma(self.ramps)
        return self.ramps


class LibgammaScreen(Screen):
    '''
    A screen (or graphics card) using the libgamma backend
    '''
    def __init__(self, display, screen, crtcs = None):
        '''
        Constructor
        
        The user should not use this, but use `get_outputs` instead
        
        @param  display:LibgammaDisplay  The display of the screen, using the libgamma backend
        @param  screen:int               The index of the screen
        @param  crtcs:set<int|str>?      List of CRTC:s to include, `None` for all
        '''
        import libgamma
        self.screen = libgamma.Partition(display.display, screen)
        self.display = display
        if display.caps.partition_restore:
            self.restore = self.screen.restore
        elif display.caps.crtc_restore:
            self.restore = self.__restore_all_crtcs
        else:
            self.restore = None
        self.crtcs = []
        if crtcs is not None:
            crtcs = list(crtcs)
        for i in range(self.screen.crtcs_available):
            crtc = LibgammaCRTC(self, i)
            if (crtcs is None) or (i in crtcs) or (crtc.connector_name in crtcs):
                self.crtcs.append(crtc)
            elif isinstance(crtc.edid, str) and (crtc.edid.upper() in crtcs):
                self.crtcs.append(crtc)
            else:
                del crtc

    
    @property
    def backend(self):
        '''
        The backend which is used to access the CLUT:s, is either the
        name of a library or the name of a display server or protocol
        
        @return  :str  The backend which is used to access the CLUT:s
        '''
        return 'libgamma'
    
    
    def __restore_all_crtcs(self):
        '''
        Restore the CLUT:s to the (configured) system defaults, for each CRTC
        '''
        for crtc in self.crtcs:
            crtc.restore()


class LibgammaDisplay(Display):
    '''
    A display using the libgamma backend
    '''
    def __init__(self, method = None, display = None, screens = None, crtcs = None):
        '''
        Constructor
        
        The user should not use this, but use `get_outputs` instead
        
        @param  method:str?              The adjustment method, `None` for the best available
        @param  display:str?             The display, `None` to read the environment, or use
                                         the only display if the adjustment method only supports
                                         one display (e.g. like on Windows)
        @param  screens:set<int>?        Lists of screens to include, `None` for all
        @param  crtcs:set<int|str>|dict<int,set<int|str>>?
                                         List of CRTC:s to include, `None` for all, elements can
                                         either be indices, connector name, or EDID:s; or a
                                         dictionary mapping for screen indices to such lists
        '''
        import libgamma
        self.cooperative = False
        if method is None:
            method = get_adjustment_methods()[0]
        self.display = libgamma.Site(method, display)
        self.caps = libgamma.method_capabilities(method)
        if self.caps.site_restore:
            self.restore = self.display.restore
        elif self.caps.partition_restore or self.caps.crtc_restore:
            self.restore = self.__restore_all_partitions
        else:
            self.restore = None
        if screens is None:
            screens = range(self.display.partitions_available)
        self.screens = []
        self.crtcs = []
        for screen in screens:
            cs = crtcs
            if isinstance(cs, dict):
                cs = cs[screen] if screen in cs else []
            screen = LibgammaScreen(self, screen, cs)
            self.screens.append(screen)
            self.crtcs.extend(screen.crtcs)
    
    
    @property
    def backend(self):
        '''
        The backend which is used to access the CLUT:s, is either the
        name of a library or the name of a display server or protocol
        
        @return  :str  The backend which is used to access the CLUT:s
        '''
        return 'libgamma'
    
    
    @property
    def lowest_priority(self):
        '''
        Return the lowest filter priority accepted by the display server,
        or other backend implementing cooperative gamma, that is, the
        priority that guarantees that no other filter, that is not also
        using this priority, is applied after a filter
        
        @return  :int?  The lowest accepted filter priority (applied last),
                        `None` if cooperative gamma is not supported
        '''
        return None
    
    
    @property
    def highest_priority(self):
        '''
        Return the highest filter priority accepted by the display server,
        or other backend implementing cooperative gamma, that is, the
        priority that guarantees that no other filter, that is not also
        using this priority, is applied before a filter
        
        @return  :int?  The highest accepted filter priority (applied first),
                        `None` if cooperative gamma is not supported
        '''
        return None
    
    
    def __restore_all_partitions(self):
        '''
        Restore the CLUT:s to the (configured) system defaults, for each screen
        '''
        for screen in self.screens:
            screen.restore()


def get_adjustment_methods(libgamma_level = 0):
    '''
    Returns a list of available adjustment methods
    
    @param   libgamma_level:int  Which libgamma adjustment methods to include:
                                 -1: None
                                 0: Methods that the environment suggests will work, excluding fake.
                                 1: Methods that the environment suggests will work, including fake.
                                 2: All real non-fake methods.
                                 3: All real methods.
                                 4: All methods.
    @return  :list<str>          Adjustment method in order of preference
    '''
    ret = []
    if libgamma_level >= 0:
        try:
            import libgamma
            lgamma_meths = libgamma.list_methods(libgamma_level)
            lgamma_map = {
                libgamma.LIBGAMMA_METHOD_DUMMY                : 'dummy',
                libgamma.LIBGAMMA_METHOD_X_RANDR              : 'randr',
                libgamma.LIBGAMMA_METHOD_X_VIDMODE            : 'vidmode',
                libgamma.LIBGAMMA_METHOD_LINUX_DRM            : 'drm',
                libgamma.LIBGAMMA_METHOD_W32_GDI              : 'w32gdi',
                libgamma.LIBGAMMA_METHOD_QUARTZ_CORE_GRAPHICS : 'quartz'
            }
            ret += [lgamma_map[m] if m in lgamma_map else m for m in lgamma_meths]
        except:
            pass
    return ret


def get_outputs(method = None, display = None, screens = None, crtcs = None):
    '''
    Get access to CRTC for editing the their gamma ramps
    
    @param   method:str?              The adjustment method, `None` for the best available.
                                      "dummy" for libgamma with dummy method,
                                      "randr" for libgamma with X's RAndR protocol,
                                      "vidmode" for libgamma with X's VidMode protocol,
                                      "drm" for libgamma with Direct Rendering Manager,
                                      "w32gdi" for libgamma with Window's GDI,
                                      "quartz" for libgamma with Quartz's (MacOS's) Core Graphics
    @param   display:str?             The display, `None` to read the environment, or use
                                      the only display if the adjustment method only supports
                                      one display (e.g. like on Windows)
    @param   screens:set<int>?        Lists of screens to include, `None` for all
    @param   crtcs:set<int|str>|dict<int,set<int|str>>?
                                      List of CRTC:s to include, `None` for all, elements can
                                      either be indices, connector name, or EDID:s; or a
                                      dictionary mapping for screen indices to such lists
    @return  :Display                 A display
    '''
    if isinstance(method, str):
        #try:
            import libgamma
            lgamma_meths = {
                'dummy'   : libgamma.LIBGAMMA_METHOD_DUMMY,
                'randr'   : libgamma.LIBGAMMA_METHOD_X_RANDR,
                'vidmode' : libgamma.LIBGAMMA_METHOD_X_VIDMODE,
                'drm'     : libgamma.LIBGAMMA_METHOD_LINUX_DRM,
                'w32gdi'  : libgamma.LIBGAMMA_METHOD_W32_GDI,
                'quartz'  : libgamma.LIBGAMMA_METHOD_QUARTZ_CORE_GRAPHICS
            }
            return LibgammaDisplay(lgamma_meths[method], display, screens, crtcs)
        #except:
        #    pass
        #raise Exception("Adjustment method %s is not available" % method)
    else:
        return LibgammaDisplay(method, display, screen, crtc)
