# -*- coding: utf-8 -*-

import Map

class AlarmReport:

    def __init__(self, config):
        self.config = config

        res = 200 / 25.4 # [px / mm]
        self.map_width = res * 120
        self.map_height = res * 120

    def generate(self, lat_deg, lon_deg, route):
        targetPixmap = Map.getTargetPixmap(lat_deg, lon_deg,
                self.map_width, self.map_height,
                route[0], self.config)
        targetPixmap.save('/tmp/target.png')

        routePixmap = Map.getRoutePixmap(lat_deg, lon_deg,
                self.map_width, self.map_height,
                route[0], self.config)
        routePixmap.save('/tmp/route.png')
