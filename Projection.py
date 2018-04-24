#-----------------------------------------------------------------------------
#
# Map projection helper functions
#
# Copyright (C) 2018 Florian Pose
#
# This file is part of Alarm Display.
#
# Alarm Display is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Alarm Display is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.
#
# You should have received a copy of the GNU General Public License along with
# Alarm Display. If not, see <http://www.gnu.org/licenses/>.
#
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
