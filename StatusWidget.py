# -*- coding: utf-8 -*-

#-----------------------------------------------------------------------------
#
# Status Widget
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

import os
import datetime
import re
import subprocess

from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtSvg import QSvgRenderer

#-----------------------------------------------------------------------------

class StatusWidget(QWidget):

    def __init__(self, main):
        super(StatusWidget, self).__init__()

        self.main = main
        config = main.config
        self.logger = main.logger

        imageDir = config.get("display", "image_dir", fallback = "images")
        self.statusPixmaps = {}
        for s in (1, 2, 3, 4, 6):
            path = os.path.join(imageDir, 'status%u.svg' % (s))
            try:
                renderer = QSvgRenderer(path)
                pixmap = QPixmap(48, 48);
                pixmap.fill(Qt.transparent);
                painter = QPainter(pixmap);
                renderer.render(painter, QRectF(pixmap.rect()));
            except:
                self.logger.warning('Failed to load status image %s.', path,
                        exc_info = True)
                continue
            self.statusPixmaps[s] = pixmap

        layout = QHBoxLayout(self)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)

        self.labelDict = {}
        self.animationDict = {}

        index = 0
        if config.has_section('status'):
            addressRe = re.compile('address([0-9]+)')

            for key, address in config.items('status'):
                ma = addressRe.fullmatch(key)
                if not ma or not address:
                    continue

                num = int(ma.group(1))
                name = config.get("status", 'name%u' % (num),
                        fallback = address)
                image = config.get("status", 'image%u' % (num),
                        fallback = '')

                label = QLabel(self)
                layout.addWidget(label, 1)

                if image:
                    path = os.path.join(imageDir, image)
                    try:
                        pixmap = QPixmap(path)
                        label = QLabel(self)
                        label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
                        label.setStyleSheet("""
                            padding: 10px;
                            background-color: #202040;
                            """)
                        layout.addWidget(label, 0)
                        label.setPixmap(pixmap)
                    except:
                        self.logger.warning('Failed to load image %s.', path,
                                exc_info = True)

                label = QLabel(self)
                layout.addWidget(label, 1)
                label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
                label.setStyleSheet("""
                    font-size: 25px;
                    background-color: #202040;
                    """)
                label.setText(name)

                label = AnimatedLabel(self)
                layout.addWidget(label, 0)
                self.labelDict[address] = label

                animation = QPropertyAnimation(label, b'color')
                animation.setStartValue(QColor('#202040'))
                animation.setKeyValueAt(0.5, QColor(Qt.white))
                animation.setEndValue(QColor('#202040'))
                animation.setDuration(1000)
                animation.setLoopCount(10)
                animation.setEasingCurve(QEasingCurve.OutInQuad);
                self.animationDict[address] = animation

        label = QLabel(self)
        layout.addWidget(label, 1)

        self.soundFile = config.get("sound", "status", fallback = '')
        self.thread = QThread()
        self.player = None

    def setStatus(self, status):
        address = status['address']
        if address in self.labelDict:
            label = self.labelDict[address]
            s = status['status']
            if s in self.statusPixmaps:
                label.setPixmap(self.statusPixmaps[s])
                label.setText('')
            else:
                label.setPixmap(QPixmap())
                label.setText(str(s))
            self.play()
        if address in self.animationDict:
            self.animationDict[address].start()

    def play(self):
        if not self.soundFile:
            return
        if self.player:
            self.logger.info('Status player still active.')
            return

        self.logger.info('Starting status player...')
        self.player = Player(self.logger, self.soundFile)
        self.player.finished.connect(self.playerFinished)
        self.player.finished.connect(self.thread.quit)
        self.player.moveToThread(self.thread)
        self.thread.started.connect(self.player.play)
        self.thread.start()

    def playerFinished(self):
        self.logger.info('Status player finished.')
        self.player = None

#-----------------------------------------------------------------------------

class AnimatedLabel(QLabel):

    def __init__(self, parent):
        super(AnimatedLabel, self).__init__(parent)

    def setColor(self, color):
        s = """
        font-size: 40px;
        padding: 10px;
        background-color: #%08x;""" % (color.rgba())
        self.setStyleSheet(s)

    def getColor(self):
        return Qt.black

    color = pyqtProperty(QColor, getColor, setColor)

#-----------------------------------------------------------------------------

class Player(QObject):

    finished = pyqtSignal()

    def __init__(self, logger, soundFile):
        super(Player, self).__init__()
        self.logger = logger
        self.cmd = ['play', '-q', soundFile]

    def __del__(self):
        self.logger.info(u'Deleting player')

    @pyqtSlot()
    def play(self):
        self.logger.info(u'Running %s', self.cmd)
        try:
            play = subprocess.Popen(self.cmd, stdout = subprocess.DEVNULL)
            play.wait()
            if play.returncode != 0:
                self.logger.error(u'Play command failed.')
        except:
            self.logger.error('Failed to execute player.', exc_info = True)
        self.finished.emit()

#-----------------------------------------------------------------------------
