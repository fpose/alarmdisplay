#!/usr/bin/python3
# -*- coding: utf-8 -*-

import sys

from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

if __name__ == '__main__':

    app = QApplication(sys.argv)

    mainWidget = QWidget()
    mainWidget.resize(1920, 1080)
    mainWidget.move(0, 0)
    mainWidget.setWindowTitle('Alarmdisplay')
    mainWidget.setStyleSheet("""
        font-size: 70px;
        background-color: rgb(0, 34, 44);
        color: rgb(2, 203, 255);
        font-family: "DejaVu Sans";
        """)

    verLayout = QVBoxLayout(mainWidget)
    verLayout.setContentsMargins(0, 0, 0, 0)

    msgLabel = QLabel(mainWidget)
    msgLabel.resize(mainWidget.width(), 300)
    msgLabel.setText(u'H1 Tierrettung\nEngelsstraße 5\nKatze auf Baum')
    msgLabel.setStyleSheet("""
        color: white;
        background-color: rgb(80, 0, 0);
        """)
    verLayout.addWidget(msgLabel, 1)

    horLayout = QHBoxLayout(mainWidget)
    verLayout.addLayout(horLayout, 2)

    lmapLabel = QLabel(mainWidget)
    lmapLabel.setStyleSheet("""
        background-color: rgb(80, 80, 0);
        """)
    horLayout.addWidget(lmapLabel, 2)

    centerLayout = QVBoxLayout(mainWidget)
    horLayout.addLayout(centerLayout, 1)

    logoLabel = QLabel(mainWidget)
    logoLabel.setStyleSheet('image: url(images/wappen-reichswalde.png);')
    centerLayout.addWidget(logoLabel)

    timerLabel = QLabel(mainWidget)
    timerLabel.setText('4:59')
    timerLabel.setAlignment(Qt.AlignCenter)
    centerLayout.addWidget(timerLabel)

    rmapLabel = QLabel(mainWidget)
    rmapLabel.setStyleSheet("""
        background-color: rgb(0, 80, 80);
        """)
    horLayout.addWidget(rmapLabel, 2)

    mainWidget.setLayout(verLayout)

    mainWidget.show()

    sys.exit(app.exec_())
