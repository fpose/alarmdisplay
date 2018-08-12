# -*- coding: utf-8 -*-

#-----------------------------------------------------------------------------
#
# Water Level Widget
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
import datetime

from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtNetwork import *

#-----------------------------------------------------------------------------

class WaterLevelWidget(QWidget):

    finished = pyqtSignal()

    def __init__(self, config, logger):
        super(WaterLevelWidget, self).__init__()

        self.config = config
        self.logger = logger

        self.updateTimer = QTimer(self)
        self.updateTimer.setInterval(5 * 60000)
        self.updateTimer.setSingleShot(False)
        self.updateTimer.timeout.connect(self.request)
        self.updateTimer.start()

        self.viewTimer = QTimer(self)
        self.viewTimer.setInterval(10000)
        self.viewTimer.setSingleShot(True)
        self.viewTimer.timeout.connect(self.viewTimeout)

        self.networkAccessManager = QNetworkAccessManager()
        self.networkAccessManager.finished.connect(self.handleResponse)

        verLayout = QVBoxLayout(self)
        verLayout.setSpacing(0)
        verLayout.setContentsMargins(0, 0, 0, 0)

        titleLabel = QLabel(self)
        titleLabel.setAlignment(Qt.AlignCenter)
        titleLabel.setText("Pegelstände")
        verLayout.addWidget(titleLabel, 2)

        label = QLabel(self)
        label.setAlignment(Qt.AlignCenter)
        verLayout.addWidget(label, 10)
        self.imageLabel = label

        spacerWidget = QWidget(self)
        verLayout.addWidget(spacerWidget, 1)

        self.pixmap = QPixmap()

        self.request()

    def start(self):
        self.viewTimer.start()

    def stop(self):
        self.viewTimer.stop()

    def request(self):
        url = self.config.get("idle", "water_url", fallback = '')
        if url:
            req = QNetworkRequest(QUrl(url))
            self.networkAccessManager.get(req)

    def handleResponse(self, reply):
        req = reply.request()
        er = reply.error()
        if er == QNetworkReply.NoError:
            bytes_string = reply.readAll()
            try:
                self.pixmap.loadFromData(bytes_string)
            except:
                self.logger.error("Failed to set water level data.",
                        exc_info = True)
        else:
            self.logger.error("Failed to get water level data:")
            self.logger.error(reply.errorString())
        self.updatePixmaps()

    def updatePixmaps(self):
        scaledPix = self.pixmap.scaledToHeight(self.imageLabel.height(),
                Qt.SmoothTransformation)
        self.imageLabel.setPixmap(scaledPix)

    def resizeEvent(self, event):
        self.logger.debug('Resizing water level widget to %u x %u.',
            event.size().width(), event.size().height())
        self.updatePixmaps()

    def viewTimeout(self):
        self.finished.emit()

#-----------------------------------------------------------------------------
