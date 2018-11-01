# -*- coding: utf-8 -*-

#-----------------------------------------------------------------------------
#
# Socket listener
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

from PyQt5 import QtCore
from PyQt5 import QtNetwork

#-----------------------------------------------------------------------------

class SocketListener(QtCore.QObject):

    pagerAlarm = QtCore.pyqtSignal(str)
    xmlAlarm = QtCore.pyqtSignal(bytes)

    def __init__(self, logger):
        super(SocketListener, self).__init__()
        self.logger = logger

        self.udpSocket = QtNetwork.QUdpSocket(self)
        self.udpSocket.bind(QtNetwork.QHostAddress.Any, 11211)
        self.udpSocket.readyRead.connect(self.readUdpSocket)

        self.tcpServer = QtNetwork.QTcpServer(self)
        self.tcpServer.listen(QtNetwork.QHostAddress.Any, 11211)
        self.tcpServer.newConnection.connect(self.tcpConnection)

        self.tcpConnection = None
        self.tcpData = b''

    def readUdpSocket(self):
        self.logger.info('Datagram received.')
        while self.udpSocket.hasPendingDatagrams():
            size = self.udpSocket.pendingDatagramSize()
            (data, host, port) = self.udpSocket.readDatagram(size)
            self.logger.info("Received from %s:%i", host.toString(), port)
            pagerStr = data.decode('utf-8')
            self.pagerAlarm.emit(pagerStr)

    def tcpConnection(self):
        self.logger.info('New connection from TCP client.')
        if self.tcpConnection:
            self.tcpConnection.disconnectFromHost()
        self.tcpConnection = self.tcpServer.nextPendingConnection()
        self.tcpConnection.readyRead.connect(self.tcpReadyRead)
        self.tcpConnection.disconnected.connect(self.tcpDisconnected)
        self.tcpConnection.error.connect(self.tcpError)
        self.tcpData = b''

    def tcpReadyRead(self):
        self.tcpData += self.tcpConnection.readAll().data()

    def tcpDisconnected(self):
        self.xmlAlarm.emit(self.tcpData)
        self.logger.info('Closing connection to TCP client.')
        self.tcpConnection = None
        self.tcpData = b''

    def tcpError(self):
        self.tcpConnection.close()

#-----------------------------------------------------------------------------
