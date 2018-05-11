# -*- coding: utf-8 -*-

#-----------------------------------------------------------------------------
#
# Alarm Widget
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
from RouteWidget import RouteWidget

#-----------------------------------------------------------------------------

class AlarmWidget(QWidget):

    def __init__(self, main):
        super(AlarmWidget, self).__init__()

        self.main = main
        self.config = main.config
        self.logger = main.logger

        self.alarm = None
        self.alarmDateTime = None

        self.imageDir = self.config.get("display", "image_dir",
                fallback = "images")

        self.elapsedTimer = QTimer(self)
        self.elapsedTimer.setInterval(1000)
        self.elapsedTimer.setSingleShot(False)
        self.elapsedTimer.timeout.connect(self.elapsedTimeout)

        verLayout = QVBoxLayout(self)
        verLayout.setSpacing(0)
        verLayout.setContentsMargins(0, 0, 0, 0)

        titleLayout = QHBoxLayout()
        titleLayout.setSpacing(0)
        verLayout.addLayout(titleLayout, 0)

        self.symbolLabel = QLabel(self)
        self.symbolLabel.setStyleSheet("""
            background-color: rgb(120, 0, 0);
            padding: 10px;
            """)
        titleLayout.addWidget(self.symbolLabel, 0)

        self.titleLabel = QLabel(self)
        self.titleLabel.setSizePolicy(QSizePolicy.Ignored,
                QSizePolicy.Preferred)
        self.titleLabel.setStyleSheet("""
            color: white;
            font-size: 80px;
            background-color: rgb(120, 0, 0);
            padding: 10px;
            """)
        titleLayout.addWidget(self.titleLabel, 1)

        self.timerLabel = QLabel(self)
        self.timerLabel.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.timerLabel.setStyleSheet("""
            color: white;
            background-color: rgb(120, 0, 0);
            padding: 10px;
            """)
        titleLayout.addWidget(self.timerLabel, 0)

        locationLayout = QHBoxLayout()
        locationLayout.setSpacing(0)
        verLayout.addLayout(locationLayout, 0)

        self.locationSymbolLabel = QLabel(self)
        self.locationSymbolLabel.setStyleSheet("""
            padding: 10px;
            """)
        locationLayout.addWidget(self.locationSymbolLabel, 0)

        innerLocationLayout = QVBoxLayout()
        innerLocationLayout.setSpacing(0)
        locationLayout.addLayout(innerLocationLayout, 1)

        self.locationLabel = QLabel(self)
        self.locationLabel.setIndent(0)
        self.locationLabel.setSizePolicy(QSizePolicy.Ignored,
                QSizePolicy.Preferred)
        self.locationLabel.setStyleSheet("""
            padding: 10px;
            """)
        innerLocationLayout.addWidget(self.locationLabel, 1)

        self.locationHintLabel = QLabel(self)
        self.locationHintLabel.setIndent(0)
        self.locationHintLabel.setSizePolicy(QSizePolicy.Ignored,
                QSizePolicy.Preferred)
        self.locationHintLabel.setStyleSheet("""
            padding: 10px;
            font-size: 40px;
            """)
        innerLocationLayout.addWidget(self.locationHintLabel, 1)

        # Attention row ------------------------------------------------------

        attentionLayout = QHBoxLayout()
        attentionLayout.setSpacing(0)
        verLayout.addLayout(attentionLayout, 0)

        self.attentionSymbolLabel = QLabel(self)
        self.attentionSymbolLabel.setStyleSheet("""
            padding: 10px;
            """)
        attentionLayout.addWidget(self.attentionSymbolLabel, 0)

        self.attentionLabel = QLabel(self)
        self.attentionLabel.setIndent(0)
        self.attentionLabel.setSizePolicy(QSizePolicy.Ignored,
                QSizePolicy.Preferred)
        self.attentionLabel.setStyleSheet("""
            padding: 10px;
            font-size: 40px;
            """)
        attentionLayout.addWidget(self.attentionLabel, 1)

        self.callerSymbolLabel = QLabel(self)
        self.callerSymbolLabel.setStyleSheet("""
            padding: 10px;
            """)
        attentionLayout.addWidget(self.callerSymbolLabel, 0)

        self.callerLabel = QLabel(self)
        self.callerLabel.setIndent(0)
        self.callerLabel.setSizePolicy(QSizePolicy.Ignored,
                QSizePolicy.Preferred)
        self.callerLabel.setStyleSheet("""
            padding: 10px;
            font-size: 40px;
            """)
        attentionLayout.addWidget(self.callerLabel, 1)

        # Fallback row -------------------------------------------------------

        self.fallbackLabel = QLabel(self)
        self.fallbackLabel.setIndent(0)
        self.fallbackLabel.setWordWrap(True)
        self.fallbackLabel.setSizePolicy(QSizePolicy.Ignored,
                QSizePolicy.Preferred)
        self.fallbackLabel.setStyleSheet("""
            padding: 10px;
            font-size: 40px;
            """)

        verLayout.addWidget(self.fallbackLabel, 0)

        # Maps ---------------------------------------------------------------

        horLayout = QHBoxLayout()
        horLayout.setSpacing(2)
        verLayout.addLayout(horLayout, 2)

        self.leftMap = MapWidget(self, self.config, self.logger)
        self.leftMap.setStyleSheet("""
            font-size: 60px;
            color: #cc0000;
            """)
        horLayout.addWidget(self.leftMap, 3)

        self.rightMap = RouteWidget(self, self.config, self.logger)
        self.rightMap.setStyleSheet("""
            font-size: 40px;
            """)
        horLayout.addWidget(self.rightMap, 3)

    def startTimer(self, alarmDateTime):
        self.alarmDateTime = alarmDateTime
        self.elapsedTimer.start()
        self.elapsedTimeout()

    def setRoute(self, route):
        self.logger.info('Destination map...')
        self.leftMap.setTarget(self.alarm.lat, self.alarm.lon, route)
        self.logger.info('Route map...')
        self.rightMap.setTarget(self.alarm.lat, self.alarm.lon, route)

    def processAlarm(self, alarm):
        self.alarm = alarm

        self.titleLabel.setText(self.alarm.title())

        image = self.alarm.imageBase()
        if image:
            image += '.svg'
            pixmap = QPixmap(os.path.join(self.imageDir, image))
        else:
            pixmap = QPixmap()
        self.symbolLabel.setPixmap(pixmap)

        self.locationLabel.setText(self.alarm.location())
        self.locationHintLabel.setText(self.alarm.ortshinweis)
        if self.locationHintLabel.text():
            self.locationHintLabel.show()
        else:
            self.locationHintLabel.hide()

        if self.locationLabel.text() or self.locationHintLabel.text():
            pixmap = QPixmap(os.path.join(self.imageDir, 'go-home.svg'))
        else:
            pixmap = QPixmap()
        self.locationSymbolLabel.setPixmap(pixmap)

        self.attentionLabel.setText(self.alarm.attention())
        if self.attentionLabel.text():
            pixmap = QPixmap(os.path.join(self.imageDir,
                        'emblem-important.svg'))
            self.attentionSymbolLabel.setPixmap(pixmap)
            self.attentionSymbolLabel.show()
            self.attentionLabel.show()
        else:
            pixmap = QPixmap()
            self.attentionSymbolLabel.setPixmap(pixmap)
            self.attentionSymbolLabel.hide()
            self.attentionLabel.hide()

        self.callerLabel.setText(self.alarm.callerInfo())
        if self.callerLabel.text():
            pixmap = QPixmap(os.path.join(self.imageDir,
                        'caller.svg'))
            self.callerSymbolLabel.setPixmap(pixmap)
            self.callerSymbolLabel.show()
            self.callerLabel.show()
        else:
            pixmap = QPixmap()
            self.callerSymbolLabel.setPixmap(pixmap)
            self.callerSymbolLabel.hide()
            self.callerLabel.hide()

        self.fallbackLabel.setText(self.alarm.fallbackStr)
        if self.fallbackLabel.text():
            self.fallbackLabel.show()
        else:
            self.fallbackLabel.hide()

        self.leftMap.invalidate()
        self.leftMap.setObjectPlan(self.alarm.objektnummer)

        self.rightMap.invalidate()

    def resizeEvent(self, event):
        self.logger.debug('Resizing alarm widget to %u x %u.',
            event.size().width(), event.size().height())

    def elapsedTimeout(self):
        now = QDateTime.currentDateTime()
        diffMs = self.alarmDateTime.msecsTo(now)
        seconds = math.floor(diffMs / 1000)
        hours = math.floor(seconds / 3600)
        seconds -= hours * 3600
        minutes = math.floor(seconds / 60)
        seconds -= minutes * 60
        if hours > 0:
            text = u'%u:%02u:%02u' % (hours, minutes, seconds)
        else:
            text = u'%u:%02u' % (minutes, seconds)
        self.timerLabel.setText(text)

#-----------------------------------------------------------------------------
