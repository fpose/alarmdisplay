# -*- coding: utf-8 -*-

import serial

from PyQt5 import QtCore

class AlarmReceiver(QtCore.QObject):

    receivedAlarm = QtCore.pyqtSignal(str)
    finished = QtCore.pyqtSignal()

    asciiExceptions = {
        '[': 'Ä', # guessed
        '\\': 'Ö', # 27-11-10 04:53:29 \\lspur
        ']': 'Ü', # guessed
        '{': 'ä', # Preamble Geb{udesteuerung
        '|': 'ö', # 01-03-17 18:34:31 G|rrestrasse
        '}': 'ü', # 27-11-10 00:43:31 Baum droht auf Fahrbahn zu St}rzen
        '~': 'ß' # 27-11-10 04:53:29 Dorfstra~e
    }

    def __init__(self, logger):
        super(AlarmReceiver, self).__init__()
        self.logger = logger

    def receive(self):
        self.logger.info('Receiver thread started.')

        try:
            ser = serial.Serial(
                port = '/dev/ttyUSB0',
                baudrate = 9600,
                parity = serial.PARITY_NONE,
                stopbits = serial.STOPBITS_ONE,
                bytesize = serial.EIGHTBITS,
                timeout = None)
        except:
            self.logger.error('Failed to open port!')
            self.finished.emit()
            return

        self.logger.info('Connected to %s', ser.portstr)

        run = True
        data = b''
        bytesReceived = 0

        while run:
            c = ser.read()
            bytesReceived += 1
            if c == b'\x00':
                pagerStr = data.decode('latin1')
                pagerStr = self.decode(pagerStr)
                self.receivedAlarm.emit(pagerStr)
                data = b''
            else:
                data += c

        ser.close()
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
