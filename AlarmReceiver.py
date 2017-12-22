# -*- coding: utf-8 -*-

import serial

from PyQt5 import QtCore

class AlarmReceiver(QtCore.QObject):

    receivedAlarm = QtCore.pyqtSignal(bytes)
    finished = QtCore.pyqtSignal()

    def receive(self):
        print('Thread started.')

        ser = serial.Serial(
            port = '/dev/ttyUSB0',
            baudrate = 9600,
            parity = serial.PARITY_NONE,
            stopbits = serial.STOPBITS_ONE,
            bytesize = serial.EIGHTBITS,
            timeout = None)

        print('Connected to', ser.portstr)

        run = True
        data = b''
        bytesReceived = 0

        while run:
            c = ser.read()
            #print(repr(c))
            bytesReceived += 1
            if c == b'\x00':
                #print('Complete: ', repr(data), bytesReceived)
                self.receivedAlarm.emit(data)
                data = b''
            else:
                data += c

        ser.close()
        self.finished.emit()
