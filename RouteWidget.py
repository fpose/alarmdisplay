# -*- coding: utf-8 -*-

from PyQt5.QtWidgets import QFrame
from PyQt5.QtGui import QPainter

import Map

class RouteWidget(QFrame):

    def __init__(self, parent, config):
        super(RouteWidget, self).__init__(parent)

        self.config = config
        self.pixmap = None

        # Destination
        self.dest_lat_deg = None
        self.dest_lon_deg = None

    def setTarget(self, lat_deg, lon_deg, route):
        self.dest_lat_deg = lat_deg
        self.dest_lon_deg = lon_deg
        self.route = route
        self.updateMap()

    def updateMap(self):
        if not self.dest_lat_deg or not self.dest_lon_deg:
            self.pixmap = None
        else:
            self.pixmap = Map.getRoutePixmap( \
                    self.dest_lat_deg, self.dest_lon_deg,
                    self.contentsRect().width(), self.contentsRect().height(),
                    self.route, self.config)
        self.update()

    def resizeEvent(self, event):
        self.updateMap()

    def paintEvent(self, event):
        painter = QPainter(self)
        if self.pixmap:
            painter.drawPixmap(0, 0, self.pixmap)
