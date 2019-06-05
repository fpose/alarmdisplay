# -*- coding: utf-8 -*-

#-----------------------------------------------------------------------------
#
# Sound functions
#
# Copyright (C) 2019 Florian Pose
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

import subprocess
from PyQt5.QtCore import *

#-----------------------------------------------------------------------------

class Sound(QObject):

    def __init__(self, config, logger):
        super(Sound, self).__init__()
        self.config = config
        self.logger = logger

        self.alarmFile = self.config.get("sound", "alarm", fallback = '')

        self.timer = QTimer(self)
        self.timer.setInterval( \
            self.config.getint("sound", "delay", fallback = 20) \
            * 1000)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.play)

        self.thread = QThread()
        self.player = None

    def start(self):
        if self.alarmFile:
            self.timer.start()

    def play(self):
        if self.player:
            self.logger.info('Player still active.')
            return

        self.logger.info('Starting player...')
        self.player = Player(self.logger, self.alarmFile)
        self.player.finished.connect(self.playerFinished)
        self.player.finished.connect(self.thread.quit)
        self.player.moveToThread(self.thread)
        self.thread.started.connect(self.player.play)
        self.thread.start()

    def playerFinished(self):
        self.logger.info('Player finished.')
        self.player = None

#-----------------------------------------------------------------------------

class Player(QObject):

    finished = pyqtSignal()

    def __init__(self, logger, soundFile):
        super(Player, self).__init__()
        self.logger = logger
        self.cmd = ['aplay', soundFile]

    def __del__(self):
        self.logger.info(u'Deleting player')

    @pyqtSlot()
    def play(self):
        self.logger.info(u'Running %s', self.cmd)
        play = subprocess.Popen(self.cmd, stdout = subprocess.DEVNULL)
        play.wait()
        if play.returncode != 0:
            self.logger.error(u'Play command failed.')
        self.finished.emit()

#-----------------------------------------------------------------------------
