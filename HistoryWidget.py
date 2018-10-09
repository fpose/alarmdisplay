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
import datetime
import babel.dates
from tzlocal import get_localzone

from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtSvg import QSvgRenderer

from MapWidget import MapWidget
from Alarm import Alarm
from helpers import *

#-----------------------------------------------------------------------------

class HistoryWidget(QWidget):

    finished = pyqtSignal()

    historySize = 5

    def __init__(self, config, logger):
        super(HistoryWidget, self).__init__()

        self.config = config
        self.logger = logger

        self.imageDir = self.config.get("display", "image_dir",
                fallback = "images")

        self.cycleTimer = QTimer(self)
        self.cycleTimer.setInterval( \
            self.config.getint("idle", "history_period", fallback = 10) \
            * 1000)
        self.cycleTimer.setSingleShot(False)
        self.cycleTimer.timeout.connect(self.cycle)

        horLayout = QHBoxLayout(self)
        horLayout.setSpacing(0)
        horLayout.setContentsMargins(0, 0, 0, 0)

        verLayout = QVBoxLayout()
        verLayout.setSpacing(0)
        verLayout.setContentsMargins(0, 0, 0, 0)
        horLayout.addLayout(verLayout, 1)

        self.targetMap = MapWidget(self, self.config, self.logger)
        self.targetMap.maxCacheEntries = self.historySize
        self.targetMap.setStyleSheet("""
            font-size: 60px;
            color: #cc0000;
            """)
        horLayout.addWidget(self.targetMap, 1)

        label = QLabel(self)
        label.setText('Letzte Einsätze')
        label.setIndent(0)
        label.setStyleSheet("""
            font-size: 50px;
            padding: 10px 10px 10px 60px;
            """)
        verLayout.addWidget(label)

        self.symbolLabels = []
        self.titleLabels = []
        self.descLabels = []
        self.index = 0

        for i in range(0, self.historySize):
            itemLayout = QHBoxLayout()
            itemLayout.setSpacing(0)
            itemLayout.setContentsMargins(0, 0, 0, 0)
            verLayout.addLayout(itemLayout)

            label = QLabel(self)
            itemLayout.addWidget(label, 0)
            self.symbolLabels.append(label)

            label = QLabel(self)
            label.setIndent(0)
            label.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)
            itemLayout.addWidget(label, 1)
            self.titleLabels.append(label)

            label = QLabel(self)
            label.setIndent(0)
            label.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)
            verLayout.addWidget(label)
            self.descLabels.append(label)

    def updateStyles(self):
        for i in range(0, self.historySize):
            label = self.symbolLabels[i]
            label.setStyleSheet(self.style(i, 'symbol'))

            label = self.titleLabels[i]
            label.setStyleSheet(self.style(i, 'title'))

            label = self.descLabels[i]
            label.setStyleSheet(self.style(i, 'desc'))

    def style(self, index, section):
        style = ''

        if section == 'symbol':
            style += 'padding: 0px 10px 0px 10px;'
        if section == 'title':
            style += 'font-size: 40px;'
        if section == 'desc':
            style += 'font-size: 25px;'
            style += 'padding: 0px 0px 20px 60px;'
            style += 'alignment: top;'

        if index == self.index:
            style += 'background-color: #5050a0;'
        else:
            if index % 2:
                style += 'background-color: #101020;'
            else:
                style += 'background-color: #202040;'

        return style

    def start(self):
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
        while index < self.historySize and len(paths) > 0:
            path = paths[0]
            paths = paths[1:]

            alarm = Alarm(self.config)
            try:
                alarm.load(path)
            except:
                continue

            if alarm.fallbackStr:
                # ignore incomplete or invalid alarms in history
                continue

            if len(self.alarms) and self.alarms[-1].matches(alarm):
                self.alarms[-1].merge(alarm)
            else:
                self.alarms.append(alarm)
                index += 1

        local_tz = get_localzone()
        now = local_tz.localize(datetime.datetime.now())

        index = 0
        for alarm in self.alarms:
            dateStr = alarm.datetime.strftime('%A, %d. %B, %H:%M')
            delta = alarm.datetime - now
            dateStr += ' (' + babel.dates.format_timedelta(delta,
                    add_direction = True) + ')'
            image = alarm.imageBase()
            if image:
                image += '.svg'
                pixmap = pixmapFromSvg(os.path.join(self.imageDir, image), 40)
            else:
                pixmap = QPixmap()
            self.symbolLabels[index].setPixmap(pixmap)
            title = alarm.title()
            if not title:
                title = alarm.fallbackStr
            self.titleLabels[index].setText(title)
            desc = dateStr
            loc = alarm.location()
            if loc:
                desc += '\n' + loc
            self.descLabels[index].setText(desc)
            index += 1

        self.index = 0
        if len(self.alarms):
            alarm = self.alarms[self.index]
            self.targetMap.setTarget(alarm.lat, alarm.lon, ([],))
            self.cycleTimer.start()
            self.updateStyles()
        else:
            self.finished.emit()

    def stop(self):
        self.cycleTimer.stop()

    def cycle(self):
        self.index += 1
        if self.index >= len(self.alarms):
            self.index = 0
            self.cycleTimer.stop()
            self.finished.emit()

        alarm = self.alarms[self.index]
        self.targetMap.setTarget(alarm.lat, alarm.lon, ([],))

        self.updateStyles()

#-----------------------------------------------------------------------------
