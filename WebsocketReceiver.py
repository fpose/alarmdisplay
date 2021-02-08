# -*- coding: utf-8 -*-

#-----------------------------------------------------------------------------
#
# Websocket Alarm Receiver
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

import websocket
import time
import json
import socket
import re

from PyQt5 import QtCore

#-----------------------------------------------------------------------------

def on_message(ws, message):
    ws.receiver.logger.info('Websocket received %s.', repr(message))
    try:
        msg_dict = json.loads(message)
    except:
        ws.receiver.logger.err('No valid json received.')
        return
    if 'auth' in msg_dict:
        ws.receiver.logger.info('Websocket authentication: %s.',
                msg_dict['auth'])
    if 'alarm' in msg_dict:
        ws.receiver.logger.info('Websocket received alarm.')
        ws.receiver.receivedAlarm.emit(msg_dict['alarm'])
    if 'status' in msg_dict:
        ws.receiver.logger.info('Websocket received status.')
        ws.receiver.receivedStatus.emit(msg_dict['status'])

def on_error(ws, error):
    ws.receiver.logger.info('Websocket error.')

def on_close(ws):
    ws.receiver.logger.info('Websocket closed.')

def on_open(ws):
    ws.receiver.logger.info('Websocket connected. Authenticating.')
    msg = {
            'host': ws.receiver.user,
            'auth_token': ws.receiver.auth_token
            }
    ws.send(json.dumps(msg))

#-----------------------------------------------------------------------------

class WebsocketReceiver(QtCore.QObject):

    receivedAlarm = QtCore.pyqtSignal(dict)
    receivedStatus = QtCore.pyqtSignal(dict)
    finished = QtCore.pyqtSignal()

    def __init__(self, config, logger):
        super(WebsocketReceiver, self).__init__()
        self.logger = logger
        self.url = config.get("websocket", "url", fallback = "")
        self.user = config.get("websocket", "user",
                fallback = socket.gethostname())
        self.auth_token = config.get("websocket", "auth_token", fallback = "")

        self.status = []

        if config.has_section('websocket'):
            statusRe = re.compile('status([0-9]+)')

            for key, host in config.items('websocket'):
                ma = statusRe.fullmatch(key)
                if not ma:
                    continue

                num = int(ma.group(1))
                address = config.get("websocket", key, fallback = '')
                name = config.get("websocket", 'name%u' % (num),
                        fallback = address)

                if not address:
                    continue

                self.logger.info('Adding status %s as %s / %s',
                        key, address, name)
                self.status.append((address, name))

    def receive(self):

        if not self.url:
            self.finished.emit()
            return

        self.logger.info('Websocket receiver thread started.')

        reconnectTimeout = 30

        ws = websocket.WebSocketApp(self.url,
                on_open = on_open,
                on_message = on_message,
                on_error = on_error,
                on_close = on_close)
        ws.receiver = self
        while True:
            self.logger.info('Connecting to %s...', self.url)
            ws.run_forever()
            self.logger.error('Websocket closed. Waiting to reconnect...')
            time.sleep(reconnectTimeout)

        self.logger.info('Receiver thread finished.')
        self.finished.emit()

#-----------------------------------------------------------------------------
