# -*- coding: utf-8 -*-

#-----------------------------------------------------------------------------
#
# Forest Fire Warning Map Widget
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

class ForestWidget(QWidget):

    finished = pyqtSignal()

    urls = ["https://www.dwd.de/DWD/warnungen/agrar/wbx/wbx_stationen.png",
            "https://www.dwd.de/DWD/warnungen/agrar/wbx/wbx_stationen1.png",
            "https://www.dwd.de/DWD/warnungen/agrar/wbx/wbx_stationen2.png"]

    def __init__(self, config, logger):
        super(ForestWidget, self).__init__()

        self.config = config
        self.logger = logger

        self.updateTimer = QTimer(self)
        self.updateTimer.setInterval(6 * 60 * 60000)
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
        titleLabel.setText("Waldbrandgefahrenindex")
        verLayout.addWidget(titleLabel, 2)

        horLayout = QHBoxLayout()
        horLayout.setSpacing(0)
        horLayout.setContentsMargins(0, 0, 0, 0)
        verLayout.addLayout(horLayout, 10)

        self.imageLabels = []
        self.pixmaps = []
        self.timeStamps = []
        for url in self.urls:
            label = QLabel(self)
            label.setAlignment(Qt.AlignCenter)
            horLayout.addWidget(label)
            self.imageLabels.append(label)

            pixmap = QPixmap()
            self.pixmaps.append(pixmap)
            self.timeStamps.append(QDateTime())

        spacerWidget = QWidget(self)
        verLayout.addWidget(spacerWidget, 1)

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
        for t in self.timeStamps:
            if not t.isValid() or t.daysTo(now) > 0:
                return False
        return True

    def request(self):
        for idx in range(len(self.urls)):
            req = QNetworkRequest(QUrl(self.urls[idx]))
            self.networkAccessManager.get(req)

    def handleResponse(self, reply):
        req = reply.request()
        er = reply.error()
        if er == QNetworkReply.NoError:
            bytes_string = reply.readAll()
            pixmap = QPixmap()
            try:
                pixmap.loadFromData(bytes_string)
                for idx in range(len(self.urls)):
                    if req.url() == QUrl(self.urls[idx]):
                        self.pixmaps[idx] = pixmap
                        self.updatePixmaps()
                        self.timeStamps[idx] = QDateTime.currentDateTime()
            except:
                self.logger.error("Failed to set forest data.",
                        exc_info = True)
        reply.deleteLater()

    def updatePixmaps(self):
        for idx in range(len(self.urls)):
            pixmap = self.pixmaps[idx]
            if pixmap.isNull():
                continue
            label = self.imageLabels[idx]
            scaledPix = pixmap.scaledToHeight(label.height(),
                    Qt.SmoothTransformation)
            label.setPixmap(scaledPix)

    def resizeEvent(self, event):
        self.updatePixmaps()

    def viewTimeout(self):
        self.finished.emit()

#-----------------------------------------------------------------------------
