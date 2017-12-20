#!/usr/bin/python3
# -*- coding: utf-8 -*-

import sys
import PyQt5.QtWidgets

import MainWidget

if __name__ == '__main__':

    app = PyQt5.QtWidgets.QApplication(sys.argv)

    mainWidget = MainWidget.MainWidget()
    mainWidget.showMaximized()

    sys.exit(app.exec_())
