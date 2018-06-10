#!/usr/bin/python3
# -*- coding: utf-8 -*-

#-----------------------------------------------------------------------------
#
# Alarm Display Entry Function
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

import sys
import configparser
import logging

import PyQt5.QtWidgets

import MainWidget

#-----------------------------------------------------------------------------

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

    logPath = config.get("display", "log_path",
            fallback = "/var/log/alarmdisplay.log")
    fileHandler = logging.FileHandler(logPath)
    fileHandler.setLevel(logging.DEBUG)
    fileHandler.setFormatter(formatter)
    logger.addHandler(fileHandler)

    logger.info('Starting up...')

    app = PyQt5.QtWidgets.QApplication(sys.argv)

    mainWidget = MainWidget.MainWidget(config, logger)
    mainWidget.showMaximized()

    sys.exit(app.exec_())

#-----------------------------------------------------------------------------
