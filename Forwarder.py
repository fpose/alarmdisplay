#!/usr/bin/python -u
# vim: set fileencoding=utf-8 sw=4 expandtab ts=4 :

#-----------------------------------------------------------------------------
#
# Alarm Forwarder
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

import re

from PyQt5 import QtNetwork

#-----------------------------------------------------------------------------

class Forwarder:

    def __init__(self, config, logger):
        self.hosts = []
        self.config = config
        self.logger = logger

        if not config.has_section('forward'):
            return

        hostRe = re.compile('host([0-9]+)')

        for key, host in self.config.items('forward'):
            ma = hostRe.fullmatch(key)
            if not ma:
                self.logger.warning('Ignoring %s.', key)
                continue

            num = int(ma.group(1))
            port = self.config.getint("forward", "port%u" % (num),
                    fallback = 11211)

            self.logger.info('Adding forward %s as %s:%u', key, host, port)

            hostInfo = QtNetwork.QHostInfo.fromName(host)
            if not hostInfo.addresses():
                self.logger.warning('    Failed to find address.')
                continue

            addr = hostInfo.addresses()[0]
            self.hosts.append((host, addr, port))

            self.logger.info('   Added address %s.', addr.toString())

    def forward(self, alarm):
        data = None
        if alarm.source == 'pager':
            data = alarm.pager.encode('utf-8')
            socket = QtNetwork.QUdpSocket()

            for host, addr, port in self.hosts:
                self.logger.info('Forwarding to %s (%s:%u/udp)',
                        host, addr.toString(), port)
                socket.writeDatagram(data, addr, port)

        elif alarm.source == 'xml':
            data = alarm.xml # bytes
            socket = QtNetwork.QTcpSocket()

            for host, addr, port in self.hosts:
                self.logger.info('Forwarding to %s (%s:%u/tcp)',
                        host, addr.toString(), port)
                socket.connectToHost(addr, port)
                if not socket.waitForConnected(5000):
                    self.logger.error('Connection failed.')
                    continue
                socket.writeData(data)
                if not socket.waitForBytesWritten(5000):
                    self.logger.error('Writing to socket failed.')
                socket.close()

#-----------------------------------------------------------------------------
