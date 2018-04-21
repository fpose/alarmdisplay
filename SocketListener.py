# -*- coding: utf-8 -*-

from AlarmReceiver import AlarmReceiver

from PyQt5 import QtCore
from PyQt5 import QtNetwork

class SocketListener(QtCore.QObject):

    receivedAlarm = QtCore.pyqtSignal(str)

    def __init__(self, logger):
        super(SocketListener, self).__init__()
        self.logger = logger

        self.socket = QtNetwork.QUdpSocket(self);
        self.socket.bind(QtNetwork.QHostAddress.Any, 11211)
        self.socket.readyRead.connect(self.readSocket)

    def readSocket(self):
        self.logger.info('Datagram received.')
        while self.socket.hasPendingDatagrams():
            size = self.socket.pendingDatagramSize()
            (data, host, port) = self.socket.readDatagram(size)
            self.logger.info("Received from %s:%i", host.toString(), port)
            pagerStr = data.decode('utf-8')
            self.receivedAlarm.emit(pagerStr)
