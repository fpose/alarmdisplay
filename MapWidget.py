# -*- coding: utf-8 -*-

from PyQt5.QtWidgets import QFrame
from PyQt5.QtGui import QPainter

import Map

class MapWidget(QFrame):

    def __init__(self, parent, config, logger):
        super(MapWidget, self).__init__(parent)

        self.config = config
        self.logger = logger
        self.invalidate()

    def invalidate(self):
        self.lat_deg = None
        self.lon_deg = None
        self.route = []
        self.updateMap()

    def setTarget(self, lat_deg, lon_deg, route):
        self.lat_deg = lat_deg
        self.lon_deg = lon_deg
        self.route = route[0]
        self.updateMap()

    def updateMap(self):
        if not self.lat_deg or not self.lon_deg:
            self.pixmap = None
        else:
            self.pixmap = Map.getTargetPixmap(self.lat_deg, self.lon_deg,
                    self.contentsRect().width(), self.contentsRect().height(),
                    self.route, self.config, self.logger)
        self.update()

    def resizeEvent(self, event):
        self.updateMap()

    def paintEvent(self, event):
        painter = QPainter(self)
        if self.pixmap:
            painter.drawPixmap(0, 0, self.pixmap)
