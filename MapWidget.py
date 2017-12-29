# -*- coding: utf-8 -*-

from PyQt5.QtWidgets import QFrame
from PyQt5.QtGui import QPainter, QFontMetrics, QColor
from PyQt5.QtCore import Qt, QPoint

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
            rect.moveBottomLeft(QPoint(margin, self.height() - margin))
            painter.fillRect(rect, QColor(255, 255, 255, 192))
            painter.drawText(rect, Qt.AlignCenter, txt)
