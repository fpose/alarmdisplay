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

from AlarmReceiver import AlarmReceiver

from PyQt5 import QtCore
from PyQt5 import QtNetwork

#-----------------------------------------------------------------------------

class SocketListener(QtCore.QObject):

    receivedAlarm = QtCore.pyqtSignal(str)

    def __init__(self, logger):
        super(SocketListener, self).__init__()
        self.logger = logger

        self.socket = QtNetwork.QUdpSocket(self)
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

#-----------------------------------------------------------------------------
