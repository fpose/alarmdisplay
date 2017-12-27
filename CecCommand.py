# -*- coding: utf-8 -*-

import subprocess

from PyQt5 import QtCore

class CecCommand(QtCore.QObject):

    start = QtCore.pyqtSignal(str)

    def __init__(self, logger):
        super(CecCommand, self).__init__()
        self.logger = logger
        self.start.connect(self.run)

    def switchOn(self):
        self.start.emit('on 0')

    @QtCore.pyqtSlot(str)
    def run(self, cecCommand):
        self.logger.info('CEC command started: %s', cecCommand)

        args = ['cec-client', '-s', '-d', '1']

        try:
            cec = subprocess.Popen(args, stdin = subprocess.PIPE)
            cec.communicate(input = cecCommand.encode('UTF-8'))
        except OSError as e:
            self.logger.error('CEC wakeup failed: %s', e)
        except:
            self.logger.error('CEC wakeup failed.')

        self.logger.info('CEC command finished.')
