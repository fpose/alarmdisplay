#-----------------------------------------------------------------------------

import math
import pyproj

#-----------------------------------------------------------------------------

class MercatorProjection:

    #-------------------------------------------------------------------------

    def __init__(self, llcrnrlon, llcrnrlat, urcrnrlon, urcrnrlat):

        projparams = {}
        projparams['proj'] = 'merc'
        projparams['units'] = 'm'
        projparams['lat_ts'] = 0.0
        self.radius = 6370997.0
        projparams['R'] = self.radius
        projparams['lon_0'] = 0.5 * (llcrnrlon + urcrnrlon)

        proj = pyproj.Proj(projparams)
        llcrnrx, llcrnry = proj(llcrnrlon, llcrnrlat)

        projparams['x_0'] = -llcrnrx
        projparams['y_0'] = -llcrnry

        self.proj = pyproj.Proj(
            projparams,
            llcrnrlon = llcrnrlon,
            llcrnrlat = llcrnrlat,
            urcrnrlon = urcrnrlon,
            urcrnrlat = urcrnrlat
        )

        self.llcrnrlon = llcrnrlon # used in __call__

    #-------------------------------------------------------------------------

    def __call__(self, lon_deg, lat_deg):
        outx, outy = self.proj(lon_deg, lat_deg)
        outx = self.radius * math.radians(lon_deg - self.llcrnrlon)
        return outx, outy

#-----------------------------------------------------------------------------
