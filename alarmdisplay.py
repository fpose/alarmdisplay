#!/usr/bin/python3
# -*- coding: utf-8 -*-

import sys
import configparser

import PyQt5.QtWidgets

import MainWidget

if __name__ == '__main__':

    configFiles = [
        '/etc/alarmdisplay.conf',
        '~/.alarmdisplay.conf',
        'alarmdisplay.conf'
        ]
    if len(sys.argv) > 1:
        configFiles.extend(sys.argv[1:])
    print(configFiles)
    config = configparser.ConfigParser()
    config.read(configFiles)

    app = PyQt5.QtWidgets.QApplication(sys.argv)

    mainWidget = MainWidget.MainWidget(config)
    mainWidget.showMaximized()

    sys.exit(app.exec_())
