# -*- coding: utf-8 -*-

#-----------------------------------------------------------------------------
#
# History Widget
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

from MapWidget import MapWidget

#-----------------------------------------------------------------------------

class HistoryWidget(QWidget):

    def __init__(self, config, logger):
        super(HistoryWidget, self).__init__()

        self.config = config
        self.logger = logger

        path = self.config.get("db", "path", fallback = None)

        horLayout = QHBoxLayout(self)
        horLayout.setSpacing(0)
        horLayout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(horLayout)

        verLayout = QVBoxLayout(self)
        verLayout.setSpacing(0)
        verLayout.setContentsMargins(0, 0, 0, 0)
        horLayout.addLayout(verLayout)

        self.targetMap = MapWidget(self, self.config, self.logger)
        self.targetMap.setStyleSheet("""
            font-size: 60px;
            color: #cc0000;
            """)
        horLayout.addWidget(self.targetMap, 3)

        label = QLabel(self)
        label.setText('Einsatz')
        horLayout.addWidget(label)

    def resizeEvent(self, event):
        self.logger.debug('Resizing history widget to %u x %u.',
            event.size().width(), event.size().height())

#-----------------------------------------------------------------------------
