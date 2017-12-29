# -*- coding: utf-8 -*-

import math

from PyQt5.QtWidgets import QFrame
from PyQt5.QtGui import QPainter, QFontMetrics, QColor
from PyQt5.QtCore import QRect, Qt, QPoint, QLocale

import Map

class RouteWidget(QFrame):

    def __init__(self, parent, config, logger):
        super(RouteWidget, self).__init__(parent)

        self.config = config
        self.logger = logger
        self.pixmap = None
        self.invalidate()

    def invalidate(self):
        self.dest_lat_deg = None
        self.dest_lon_deg = None
        self.route = []
        self.distance = None
        self.duration = None
        self.updateMap()

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
                    self.route, self.config, self.logger)
        self.update()

    def resizeEvent(self, event):
        self.logger.debug("RouteWidget resize %s", event.size())
        self.updateMap()

    def paintEvent(self, event):
        painter = QPainter(self)
        if self.pixmap:
            painter.drawPixmap(0, 0, self.pixmap)
        rect = QRect(0, 0, self.width(), self.height())
        margin = 25
        pad = 10
        if self.distance:
            txt = QLocale().toString(self.distance / 1000, 'f', 1) + ' km'
            fm = QFontMetrics(painter.font())
            rect = fm.boundingRect(txt)
            rect = fm.boundingRect(rect, 0, txt)
            rect.adjust(-pad, 0, pad, 0)
            rect.moveBottomRight(QPoint(self.width() - margin,
                self.height() - margin))
            painter.fillRect(rect, QColor(255, 255, 255, 192))
            painter.drawText(rect, Qt.AlignCenter, txt)
        if self.duration:
            minutes = math.floor(self.duration / 60)
            seconds = self.duration - minutes * 60
            txt = '%u:%02u min.' % (minutes, seconds)
            fm = QFontMetrics(painter.font())
            rect = fm.boundingRect(txt)
            rect = fm.boundingRect(rect, 0, txt)
            rect.adjust(-pad, 0, pad, 0)
            rect.moveBottomLeft(QPoint(margin, self.height() - margin))
            painter.fillRect(rect, QColor(255, 255, 255, 192))
            painter.drawText(rect, Qt.AlignCenter, txt)
