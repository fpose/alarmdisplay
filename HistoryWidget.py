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
from Alarm import Alarm

#-----------------------------------------------------------------------------

class HistoryWidget(QWidget):

    def __init__(self, config, logger):
        super(HistoryWidget, self).__init__()

        self.config = config
        self.logger = logger

        self.cycleTimer = QTimer(self)
        self.cycleTimer.setInterval( \
            self.config.get("idle", "cycle_period", fallback = 5) * 1000)
        self.cycleTimer.setSingleShot(False)
        self.cycleTimer.timeout.connect(self.cycle)

        horLayout = QHBoxLayout(self)
        horLayout.setSpacing(0)
        horLayout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(horLayout)

        verLayout = QVBoxLayout(self)
        verLayout.setSpacing(0)
        verLayout.setContentsMargins(0, 0, 0, 0)
        horLayout.addLayout(verLayout, 1)

        self.targetMap = MapWidget(self, self.config, self.logger)
        self.targetMap.setStyleSheet("""
            font-size: 60px;
            color: #cc0000;
            """)
        horLayout.addWidget(self.targetMap, 1)

        self.titleLabels = []
        self.descLabels = []
        self.index = 0

        for i in range(0, 5):
            label = QLabel(self)
            verLayout.addWidget(label)
            self.titleLabels.append(label)

            label = QLabel(self)
            label.setAlignment(Qt.AlignTop)
            verLayout.addWidget(label)
            self.descLabels.append(label)

        self.update()
        self.updateStyles()

    def updateStyles(self):
        for i in range(0, 5):
            label = self.titleLabels[i]
            label.setStyleSheet(self.style(i, 'title'))

            label = self.descLabels[i]
            label.setStyleSheet(self.style(i, 'desc'))

    def resizeEvent(self, event):
        self.logger.debug('Resizing history widget to %u x %u.',
            event.size().width(), event.size().height())

    def style(self, index, section):
        style = 'padding: 10px;'

        if section == 'title':
            style += 'font-size: 40px;'
        else:
            style += 'font-size: 30px;'

        if index == self.index:
            style += 'background-color: #404080;'

        return style

    def update(self):
        self.cycleTimer.stop()

        path = self.config.get("db", "path", fallback = None)
        if not path:
            return

        paths = [os.path.join(path, entry) for entry in os.listdir(path)]
        paths = [path for path in paths if \
                (path.endswith('.dme') or \
                path.endswith('.xml')) and \
                os.path.isfile(path)]
        paths = sorted(paths, reverse = True)

        self.alarms = []
        index = 0
        while index < 5 and len(paths) > 0:
            path = paths[0]
            paths = paths[1:]

            alarm = Alarm(self.config)
            alarm.load(path, self.logger)

            if len(self.alarms) and self.alarms[-1].matches(alarm):
                self.alarms[-1].merge(alarm)
            else:
                self.alarms.append(alarm)
                index += 1

        index = 0
        for alarm in self.alarms:
            dateStr = alarm.datetime.strftime('%A, %d. %B %Y, %H:%M')
            self.titleLabels[index].setText(alarm.title())
            self.descLabels[index].setText(dateStr + '\n' + alarm.location())
            index += 1

        self.index = 0
        if len(self.alarms):
            alarm = self.alarms[self.index]
            self.targetMap.setTarget(alarm.lat, alarm.lon, ([],))
            self.cycleTimer.start()

    def cycle(self):
        self.index += 1
        if self.index >= len(self.alarms):
            self.index = 0

        alarm = self.alarms[self.index]
        self.targetMap.setTarget(alarm.lat, alarm.lon, ([],))

        self.updateStyles()

#-----------------------------------------------------------------------------
