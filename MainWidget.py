# -*- coding: utf-8 -*-

import os
import math

from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

from MapWidget import MapWidget
from RouteWidget import RouteWidget
from Map import getRoute

class MainWidget(QWidget):

    def __init__(self, config):
        super(MainWidget, self).__init__()

        self.config = config

        self.alarmActive = False
        self.elapsedTimer = QTimer(self)
        self.elapsedTimer.setInterval(1000)
        self.elapsedTimer.setSingleShot(False)
        self.elapsedTimer.timeout.connect(self.timeout)
        self.alarmDateTime = None

        self.move(0, 0)
        self.resize(1920, 1080)

        self.setWindowTitle('Alarmdisplay')
        self.setStyleSheet("""
            font-size: 70px;
            background-color: rgb(0, 34, 44);
            color: rgb(2, 203, 255);
            font-family: "DejaVu Sans";
            """)

        verLayout = QVBoxLayout(self)
        verLayout.setContentsMargins(0, 0, 0, 0)

        self.msgLabel = QLabel(self)
        self.msgLabel.setStyleSheet("""
            color: white;
            background-color: rgb(80, 0, 0);
            """)
        verLayout.addWidget(self.msgLabel, 1)

        horLayout = QHBoxLayout(self)
        verLayout.addLayout(horLayout, 2)

        self.leftMap = MapWidget(self, self.config)
        self.leftMap.setStyleSheet("""
            background-color: rgb(80, 80, 0);
            """)
        horLayout.addWidget(self.leftMap, 2)

        centerLayout = QVBoxLayout(self)
        horLayout.addLayout(centerLayout, 1)

        logoLabel = QLabel(self)
        logo = self.config.get("display", "logo", fallback = None)
        if logo:
            imageDir = self.config.get("display", "image_dir",
                    fallback = "images")
            styleSheet = 'image: url({0});'.format( \
                    os.path.join(imageDir, logo))
            logoLabel.setStyleSheet(styleSheet)
        centerLayout.addWidget(logoLabel)

        self.timerLabel = QLabel(self)
        self.timerLabel.setAlignment(Qt.AlignCenter)
        centerLayout.addWidget(self.timerLabel)

        self.rightMap = RouteWidget(self, self.config)
        self.rightMap.setStyleSheet("""
            background-color: rgb(0, 80, 80);
            """)
        horLayout.addWidget(self.rightMap, 2)

        self.setLayout(verLayout)

        action = QAction(self)
        action.setShortcut(QKeySequence("1"))
        action.setShortcutContext(Qt.ApplicationShortcut)
        action.triggered.connect(self.exampleJugend)
        self.addAction(action)

        action = QAction(self)
        action.setShortcut(QKeySequence("2"))
        action.setShortcutContext(Qt.ApplicationShortcut)
        action.triggered.connect(self.exampleEngels)
        self.addAction(action)

        action = QAction(self)
        action.setShortcut(QKeySequence("3"))
        action.setShortcutContext(Qt.ApplicationShortcut)
        action.triggered.connect(self.exampleSack)
        self.addAction(action)

        self.exampleJugend()

    def resizeEvent(self, event):
        print(event.size())

    def startTimer(self):
        self.alarmDateTime = QDateTime.currentDateTime()
        self.elapsedTimer.start()
        self.timeout()

    def timeout(self):
        now = QDateTime.currentDateTime()
        diffMs = self.alarmDateTime.msecsTo(now)
        seconds = math.floor(diffMs / 1000)
        minutes = math.floor(seconds / 60)
        seconds -= minutes * 60
        self.timerLabel.setText(u'%02u:%02u' % (minutes, seconds))

    def exampleJugend(self):
        self.startTimer()
        self.msgLabel.setText(u'B3 Wohnungsbrand\nSt.-Anna-Berg 5\n' \
                u'Jugendherberge')
        lat_deg = 51.78317
        lon_deg = 6.10695
        route = getRoute(lat_deg, lon_deg, self.config)
        self.leftMap.setTarget(lat_deg, lon_deg, route)
        self.rightMap.setTarget(lat_deg, lon_deg, route)

    def exampleEngels(self):
        self.startTimer()
        self.msgLabel.setText(u'H1 Tierrettung\nEngelsstraße 5\n' \
                u'Katze auf Baum')
        lat_deg = 51.75065
        lon_deg = 6.11170
        route = getRoute(lat_deg, lon_deg, self.config)
        self.leftMap.setTarget(lat_deg, lon_deg, route)
        self.rightMap.setTarget(lat_deg, lon_deg, route)

    def exampleSack(self):
        self.startTimer()
        self.msgLabel.setText(u'B2 Garagenbrand\nSackstraße 173\n' \
                u'Kfz brennt unter Carport')
        lat_deg = 51.77190
        lon_deg = 6.12305
        route = getRoute(lat_deg, lon_deg, self.config)
        self.leftMap.setTarget(lat_deg, lon_deg, route)
        self.rightMap.setTarget(lat_deg, lon_deg, route)
