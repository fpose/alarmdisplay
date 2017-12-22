# -*- coding: utf-8 -*-

import math

from PyQt5.QtWidgets import QFrame
from PyQt5.QtGui import QPainter
from PyQt5.QtCore import QRect, Qt

import Map

class RouteWidget(QFrame):

    def __init__(self, parent, config):
        super(RouteWidget, self).__init__(parent)

        self.config = config
        self.pixmap = None

        # Destination
        self.dest_lat_deg = None
        self.dest_lon_deg = None
        self.route = []
        self.distance = None
        self.duration = None

    def setTarget(self, lat_deg, lon_deg, route):
        self.dest_lat_deg = lat_deg
        self.dest_lon_deg = lon_deg
        self.route = route[0]
        self.distance = route[1]
        self.duration = route[2]
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
        rect = QRect(0, 0, self.width(), self.height())
        if self.distance:
            painter.drawText(rect, Qt.AlignLeft | Qt.AlignBottom,
                    '%.1f km' % (self.distance / 1000))
        if self.duration:
            minutes = math.floor(self.duration / 60)
            seconds = self.duration - minutes * 60
            painter.drawText(rect, Qt.AlignRight | Qt.AlignBottom,
                    '%u:%02u min.' % (minutes, seconds))
