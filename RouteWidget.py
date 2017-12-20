# -*- coding: utf-8 -*-

from PyQt5.QtWidgets import QFrame
from PyQt5.QtGui import QPainter

import Map

class RouteWidget(QFrame):

    def __init__(self, parent):
        super(RouteWidget, self).__init__(parent)

        self.pixmap = None

        # Einfahrt Depot
        self.home_lat_deg = 51.76059
        self.home_lon_deg = 6.09806

        # Destination
        self.dest_lat_deg = 0.0
        self.dest_lon_deg = 0.0

    def setTarget(self, lat_deg, lon_deg):
        self.dest_lat_deg = lat_deg
        self.dest_lon_deg = lon_deg
        self.updateMap()

    def updateMap(self):
        if not self.home_lat_deg or not self.home_lon_deg or \
            not self.dest_lat_deg or not self. dest_lon_deg:
            self.pixmap = None
        else:
            self.pixmap = Map.getRoutePixmap(self.home_lat_deg,
                    self.home_lon_deg, self.dest_lat_deg, self.dest_lon_deg,
                    self.contentsRect().width(), self.contentsRect().height())
        self.update()

    def resizeEvent(self, event):
        self.updateMap()

    def paintEvent(self, event):
        painter = QPainter(self)
        if self.pixmap:
            painter.drawPixmap(0, 0, self.pixmap)
