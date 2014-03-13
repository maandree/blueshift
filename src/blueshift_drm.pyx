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
from libc.stdlib cimport malloc, free


cdef extern void blueshift_drm_close()
cdef extern int blueshift_drm_card_count()
cdef extern int blueshift_drm_open_card(int card_index)
cdef extern void blueshift_drm_update_card(int connection)
cdef extern void blueshift_drm_close_card(int connection)
cdef extern int blueshift_drm_crtc_count(int connection)
cdef extern int blueshift_drm_connector_count(int connection)
cdef extern int blueshift_drm_gamma_size(int connection, int crtc_index)
cdef extern int blueshift_drm_get_gamma_ramps(int connection, int crtc_index, int gamma_size,
                                              unsigned short int* red,
                                              unsigned short int* green,
                                              unsigned short int* blue)
cdef extern int blueshift_drm_set_gamma_ramps(int connection, int crtc_index, int gamma_size,
                                              unsigned short int* red,
                                              unsigned short int* green,
                                              unsigned short int* blue)
cdef extern void blueshift_drm_open_connector(int connection, int connector_index)
cdef extern void blueshift_drm_close_connector(int connection, int connector_index)
cdef extern int blueshift_drm_get_width(int connection, int connector_index)
cdef extern int blueshift_drm_get_height(int connection, int connector_index)
cdef extern int blueshift_drm_is_connected(int connection, int connector_index)
cdef extern int blueshift_drm_get_crtc(int connection, int connector_index)
cdef extern int blueshift_drm_get_connector_type_index(int connection, int connector_index)
cdef extern const char* blueshift_drm_get_connector_type_name(int connection, int connector_index)
cdef extern long int blueshift_drm_get_edid(int connection, int connector_index, char* edid,
                                            long int size, int hexadecimal)


def drm_close():
    '''
    Free all resources, but you need to close all connections first
    '''
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


def drm_get_gamma_ramps(int connection, int crtc_index, int gamma_size):
    '''
    Get the gamma ramps of the of a monitor
    
    @param   connection                                 The identifier for the connection to the card
    @param   crtc_index                                 The index of the CRTC to read from
    @param   gamma_size                                 The size a gamma ramp
    @return  :(r:list<int>, g:list<int>, b:list<int>)?  The current red, green and blue colour curves
    '''
    cdef unsigned short int* r
    cdef unsigned short int* g
    cdef unsigned short int* b
    r = <unsigned short int*>malloc(gamma_size * 2)
    g = <unsigned short int*>malloc(gamma_size * 2)
    b = <unsigned short int*>malloc(gamma_size * 2)
    if (r is NULL) or (g is NULL) or (b is NULL):
        raise MemoryError()
    rc = blueshift_drm_get_gamma_ramps(connection, crtc_index, gamma_size, r, g, b)
    if rc == 0:
        rc_r, rc_g, rc_b = [], [], []
        for i in range(gamma_size):
            rc_r.append(r[i])
            rc_g.append(g[i])
            rc_b.append(b[i])
        free(r)
        free(g)
        free(b)
        return (rc_r, rc_g, rc_b)
    else:
        free(r)
        free(g)
        free(b)
        return None


def drm_set_gamma_ramps(int connection, int crtc_index, int gamma_size, r_curve, g_curve, b_curve):
    '''
    Set the gamma ramps of the of a monitor
    
    @param   connection                        The identifier for the connection to the card
    @param   crtc_index                        The index of the CRTC to read from
    @param   gamma_size                        The size a gamma ramp
    @param   r_curve:list<unsigned short int>  The red gamma ramp
    @param   g_curve:list<unsigned short int>  The green gamma ramp
    @param   b_curve:list<unsigned short int>  The blue gamma ramp
    @return  :int                              Zero on success
    '''
    cdef unsigned short int* r
    cdef unsigned short int* g
    cdef unsigned short int* b
    r = <unsigned short int*>malloc(gamma_size * 2)
    g = <unsigned short int*>malloc(gamma_size * 2)
    b = <unsigned short int*>malloc(gamma_size * 2)
    if (r is NULL) or (g is NULL) or (b is NULL):
        raise MemoryError()
    for i in range(gamma_size):
        r[i] = r_curve[i] & 0xFFFF
        g[i] = g_curve[i] & 0xFFFF
        b[i] = b_curve[i] & 0xFFFF
    rc = blueshift_drm_set_gamma_ramps(connection, crtc_index, gamma_size, r, g, b)
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
    cdef long int size
    cdef long int got
    cdef char* edid
    cdef bytes rc
    
    size = 256
    edid = <char*>malloc(size + 1)
    got = blueshift_drm_get_edid(connection, connector_index, edid, size, 1)
    
    if got == 0:
        free(edid)
        return None
    
    if got * 2 > size:
        size = got
        blueshift_drm_get_edid(connection, connector_index, edid, size, 1)
    
    edid[got * 2] = 0
    rc = edid
    free(edid)
    return rc.decode('utf-8', 'replace')

