#!/usr/bin/python3
# -*- coding: utf-8 -*-

#-----------------------------------------------------------------------------
#
# Unit tests
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
from Map import getRoute
from AlarmReport import AlarmReport
from Alarm import Alarm, EinsatzMittel

#-----------------------------------------------------------------------------

configFiles = [
    '/etc/alarmdisplay.conf',
    '~/.alarmdisplay.conf',
    'alarmdisplay.conf'
    ]
if len(sys.argv) > 1:
    configFiles.extend(sys.argv[1:])
config = configparser.ConfigParser()
config.read(configFiles)

logger = logging.getLogger('alarmdisplay')
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s %(message)s')
streamHandler = logging.StreamHandler()
streamHandler.setLevel(logging.DEBUG)
streamHandler.setFormatter(formatter)
logger.addHandler(streamHandler)

app = PyQt5.QtWidgets.QApplication(sys.argv)

report = AlarmReport(config, logger)

logger.info('Load')
alarm = Alarm(config)
alarm.load('alarm_db/2018-05-12-19-53-24.dme', logger)
alarm2 = Alarm(config)
alarm2.load('alarm_db/2018-05-12-19-53-26.xml', logger)
alarm.merge(alarm2)

logger.info('Route')
route = getRoute(alarm.lat, alarm.lon, config, logger)

logger.info('Generate')
report.generate(alarm, route)

#-----------------------------------------------------------------------------
