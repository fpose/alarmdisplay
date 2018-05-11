# -*- coding: utf-8 -*-

#-----------------------------------------------------------------------------
#
# Idle Widget
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
import math
import datetime

from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

from HistoryWidget import *
from helpers import *

#-----------------------------------------------------------------------------

class IdleWidget(QWidget):

    def __init__(self, main):
        super(IdleWidget, self).__init__()

        self.main = main
        self.config = main.config
        self.logger = main.logger

        self.imageDir = self.config.get("display", "image_dir",
                fallback = "images")

        self.clockTimer = QTimer(self)
        self.clockTimer.setInterval(100)
        self.clockTimer.setSingleShot(False)
        self.clockTimer.timeout.connect(self.clockTimeout)
        self.clockTimer.start()

        verLayout = QVBoxLayout(self)
        verLayout.setSpacing(0)
        verLayout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(verLayout)

        titleLayout = QHBoxLayout(self)
        titleLayout.setSpacing(0)
        verLayout.addLayout(titleLayout, 0)

        self.symbolLabel = QLabel(self)
        self.symbolLabel.setStyleSheet("""
            background-color: rgb(0, 0, 120);
            padding: 10px;
            """)
        logo = self.config.get("display", "logo", fallback = None)
        if logo:
            pixmap = QPixmap(os.path.join(self.imageDir, logo))
            pixmap = pixmap.scaledToWidth(100,
                    mode = Qt.SmoothTransformation)
            print(pixmap.size())
            self.symbolLabel.setPixmap(pixmap)

        titleLayout.addWidget(self.symbolLabel, 0)

        self.titleLabel = QLabel(self)
        self.titleLabel.setSizePolicy(QSizePolicy.Ignored,
                QSizePolicy.Preferred)
        self.titleLabel.setStyleSheet("""
            color: white;
            font-size: 60px;
            background-color: rgb(0, 0, 120);
            padding: 10px;
            """)
        self.titleLabel.setText(self.config.get("display", "title",
                fallback = "Alarmdisplay"))
        titleLayout.addWidget(self.titleLabel, 1)

        self.clockLabel = QLabel(self)
        self.clockLabel.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.clockLabel.setStyleSheet("""
            color: white;
            font-size: 80px;
            background-color: rgb(0, 0, 120);
            padding: 10px;
            """)
        titleLayout.addWidget(self.clockLabel, 0)

        self.stackedWidget = QStackedWidget(self)
        verLayout.addWidget(self.stackedWidget)

        self.historyWidget = HistoryWidget(self.config, self.logger)
        self.stackedWidget.addWidget(self.historyWidget)

    def update(self):
        self.historyWidget.update()

    def resizeEvent(self, event):
        self.logger.debug('Resizing idle widget to %u x %u.',
            event.size().width(), event.size().height())

    def clockTimeout(self):
        now = datetime.datetime.now()
        clockStr = now.strftime('%H:%M:%S')
        if self.clockLabel.text() != clockStr:
            self.clockLabel.setText(clockStr)

#-----------------------------------------------------------------------------
