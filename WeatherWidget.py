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

from MapWidget import MapWidget
from Alarm import Alarm

#-----------------------------------------------------------------------------

class WeatherWidget(QWidget):

    finished = pyqtSignal()

    weatherUrl = "https://www.dwd.de/DWD/warnungen/warnstatus/SchilderEM.jpg"
    forestUrl = "https://www.dwd.de/DWD/warnungen/agrar/wbx/wbx_stationen.png"

    def __init__(self, config, logger):
        super(WeatherWidget, self).__init__()

        self.config = config
        self.logger = logger

        self.index = 0
        self.pixmaps = [QPixmap(), QPixmap()]

        self.updateTimer = QTimer(self)
        self.updateTimer.setInterval(5 * 60000)
        self.updateTimer.setSingleShot(False)
        self.updateTimer.timeout.connect(self.requestWeather)
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

        self.requestWeather()
        self.requestForest()

    def start(self):
        self.index = 0
        self.viewTimer.start()
        self.updatePixmap()

    def updatePixmap(self):
        if self.index < len(self.pixmaps):
            self.imageLabel.setPixmap(self.pixmaps[self.index])
        else:
            self.imageLabel.setPixmap(QPixmap())

    def stop(self):
        self.viewTimer.stop()

    def requestWeather(self):
        req = QNetworkRequest(QUrl(self.weatherUrl))
        self.networkAccessManager.get(req)

    def requestForest(self):
        req = QNetworkRequest(QUrl(self.forestUrl))
        self.networkAccessManager.get(req)

    def handleResponse(self, reply):
        req = reply.request()
        er = reply.error()
        if er == QNetworkReply.NoError:
            bytes_string = reply.readAll()
            pixmap = QPixmap()
            try:
                pixmap.loadFromData(bytes_string)
                if req.url() == QUrl(self.weatherUrl):
                    index = 0
                else:
                    index = 1
                    #pixmap.setMask(pixmap.createHeuristicMask());
                self.pixmaps[index] = pixmap
                self.updatePixmap()
            except:
                self.logger.error("Failed to set weather data.",
                        exc_info = True)
        else:
            self.logger.error("Failed to get weather data:")
            self.logger.error(reply.errorString())

    def resizeEvent(self, event):
        self.logger.debug('Resizing weather widget to %u x %u.',
            event.size().width(), event.size().height())

    def viewTimeout(self):
        self.index += 1
        if self.index < len(self.pixmaps):
            self.updatePixmap()
            self.viewTimer.start()
        else:
            self.finished.emit()

#-----------------------------------------------------------------------------
