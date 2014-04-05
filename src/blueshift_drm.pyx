# -*- python -*-

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

cimport cython
from libc.stdlib cimport malloc, free, realloc
from libc.stdint cimport *


cdef extern void blueshift_drm_close()
'''
Free all resources, but you need to close all connections first
'''

cdef extern int blueshift_drm_card_count()
'''
Get the number of cards present on the system

@return  The number of cards present on the system
'''

cdef extern int blueshift_drm_open_card(int card_index)
'''
Open connection to a graphics card

@param   card_index  The index of the graphics card
@return              -1 on failure, otherwise an identifier for the connection to the card
'''

cdef extern void blueshift_drm_update_card(int connection)
'''
Update the resource, required after `blueshift_drm_open_card`

@param  connection  The identifier for the connection to the card
'''

cdef extern void blueshift_drm_close_card(int connection)
'''
Close connection to the graphics card

@param  connection  The identifier for the connection to the card
'''

cdef extern int blueshift_drm_crtc_count(int connection)
'''
Return the number of CRTC:s on the opened card

@param   connection  The identifier for the connection to the card
@return              The number of CRTC:s on the opened card
'''

cdef extern int blueshift_drm_connector_count(int connection)
'''
Return the number of connectors on the opened card

@param   connection  The identifier for the connection to the card
@return              The number of connectors on the opened card
'''

cdef extern int blueshift_drm_gamma_size(int connection, int crtc_index)
'''
Return the size of the gamma ramps on a CRTC

@param   connection  The identifier for the connection to the card
@param   crtc_index  The index of the CRTC
@return              The size of the gamma ramps on a CRTC
'''

cdef extern int blueshift_drm_get_gamma_ramps(int connection, int crtc_index, int gamma_size,
                                              uint16_t* red, uint16_t* green, uint16_t* blue)
'''
Get the current gamma ramps of a monitor

@param   connection  The identifier for the connection to the card
@param   crtc_index  The index of the CRTC to read from
@param   gamma_size  The size a gamma ramp
@param   red         Storage location for the red gamma ramp
@param   green       Storage location for the green gamma ramp
@param   blue        Storage location for the blue gamma ramp
@return              Zero on success
'''

cdef extern int blueshift_drm_set_gamma_ramps(int connection, int crtc_index, int gamma_size,
                                              uint16_t* red, uint16_t* green, uint16_t* blue)
'''
Set the gamma ramps of the of a monitor

@param   connection  The identifier for the connection to the card
@param   crtc_index  The index of the CRTC to read from
@param   gamma_size  The size a gamma ramp
@param   red         The red gamma ramp
@param   green       The green gamma ramp
@param   blue        The blue gamma ramp
@return              Zero on success
'''

cdef extern void blueshift_drm_open_connector(int connection, int connector_index)
'''
Acquire information about a connector

@param  connection       The identifier for the connection to the card
@param  connector_index  The index of the connector
'''

cdef extern void blueshift_drm_close_connector(int connection, int connector_index)
'''
Release information about a connector

@param  connection       The identifier for the connection to the card
@param  connector_index  The index of the connector
'''

cdef extern int blueshift_drm_get_width(int connection, int connector_index)
'''
Get the physical width the monitor connected to a connector

@param   connection       The identifier for the connection to the card
@param   connector_index  The index of the connector
@return                   The physical width of the monitor in millimetres, 0 if unknown or not connected
'''

cdef extern int blueshift_drm_get_height(int connection, int connector_index)
'''
Get the physical height the monitor connected to a connector

@param   connection       The identifier for the connection to the card
@param   connector_index  The index of the connector
@return                   The physical height of the monitor in millimetres, 0 if unknown or not connected
'''

cdef extern int blueshift_drm_is_connected(int connection, int connector_index)
'''
Get whether a monitor is connected to a connector

@param   connection       The identifier for the connection to the card
@param   connector_index  The index of the connector
@return                   1 if there is a connection, 0 otherwise, -1 if unknown
'''

cdef extern int blueshift_drm_get_crtc(int connection, int connector_index)
'''
Get the index of the CRTC of the monitor connected to a connector

@param   connection       The identifier for the connection to the card
@param   connector_index  The index of the connector
@return                   The index of the CRTC
'''

cdef extern int blueshift_drm_get_connector_type_index(int connection, int connector_index)
'''
Get the index of the type of a connector

@param   connection       The identifier for the connection to the card
@param   connector_index  The index of the connector
@return                   The connector type by index, 0 for unknown
'''

cdef extern const char* blueshift_drm_get_connector_type_name(int connection, int connector_index)
'''
Get the name of the type of a connector

@param   connection       The identifier for the connection to the card
@param   connector_index  The index of the connector
@return                   The connector type by name, "Unknown" if not identifiable,
                          "Unrecognised" if Blueshift does not recognise it.
'''

cdef extern long int blueshift_drm_get_edid(int connection, int connector_index, char* edid,
                                            long int size, int hexadecimal)
'''
Get the extended display identification data for the monitor connected to a connector

@param   connection       The identifier for the connection to the card
@param   connector_index  The index of the connector
@param   edid             Storage location for the EDID, it should be 128 bytes, 256 bytes + zero termination if hex
@param   size             The size allocated to `edid` excluding your zero termination
@param   hexadecimal      Whether to convert to hexadecimal representation, this is preferable
@return                   The length of the found value, 0 if none, as if hex is false
'''



cdef uint16_t* r_shared
'''
Non-threadsafe storage for the red colour curve to be used in native code
'''

cdef uint16_t* g_shared
'''
Non-threadsafe storage for the green colour curve to be used in native code
'''

cdef uint16_t* b_shared
'''
Non-threadsafe storage for the blue colour curve to be used in native code
'''

r_shared = NULL
g_shared = NULL
b_shared = NULL



def drm_close():
    '''
    Free all resources, but you need to close all connections first
    '''
    global r_shared, g_shared, b_shared
    # Deallocate colour curve storage
    if r_shared is not NULL:
        free(r_shared)
        r_shared = NULL
    if g_shared is not NULL:
        free(g_shared)
        g_shared = NULL
    if b_shared is not NULL:
        free(b_shared)
        b_shared = NULL
    # Close all native resources
    blueshift_drm_close()


def drm_card_count():
    '''
    Get the number of cards present on the system
    
    @return  :int  The number of cards present on the system
    '''
    return blueshift_drm_card_count()


def drm_open_card(int card_index):
    '''
    Open connection to a graphics card
    
    @param   card_index  The index of the graphics card
    @return  :int        -1 on failure, otherwise an identifier for the connection to the card
    '''
    return blueshift_drm_open_card(card_index)


def drm_update_card(int connection):
    '''
    Update the resource, required after `blueshift_drm_open_card`
    
    @param  connection  The identifier for the connection to the card
    '''
    blueshift_drm_update_card(connection)


def drm_close_card(int connection):
    '''
    Close connection to the graphics card
    
    @param  connection  The identifier for the connection to the card
    '''
    blueshift_drm_close_card(connection)


def drm_crtc_count(int connection):
    '''
    Return the number of CRTC:s on the opened card
    
    @param   connection  The identifier for the connection to the card
    @return  :int        The number of CRTC:s on the opened card
    '''
    return blueshift_drm_crtc_count(connection)


def drm_connector_count(int connection):
    '''
    Return the number of connectors on the opened card
    
    @param   connection  The identifier for the connection to the card
    @return  :int        The number of connectors on the opened card
    '''
    return blueshift_drm_connector_count(connection)


def drm_gamma_size(int connection, int crtc_index):
    '''
    Return the size of the gamma ramps on a CRTC
    
    @param   connection  The identifier for the connection to the card
    @param   crtc_index  The index of the CRTC
    @return  :int        The size of the gamma ramps on a CRTC
    '''
    return blueshift_drm_gamma_size(connection, crtc_index)


def drm_get_gamma_ramps(int connection, int crtc_index, int gamma_size, threadsafe = False):
    '''
    Get the gamma ramps of the of a monitor
    
    @param   connection                                 The identifier for the connection to the card
    @param   crtc_index                                 The index of the CRTC to read from
    @param   gamma_size                                 The size a gamma ramp
    @param   threadsafe:bool                            Whether to decrease memory efficiency and performace so
                                                        multiple threads can use DRM concurrently
    @return  :(r:list<int>, g:list<int>, b:list<int>)?  The current red, green and blue colour curves
    '''
    global r_shared, g_shared, b_shared
    cdef uint16_t* r
    cdef uint16_t* g
    cdef uint16_t* b
    # If not running in thread-safe mode,
    if not threadsafe:
        # allocate the shared storage space for colour curves
        # if not already allocated.
        if r_shared is NULL:
            r_shared = <uint16_t*>malloc(gamma_size * sizeof(uint16_t))
        if g_shared is NULL:
            g_shared = <uint16_t*>malloc(gamma_size * sizeof(uint16_t))
        if b_shared is NULL:
            b_shared = <uint16_t*>malloc(gamma_size * sizeof(uint16_t))
    # If not thread-safe use those, otherwise allocate ad-hoc ones
    r = <uint16_t*>malloc(gamma_size * sizeof(uint16_t)) if threadsafe else r_shared
    g = <uint16_t*>malloc(gamma_size * sizeof(uint16_t)) if threadsafe else g_shared
    b = <uint16_t*>malloc(gamma_size * sizeof(uint16_t)) if threadsafe else b_shared
    # Check for out-of-memory error, both for thread-safe and thread-unsafe
    if (r is NULL) or (g is NULL) or (b is NULL):
        raise MemoryError()
    # Get current curves
    rc = blueshift_drm_get_gamma_ramps(connection, crtc_index, gamma_size, r, g, b)
    if rc == 0:
        # If successful:
        # Move the C native colour curves to Python data structures
        rc_r, rc_g, rc_b = [], [], []
        for i in range(gamma_size):
            rc_r.append(r[i])
            rc_g.append(g[i])
            rc_b.append(b[i])
        # Then, if running in thread-safe mode,
        if threadsafe:
            # deallocate the ad-hoc curve storage.
            free(r)
            free(g)
            free(b)
        return (rc_r, rc_g, rc_b)
    else:
        # On failure,
        if threadsafe:
            # deallocate the ad-hoc curve storage
            # if running in thread-safe mode.
            free(r)
            free(g)
            free(b)
        return None


def drm_set_gamma_ramps(int connection, crtc_indices, int gamma_size, r_curve, g_curve, b_curve, threadsafe = False):
    '''
    Set the gamma ramps of the of a monitor
    
    @param   connection            The identifier for the connection to the card
    @param   crtc_index:list<int>  The index of the CRTC to read from
    @param   gamma_size            The size a gamma ramp
    @param   r_curve:list<int>     The red gamma ramp
    @param   g_curve:list<int>     The green gamma ramp
    @param   b_curve:list<int>     The blue gamma ramp
    @param   threadsafe:bool       Whether to decrease memory efficiency and performace so
                                   multiple threads can use DRM concurrently
    @return  :int                  Zero on success
    '''
    global r_shared, g_shared, b_shared
    cdef uint16_t* r
    cdef uint16_t* g
    cdef uint16_t* b
    # If not running in thread-safe mode,
    if not threadsafe:
        # allocate the shared storage space for colour curves
        # if not already allocated.
        if r_shared is NULL:
            r_shared = <uint16_t*>malloc(gamma_size * sizeof(uint16_t))
        if g_shared is NULL:
            g_shared = <uint16_t*>malloc(gamma_size * sizeof(uint16_t))
        if b_shared is NULL:
            b_shared = <uint16_t*>malloc(gamma_size * sizeof(uint16_t))
    # If not thread-safe use those, otherwise allocate ad-hoc ones
    r = <uint16_t*>malloc(gamma_size * sizeof(uint16_t)) if threadsafe else r_shared
    g = <uint16_t*>malloc(gamma_size * sizeof(uint16_t)) if threadsafe else g_shared
    b = <uint16_t*>malloc(gamma_size * sizeof(uint16_t)) if threadsafe else b_shared
    # Check for out-of-memory error, both for thread-safe and thread-unsafe
    if (r is NULL) or (g is NULL) or (b is NULL):
        raise MemoryError()
    # Convert the Python colour curves to C native format
    for i in range(gamma_size):
        r[i] = r_curve[i] & 0xFFFF
        g[i] = g_curve[i] & 0xFFFF
        b[i] = b_curve[i] & 0xFFFF
    rc = 0
    # For each selected CRTC,
    for crtc_index in crtc_indices:
        # adjust the colour curves.
        rc |= blueshift_drm_set_gamma_ramps(connection, crtc_index, gamma_size, r, g, b)
    if threadsafe:
        # deallocate the ad-hoc curve storage
        # if running in thread-safe mode
        free(r)
        free(g)
        free(b)
    return rc


def drm_open_connector(int connection, int connector_index):
    '''
    Acquire information about a connector
    
    @param  connection       The identifier for the connection to the card
    @param  connector_index  The index of the connector
    '''
    blueshift_drm_open_connector(connection, connector_index)


def drm_close_connector(int connection, int connector_index):
    '''
    Release information about a connector
    
    @param  connection       The identifier for the connection to the card
    @param  connector_index  The index of the connector
    '''
    blueshift_drm_close_connector(connection, connector_index)


def drm_get_width(int connection, int connector_index):
    '''
    Get the physical width the monitor connected to a connector
    
    @param   connection       The identifier for the connection to the card
    @param   connector_index  The index of the connector
    @return  :int             The physical width of the monitor in millimetres, 0 if unknown or not connected
    '''
    return blueshift_drm_get_width(connection, connector_index)


def drm_get_height(int connection, int connector_index):
    '''
    Get the physical height the monitor connected to a connector
    
    @param   connection       The identifier for the connection to the card
    @param   connector_index  The index of the connector
    @return  :int             The physical height of the monitor in millimetres, 0 if unknown or not connected
    '''
    return blueshift_drm_get_height(connection, connector_index)


def drm_is_connected(int connection, int connector_index):
    '''
    Get whether a monitor is connected to a connector
    
    @param   connection       The identifier for the connection to the card
    @param   connector_index  The index of the connector
    @return  :int             1 if there is a connection, 0 otherwise, -1 if unknown
    '''
    return blueshift_drm_is_connected(connection, connector_index)


def drm_get_crtc(int connection, int connector_index):
    '''
    Get the index of the CRTC of the monitor connected to a connector
    
    @param   connection       The identifier for the connection to the card
    @param   connector_index  The index of the connector
    @return  :int             The index of the CRTC
    '''
    return blueshift_drm_get_crtc(connection, connector_index)


def drm_get_connector_type_index(int connection, int connector_index):
    '''
    Get the index of the type of a connector
    
    @param   connection       The identifier for the connection to the card
    @param   connector_index  The index of the connector
    @return  :int             The connector type by index, 0 for unknown
    '''
    return blueshift_drm_get_connector_type_index(connection, connector_index)


def drm_get_connector_type_name(int connection, int connector_index):
    '''
    Get the name of the type of a connector
    
    @param   connection       The identifier for the connection to the card
    @param   connector_index  The index of the connector
    @return  :str             The connector type by name, "Unknown" if not identifiable,
                              "Unrecognised" if Blueshift does not recognise it.
    '''
    return (<bytes>blueshift_drm_get_connector_type_name(connection, connector_index)).decode('utf-8', 'replace')


def drm_get_edid(int connection, int connector_index):
    '''
    Get the extended display identification data for the monitor connected to a connector
    
    @param   connection        The identifier for the connection to the card
    @param   connector_index   The index of the connector
    @return  :str?             The extended display identification data for the monitor
    '''
    global edid_shared
    cdef long int size
    cdef long int got
    cdef char* edid
    cdef bytes rc
    
    # Prototype side of the hexadecimal representation
    # of the EDID, should be exact
    size = 256
    # Allocate storage space for the EDID, with one
    # extra character for NUL-termination
    edid = <char*>malloc((size + 1) * sizeof(char))
    # Check for out-of-memory error
    if edid is NULL:
        raise MemoryError()
    # Fill the storage space for the EDID, with the
    # EDID of the monitor connected to the selected
    # connector, in hexadecimal, representation.
    got = blueshift_drm_get_edid(connection, connector_index, edid, size, 1)
    
    # If the length of the EDID is zero,
    if got == 0:
        # the free the storage space,
        free(edid)
        # and return that it failed.
        return None
    
    # But if we got an non-zero length, it is of the
    # EDID's byte-length, not in hexadecimal representation
    # that is twice as long.
    if got * 2 > size:
        # In if that length is larger than we have anticipated,
        # update to new size (of the hexadecimal representation),
        size = got * 2
        # and reallocate the storage.
        edid = <char*>realloc(edid, (size + 1) * sizeof(char))
        # Check for out-of-memory error
        if edid is NULL:
            raise MemoryError()
        # Get the full EDID.
        got = blueshift_drm_get_edid(connection, connector_index, edid, size, 1)
        # Check that we got the EDID. There is an unlikely
        # race condition where the user can have unplugged
        # the monitor.
        if got == 0:
            # If we did not get an EDID,
            # free the storage for it,
            free(edid)
            # and return that it failed.
            return None
        # If we got a large EDID yet,
        if got * 2 > size:
            # ignore it because it should happen,
            # EDID:s are 128 bytes long and the risk that
            # the use plugged in new monitor that did not
            # have the same EDID format, is super unlikely.
            # She would have to pause the program or used
            # a KVM switch between the two readings.
            # Instead just truncate the EDID to the size
            # that we expected; it is not fatal.
            got = size // 2
    
    # NUL-terminate the EDID,
    edid[got * 2] = 0
    # and convert it to bytes so that we can
    # later convert it to a Python string,
    rc = edid
    # and deallocate the C string.
    free(edid)
    # Convert the EDID to a Sython string
    return rc.decode('utf-8', 'replace')

