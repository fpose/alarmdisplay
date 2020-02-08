# -*- coding: utf-8 -*-

#-----------------------------------------------------------------------------
#
# Alarm Receiver
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

import serial
import time

from PyQt5 import QtCore

#-----------------------------------------------------------------------------

class AlarmReceiver(QtCore.QObject):

    receivedAlarm = QtCore.pyqtSignal(str)
    finished = QtCore.pyqtSignal()
    errorMessage = QtCore.pyqtSignal(str)

    asciiExceptions = {
        '[': 'Ä', # guessed
        '\\': 'Ö', # 27-11-10 04:53:29 \\lspur
        ']': 'Ü', # guessed
        '{': 'ä', # Preamble Geb{udesteuerung
        '|': 'ö', # 01-03-17 18:34:31 G|rrestrasse
        '}': 'ü', # 27-11-10 00:43:31 Baum droht auf Fahrbahn zu St}rzen
        '~': 'ß' # 27-11-10 04:53:29 Dorfstra~e
    }

    def __init__(self, config, logger):
        super(AlarmReceiver, self).__init__()
        self.logger = logger
        self.port = config.get("pager", "device", fallback = "/dev/ttyUSB0")
        self.connected = True

    def setConnected(self, newState):
        if self.connected and not newState:
            self.errorMessage.emit('Keine Verbindung zum DME!')
        if not self.connected and newState:
            self.errorMessage.emit('')
        self.connected = newState

    def receive(self):

        if not self.port:
            self.finished.emit()
            return

        self.logger.info('Receiver thread started.')

        reconnectTimeout = 30

        while True:
            try:
                ser = serial.serial_for_url(
                        'alt://%s?class=PosixPollSerial' % (self.port),
                        baudrate = 9600,
                        parity = serial.PARITY_NONE,
                        stopbits = serial.STOPBITS_ONE,
                        bytesize = serial.EIGHTBITS,
                        timeout = 10.0)
            except:
                self.setConnected(False)
                time.sleep(reconnectTimeout)
                continue

            self.logger.info('Connected to %s', ser.portstr)
            self.setConnected(True)

            data = b''
            bytesReceived = 0

            while True:
                try:
                    c = ser.read()
                except serial.serialutil.SerialException as e:
                    self.logger.error('Serial port disconnected:')
                    self.logger.error(e)
                    break
                bytesReceived += 1
                if c == b'\x00':
                    pagerStr = data.decode('latin1')
                    pagerStr = self.decode(pagerStr)
                    self.receivedAlarm.emit(pagerStr)
                    data = b''
                else:
                    data += c

            ser.close()
            self.setConnected(False)
            time.sleep(reconnectTimeout)

        self.logger.info('Receiver thread finished.')
        self.finished.emit()

    @classmethod
    def decode(cls, data):
        ret = ''
        for c in data:
            if c in cls.asciiExceptions:
                ret += cls.asciiExceptions[c]
            else:
                ret += c
        return ret

#-----------------------------------------------------------------------------
