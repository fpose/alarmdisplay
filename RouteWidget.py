# -*- coding: utf-8 -*-

#-----------------------------------------------------------------------------
#
# Route Display Widget
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

from PyQt5.QtWidgets import QFrame
from PyQt5.QtGui import QPainter, QFontMetrics, QColor
from PyQt5.QtCore import QRect, Qt, QPoint, QLocale

import Map

#-----------------------------------------------------------------------------

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
            self.markerRects = []
        else:
            self.pixmap, self.markerRects = Map.getRoutePixmap( \
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
            if self.intersectsMarkers(rect):
                rect.moveTopRight(QPoint(self.width() - margin, margin))
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
            if self.intersectsMarkers(rect):
                rect.moveTopLeft(QPoint(margin, margin))
            painter.fillRect(rect, QColor(255, 255, 255, 192))
            painter.drawText(rect, Qt.AlignCenter, txt)

    def intersectsMarkers(self, rect):
        for markerRect in self.markerRects:
            if markerRect.intersects(rect):
                return True
        return False

#-----------------------------------------------------------------------------
