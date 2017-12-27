#!/usr/bin/python3
# -*- coding: utf-8 -*-

import sys
import configparser
import logging

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

    logger = logging.getLogger('alarmdisplay')

    logger.setLevel(logging.DEBUG)

    formatter = logging.Formatter('%(asctime)s %(message)s')

    streamHandler = logging.StreamHandler()
    streamHandler.setLevel(logging.DEBUG)
    streamHandler.setFormatter(formatter)
    logger.addHandler(streamHandler)

    logPath = 'alarmdisplay.log'
    fileHandler = logging.FileHandler(logPath)
    fileHandler.setLevel(logging.DEBUG)
    fileHandler.setFormatter(formatter)
    logger.addHandler(fileHandler)

    logger.info('Starting up...')

    app = PyQt5.QtWidgets.QApplication(sys.argv)

    mainWidget = MainWidget.MainWidget(config, logger)
    mainWidget.showMaximized()

    sys.exit(app.exec_())
