# -*- coding: utf-8 -*-

from PyQt5.QtWidgets import QFrame
from PyQt5.QtGui import QPainter

import Map

class MapWidget(QFrame):

    def __init__(self, parent, zoom):
        super(MapWidget, self).__init__(parent)

        self.pixmap = None
        self.zoom = zoom

        # Engelsstraße 5
        self.lat_deg = 0.0
        self.lon_deg = 0.0

    def setTarget(self, lat_deg, lon_deg):
        self.lat_deg = lat_deg
        self.lon_deg = lon_deg
        self.updateMap()

    def updateMap(self):
        self.pixmap = Map.getTargetPixmap(self.lat_deg, self.lon_deg,
                self.zoom, self.contentsRect().width(),
                self.contentsRect().height())
        self.update()

    def resizeEvent(self, event):
        self.updateMap()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.drawPixmap(0, 0, self.pixmap)
