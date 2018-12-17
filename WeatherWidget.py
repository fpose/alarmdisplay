# -*- coding: utf-8 -*-

#-----------------------------------------------------------------------------
#
# Weather Widget
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

class WeatherWidget(QWidget):

    finished = pyqtSignal()

    url = "https://www.dwd.de/DWD/warnungen/warnstatus/SchilderEM.jpg"

    def __init__(self, config, logger):
        super(WeatherWidget, self).__init__()

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

        horLayout = QHBoxLayout(self)
        horLayout.setSpacing(0)
        horLayout.setContentsMargins(0, 0, 0, 0)

        label = QLabel(self)
        label.setAlignment(Qt.AlignCenter)
        horLayout.addWidget(label)
        self.imageLabel = label
        self.timeStamp = QDateTime()

        self.request()

    def start(self):
        if self.dataValid():
            self.viewTimer.start()
        else:
            self.finished.emit()

    def stop(self):
        self.viewTimer.stop()

    def dataValid(self):
        now = QDateTime.currentDateTime()
        return self.timeStamp.isValid() and self.timeStamp.daysTo(now) == 0

    def request(self):
        req = QNetworkRequest(QUrl(self.url))
        self.networkAccessManager.get(req)

    def handleResponse(self, reply):
        req = reply.request()
        er = reply.error()
        if er == QNetworkReply.NoError:
            bytes_string = reply.readAll()
            pixmap = QPixmap()
            try:
                pixmap.loadFromData(bytes_string)
                self.imageLabel.setPixmap(pixmap)
                self.timeStamp = QDateTime.currentDateTime()
            except:
                self.logger.error("Failed to set weather data.",
                        exc_info = True)
        reply.deleteLater()

    def viewTimeout(self):
        self.finished.emit()

#-----------------------------------------------------------------------------
