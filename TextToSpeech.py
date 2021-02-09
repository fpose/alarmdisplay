# -*- coding: utf-8 -*-

#-----------------------------------------------------------------------------
#
# TextToSpeech functions
#
# Copyright (C) 2021 Florian Pose
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
import tempfile
import os
from gtts import gTTS
from PyQt5.QtCore import *

#-----------------------------------------------------------------------------

class TextToSpeech(QObject):

    def __init__(self, config, logger):
        super(TextToSpeech, self).__init__()
        self.config = config
        self.logger = logger

        self.ttsDelay = self.config.getint("sound", "tts_delay",
                fallback = 30)
        self.repetitions = self.config.getint("sound", "tts_repetitions",
                fallback = 10)
        self.padFile = self.config.get("sound", "tts_pad_file",
                fallback = '')

        self.timer = QTimer(self)
        self.timer.setInterval(self.ttsDelay * 1000)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.play)

        self.thread = QThread()
        self.player = None
        self.file = None
        self.repetition = 0

    def clear(self):
        self.logger.info('Clearing TTS.')
        self.file = None

    def setText(self, text):
        self.logger.info('Generating TTS for %s', text)
        try:
            new_file = tempfile.NamedTemporaryFile(suffix = '.mp3')
        except:
            self.logger.error('Failed to generate temporary file for TTS.')
            return
        try:
            tts = gTTS(text = text, lang = 'de')
            tts.save(new_file.name)
        except:
            self.logger.error('TTS failed.')
            return
        self.file = new_file
        if self.padFile:
            try:
                pad_file = tempfile.NamedTemporaryFile(suffix = '.wav')
            except:
                self.logger.error( \
                        'Failed to generate temporary file for padding.')
                return
            cmd = 'sox ' + self.padFile + ' ' + new_file.name + ' ' \
                    + self.padFile + ' ' + pad_file.name
            self.logger.info('Executing %s', cmd)
            try:
                ret = os.system(cmd)
            except Exception as e:
                self.logger.error('Padding failed: %s', e)
                return
            if ret == 0:
                self.file = pad_file

    def start(self):
        self.repetition = 0
        if self.repetition < self.repetitions:
            self.timer.start()

    def play(self):
        if self.player:
            self.logger.info('TTS player still active.')
            return

        if self.file:
            self.logger.info('Starting TTS player...')
            self.player = Player(self.logger, self.file.name)
            self.player.finished.connect(self.playerFinished)
            self.player.finished.connect(self.thread.quit)
            self.player.moveToThread(self.thread)
            self.thread.started.connect(self.player.play)
            self.thread.start()

        self.repetition += 1
        if self.repetition < self.repetitions:
            self.timer.start()

    def playerFinished(self):
        self.logger.info('TTS player finished.')
        self.player = None

#-----------------------------------------------------------------------------

class Player(QObject):

    finished = pyqtSignal()

    def __init__(self, logger, soundFile):
        super(Player, self).__init__()
        self.logger = logger
        self.cmd = ['play', '-q', soundFile]

    def __del__(self):
        self.logger.info(u'Deleting TTS player')

    @pyqtSlot()
    def play(self):
        self.logger.info(u'Running %s', self.cmd)
        play = subprocess.Popen(self.cmd, stdout = subprocess.DEVNULL)
        play.wait()
        if play.returncode != 0:
            self.logger.error(u'TTS play command failed.')
        self.finished.emit()

#-----------------------------------------------------------------------------
