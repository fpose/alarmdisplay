# -*- coding: utf-8 -*-

#-----------------------------------------------------------------------------
#
# Status Widget
#
# Copyright (C) 2021 Florian Pose
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
import datetime
import re

from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtSvg import QSvgRenderer

#-----------------------------------------------------------------------------

class StatusWidget(QWidget):

    def __init__(self, main):
        super(StatusWidget, self).__init__()

        self.main = main
        self.config = main.config
        self.logger = main.logger
        websocketReceiver = main.websocketReceiver

        imageDir = self.config.get("display", "image_dir",
                fallback = "images")
        self.statusPixmaps = {}
        for s in (1, 2, 3, 4, 6):
            path = os.path.join(imageDir, 'status%u.svg' % (s))
            try:
                renderer = QSvgRenderer(path)
                pixmap = QPixmap(48, 48);
                pixmap.fill(Qt.transparent);
                painter = QPainter(pixmap);
                renderer.render(painter, QRectF(pixmap.rect()));
            except:
                self.logger.warning('Failed to load status image %s.', path,
                        exc_info = True)
                continue
            self.statusPixmaps[s] = pixmap

        layout = QHBoxLayout(self)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)

        self.labelDict = {}
        self.animationDict = {}
        for address, name in websocketReceiver.status:
            label = QLabel(self)
            layout.addWidget(label, 1)
            label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            label.setStyleSheet("""
                font-size: 30px;
                padding: 10px;
                """)
            label.setText(name)

            label = AnimatedLabel(self)
            layout.addWidget(label, 0)
            self.labelDict[address] = label

            animation = QPropertyAnimation(label, b'color')
            animation.setStartValue(QColor(Qt.transparent))
            animation.setKeyValueAt(0.5, QColor(Qt.white))
            animation.setEndValue(QColor(Qt.transparent))
            animation.setDuration(1000)
            animation.setLoopCount(10)
            animation.setEasingCurve(QEasingCurve.OutInQuad);
            self.animationDict[address] = animation

        label = QLabel(self)
        layout.addWidget(label, 1)

    def setStatus(self, status):
        address = status['address']
        if address in self.labelDict:
            label = self.labelDict[address]
            s = status['status']
            if s in self.statusPixmaps:
                label.setPixmap(self.statusPixmaps[s])
                label.setText('')
            else:
                label.setPixmap(QPixmap())
                label.setText(str(s))
        if address in self.animationDict:
            self.animationDict[address].start()

#-----------------------------------------------------------------------------

class AnimatedLabel(QLabel):

    def __init__(self, parent):
        super(AnimatedLabel, self).__init__(parent)

    def setColor(self, color):
        s = """
        font-size: 40px;
        padding: 10px;
        background-color: #%08x;""" % (color.rgba())
        self.setStyleSheet(s)

    def getColor(self):
        return Qt.black

    color = pyqtProperty(QColor, getColor, setColor)

#-----------------------------------------------------------------------------
