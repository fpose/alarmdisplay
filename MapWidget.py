# -*- coding: utf-8 -*-

from PyQt5.QtWidgets import QFrame
from PyQt5.QtGui import QPainter

import Map

class MapWidget(QFrame):

    def __init__(self, parent, zoom):
        super(MapWidget, self).__init__(parent)

        self.pixmap = None
        self.zoom = zoom

        # Einfahrt Depot
        self.lat_deg = 51.76059
        self.lon_deg = 6.09806

        # Jugendherberge
        self.lat_deg = 51.78317
        self.lon_deg = 6.10695

        # Engelsstraße 5
        self.lat_deg = 51.75065
        self.lon_deg = 6.11170

    def resizeEvent(self, event):
        self.pixmap = Map.getTargetPixmap(self.lat_deg, self.lon_deg,
                self.zoom, self.contentsRect().width(),
                self.contentsRect().height())

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.drawPixmap(0, 0, self.pixmap)
