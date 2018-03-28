# vim: set fileencoding=utf-8 sw=4 expandtab ts=4 :

#-----------------------------------------------------------------------------

import time
import imaplib
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
        imap = imaplib.IMAP4_SSL(self.imapHost)

        self.logger.info('Logging in...')
        imap.login(self.imapUser, self.imapPass)

        self.logger.info('Selecting INBOX...')
        ret = imap.select("INBOX")
        num = ret[1][0]
        self.logger.info(u'Mailbox mit %s Nachrichten ausgewählt.', num)

        while self.run:
            try:
                time.sleep(5)
            except IOError:
                pass

            (retcode, response) = imap.recent()

            if len(response) != 1:
                self.logger.error(u'Ungültige Antwort: %s', len(response))
                break

            if response[0] == None or int(response[0]) == 0:
                continue

            self.fetchNewMails(imap)

        imap.close()
        imap.logout()

#-----------------------------------------------------------------------------

    def fetchNewMails(self, imap):
        (retcode, messages) = imap.search(None, '(UNSEEN)')

        for num in messages[0].split():

            self.logger.info(u'Hole Nachricht %s...', num)
            result, data = imap.fetch(num, '(RFC822)')

            try:
                imap.store(num, '+FLAGS', '\\Seen')
                self.logger.info(u'Nachricht als gelesen markiert.')
            except:
                self.logger.error(u'Konnte Nachricht nicht als gelesen' + \
                    ' markieren:', exc_info = True)

            for response_part in data:
                if not isinstance(response_part, tuple):
                    continue

                msg = email.message_from_bytes(response_part[1])

                self.logger.info(u'Von: %s', msg['From'])

                subject = u''
                if 'subject' in msg:
                    subject = msg['subject']
                self.logger.info(u'Betreff: %s', subject)

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

#----------------------------------------------------------------------------
