# -*- coding: utf-8 -*-

#-----------------------------------------------------------------------------
#
# Map Display Widget
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

import os

from PyQt5.QtWidgets import QFrame
from PyQt5.QtGui import QPainter, QFontMetrics, QColor, QIcon
from PyQt5.QtCore import Qt, QPoint, QSize, QRect

import Map

#-----------------------------------------------------------------------------

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
        self.objectPlan = None
        self.updateMap()

    def setObjectPlan(self, objectPlan):
        self.objectPlan = objectPlan
        self.update()

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
        self.logger.debug("MapWidget resize %s", event.size())
        self.updateMap()

    def paintEvent(self, event):
        painter = QPainter(self)
        if self.pixmap:
            painter.drawPixmap(0, 0, self.pixmap)
        margin = 25
        pad = 10
        if self.objectPlan:
            txt = self.objectPlan
            fm = QFontMetrics(painter.font())
            rect = fm.boundingRect(txt)
            rect = fm.boundingRect(rect, 0, txt)
            rect.adjust(-pad, 0, pad, 0)

            imageDir = self.config.get("display", "image_dir",
                fallback = "images")
            iconPath = os.path.join(imageDir, 'text-x-generic.svg')
            icon = QIcon(iconPath)
            iconSize = icon.actualSize(rect.size())
            rect.adjust(0, 0, iconSize.width(), 0)

            rect.moveBottomLeft(QPoint(margin, self.height() - margin))
            painter.fillRect(rect, QColor(255, 255, 255, 192))

            iconRect = QRect(rect)
            iconRect.setWidth(iconSize.width())
            icon.paint(painter, iconRect)

            textRect = rect.adjusted(iconRect.width(), 0, 0, 0)
            painter.drawText(textRect, Qt.AlignCenter, txt)

#-----------------------------------------------------------------------------
