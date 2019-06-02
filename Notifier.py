#!/usr/bin/python -u
# vim: set fileencoding=utf-8 sw=4 expandtab ts=4 :

#-----------------------------------------------------------------------------
#
# Notifier
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

import socket

from PyQt5.QtCore import QUrl, QUrlQuery
from PyQt5.QtNetwork import *

#-----------------------------------------------------------------------------

class Notifier:

    def __init__(self, config, logger):
        self.config = config
        self.logger = logger

        self.networkAccessManager = QNetworkAccessManager()
        self.networkAccessManager.finished.connect(self.handle_response)

        self.url = self.config.get("notify", "url", fallback = "")
        self.host_name = socket.gethostname()

        if not self.url:
            return

        self.logger.info('Notifying %s.', self.url)

    def pager(self, pager_string):

        if not self.url:
            return

        # FIXME manually replace semicolon
        pager_string = pager_string.replace(";", "%3B")

        query = QUrlQuery()
        query.addQueryItem("host_name", self.host_name)
        query.addQueryItem("pager_string", pager_string)
        data = query.toString(QUrl.FullyEncoded).encode('utf-8')

        self.logger.info("Notifing %s...", self.url)
        req = QNetworkRequest(QUrl(self.url))
        req.setHeader(QNetworkRequest.ContentTypeHeader,
                'application/x-www-form-urlencoded')
        reply = self.networkAccessManager.post(req, data)

    def handle_response(self, reply):
        req = reply.request()
        err = reply.error()
        if err == QNetworkReply.NoError:
            self.logger.info("Notification successful.")
        else:
            self.logger.error("Notification failed: %s", reply.errorString())
        reply.deleteLater()

#-----------------------------------------------------------------------------
