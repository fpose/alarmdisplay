#!/usr/bin/python3
# -*- coding: utf-8 -*-

#-----------------------------------------------------------------------------
#
# Test for speech output
#
# Copyright (C) 2020 Florian Pose
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
import os
import configparser
import logging
from Alarm import Alarm
from gtts import gTTS

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

path = config.get("db", "path", fallback = None)
if not path:
    sys.exit(1)

paths = [os.path.join(path, entry) for entry in os.listdir(path)]
paths = [path for path in paths if \
        (path.endswith('.dme') or \
        path.endswith('.xml') or \
        path.endswith('.json')) and \
        os.path.isfile(path)]
paths = sorted(paths, reverse = True)

alarms = []
index = 0
while len(paths) > 0:
    path = paths[0]
    paths = paths[1:]

    alarm = Alarm(config)
    try:
        alarm.load(path)
    except Exception as e:
        logger('Failed to load %s: %s', path, e)
        continue

    if alarm.fallbackStr:
        # ignore incomplete or invalid alarms in history
        continue

    if len(alarms) and alarms[-1].matches(alarm):
        alarms[-1].merge(alarm)
    else:
        alarms.append(alarm)
        index += 1

for alarm in alarms:
    text = alarm.spoken()
    print(text)
    tts = gTTS(text = text, lang="de")
    tts.save('text.mp3')
    os.system('play text.mp3')

#-----------------------------------------------------------------------------
