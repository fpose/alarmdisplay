# vim: set fileencoding=utf-8 sw=4 expandtab ts=4 :

#-----------------------------------------------------------------------------
#
# Imap Monitor
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

import time
from imapclient import IMAPClient
import email

from PyQt5 import QtCore

#-----------------------------------------------------------------------------

class ImapMonitor(QtCore.QObject):

    receivedAlarm = QtCore.pyqtSignal(bytes)
    finished = QtCore.pyqtSignal()

#-----------------------------------------------------------------------------

    def __init__(self, config, logger):
        super(ImapMonitor, self).__init__()
        self.logger = logger
        self.run = True

        self.imapHost = config.get('email', 'imap_host', fallback = None)
        self.imapUser = config.get('email', 'imap_user', fallback = None)
        self.imapPass = config.get('email', 'imap_pass', fallback = None)

        if not self.imapHost or not self.imapUser or not self.imapPass:
            self.run = False

#-----------------------------------------------------------------------------

    def start(self):
        self.logger.info(u'Started IMAP monitor.')

        while self.run:
            try:
                self.imapCycle()
            except:
                self.logger.error('IMAP cycle failed:', exc_info = True)
            if self.run:
                time.sleep(10)

        self.logger.info(u'IMAP monitor finished.')
        self.finished.emit()

#-----------------------------------------------------------------------------

    def imapCycle(self):
        self.logger.info('Connecting to %s...', repr(self.imapHost))
        imap = IMAPClient(self.imapHost)

        self.logger.info('Logging in...')
        imap.login(self.imapUser, self.imapPass)

        self.logger.info('Selecting INBOX...')
        ret = imap.select_folder("INBOX")
        num = ret[b'EXISTS']
        self.logger.info(u'Selected mailbox with %s messages.', num)

        self.logger.info(u'Starting IMAP idle mode.')
        imap.idle()

        while self.run:
            try:
                # Wait for an IDLE response
                responses = imap.idle_check(timeout = 60 * 5)
                # TODO: process response and stay in idle mode
            except:
                self.logger.error('IMAP error:', exc_info = True)
                break

            imap.idle_done()
            self.fetchNewMails(imap)
            imap.idle()

        imap.close()
        imap.logout()

#-----------------------------------------------------------------------------

    def fetchNewMails(self, imap):
        messageIds = imap.search('UNSEEN')

        if len(messageIds) == 0:
            return

        self.logger.info(u'Fetching messages %s...', messageIds)
        messages = imap.fetch(messageIds, 'RFC822')

        for messageId in messageIds:
            imapMessage = messages[messageId]

            try:
                imap.set_flags(messageId, '\\Seen')
                self.logger.info(u'Marked message as seen.')
            except:
                self.logger.error(u'Failed to mark message as seen:',
                        exc_info = True)

            content = imapMessage[b'RFC822']

            msg = email.message_from_bytes(content)

            if 'From' in msg:
                self.logger.info(u'From: %s', msg['From'])

            if 'subject' in msg:
                self.logger.info(u'Subject: %s', msg['subject'])

            for part in msg.walk():
                if part.get_content_maintype() == 'multipart':
                    continue
                if part.get('Content-Disposition') is None:
                    continue

                fileName = part.get_filename()

                if fileName == None or not fileName.endswith('xml'):
                    continue

                xmlContent = part.get_payload(decode = True)
                self.receivedAlarm.emit(xmlContent)

#-----------------------------------------------------------------------------
