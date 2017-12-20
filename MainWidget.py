# -*- coding: utf-8 -*-

from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

from MapWidget import MapWidget
from RouteWidget import RouteWidget

class MainWidget(QWidget):

    def __init__(self):
        super(MainWidget, self).__init__()

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
        self.msgLabel.resize(self.width(), 300)
        self.msgLabel.setText(u'H1 Tierrettung\nEngelsstraße 5\nKatze auf Baum')
        self.msgLabel.setStyleSheet("""
            color: white;
            background-color: rgb(80, 0, 0);
            """)
        verLayout.addWidget(self.msgLabel, 1)

        horLayout = QHBoxLayout(self)
        verLayout.addLayout(horLayout, 2)

        self.leftMap = MapWidget(self, 17)
        self.leftMap.setStyleSheet("""
            background-color: rgb(80, 80, 0);
            """)
        horLayout.addWidget(self.leftMap, 2)

        centerLayout = QVBoxLayout(self)
        horLayout.addLayout(centerLayout, 1)

        logoLabel = QLabel(self)
        logoLabel.setStyleSheet('image: url(images/wappen-reichswalde.png);')
        centerLayout.addWidget(logoLabel)

        timerLabel = QLabel(self)
        timerLabel.setText('4:59')
        timerLabel.setAlignment(Qt.AlignCenter)
        centerLayout.addWidget(timerLabel)

        self.rightMap = RouteWidget(self)
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

    def exampleJugend(self):
        self.msgLabel.setText(u'B3 Wohnungsbrand\nSt.-Anna-Berg 5\n' \
                u'Jugendherberge')
        lat_deg = 51.78317
        lon_deg = 6.10695
        self.leftMap.setTarget(lat_deg, lon_deg)
        self.rightMap.setTarget(lat_deg, lon_deg)

    def exampleEngels(self):
        self.msgLabel.setText(u'H1 Tierrettung\nEngelsstraße 5\n' \
                u'Katze auf Baum')
        lat_deg = 51.75065
        lon_deg = 6.11170
        self.leftMap.setTarget(lat_deg, lon_deg)
        self.rightMap.setTarget(lat_deg, lon_deg)

