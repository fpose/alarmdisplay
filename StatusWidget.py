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

#-----------------------------------------------------------------------------

class StatusWidget(QWidget):

    def __init__(self, main):
        super(StatusWidget, self).__init__()

        self.main = main
        self.config = main.config
        self.logger = main.logger
        websocketReceiver = main.websocketReceiver

        self.imageDir = self.config.get("display", "image_dir",
                fallback = "images")

        layout = QHBoxLayout(self)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)

        self.labelDict = {}
        for address, name in websocketReceiver.status:
            label = QLabel(self)
            layout.addWidget(label, 1)
            label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            label.setStyleSheet("""
                font-size: 30px;
                padding: 10px;
                """)
            label.setText(name)

            label = QLabel(self)
            layout.addWidget(label, 0)
            label.setStyleSheet("""
                font-size: 40px;
                padding: 10px;
                """)
            self.labelDict[address] = label

        label = QLabel(self)
        layout.addWidget(label, 1)

    def setStatus(self, status):
        if status['address'] in self.labelDict:
            label = self.labelDict[status['address']]
            label.setText(str(status['status']))

#-----------------------------------------------------------------------------
