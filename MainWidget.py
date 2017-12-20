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

        msgLabel = QLabel(self)
        msgLabel.resize(self.width(), 300)
        msgLabel.setText(u'H1 Tierrettung\nEngelsstraße 5\nKatze auf Baum')
        msgLabel.setStyleSheet("""
            color: white;
            background-color: rgb(80, 0, 0);
            """)
        verLayout.addWidget(msgLabel, 1)

        horLayout = QHBoxLayout(self)
        verLayout.addLayout(horLayout, 2)

        leftMap = MapWidget(self, 17)
        leftMap.setStyleSheet("""
            background-color: rgb(80, 80, 0);
            """)
        horLayout.addWidget(leftMap, 2)

        centerLayout = QVBoxLayout(self)
        horLayout.addLayout(centerLayout, 1)

        logoLabel = QLabel(self)
        logoLabel.setStyleSheet('image: url(images/wappen-reichswalde.png);')
        centerLayout.addWidget(logoLabel)

        timerLabel = QLabel(self)
        timerLabel.setText('4:59')
        timerLabel.setAlignment(Qt.AlignCenter)
        centerLayout.addWidget(timerLabel)

        rightMap = RouteWidget(self)
        rightMap.setStyleSheet("""
            background-color: rgb(0, 80, 80);
            """)
        horLayout.addWidget(rightMap, 2)

        self.setLayout(verLayout)

        # Jugendherberge
        lat_deg = 51.78317
        lon_deg = 6.10695
        msgLabel.setText(u'B3 Wohnungsbrand\nSt.-Anna-Berg 5\nJugendherberge')

        # # Engelsstraße 5
        # lat_deg = 51.75065
        # lon_deg = 6.11170
        # msgLabel.setText(u'H1 Tierrettung\nEngelsstraße 5\nKatze auf Baum')

        leftMap.setTarget(lat_deg, lon_deg)
        rightMap.setTarget(lat_deg, lon_deg)
