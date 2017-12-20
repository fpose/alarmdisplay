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

        # Engelsstraße 5
        self.dest_lat_deg = 51.75065
        self.dest_lon_deg = 6.11170

    def resizeEvent(self, event):
        self.pixmap = Map.getRoutePixmap(self.home_lat_deg, self.home_lon_deg,
            self.dest_lat_deg, self.dest_lon_deg,
            self.contentsRect().width(), self.contentsRect().height())

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.drawPixmap(0, 0, self.pixmap)
