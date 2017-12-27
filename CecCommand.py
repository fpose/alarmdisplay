# -*- coding: utf-8 -*-

import subprocess

from PyQt5 import QtCore

class CecCommand(QtCore.QObject):

    start = QtCore.pyqtSignal(str)

    def __init__(self):
        super(CecCommand, self).__init__()
        self.start.connect(self.run)

    def switchOn(self):
        self.start.emit('on 0')

    @QtCore.pyqtSlot(str)
    def run(self, cecCommand):
        print('CEC command started:', cecCommand)

        args = ['cec-client', '-s', '-d', '1']

        try:
            cec = subprocess.Popen(args, stdin = subprocess.PIPE)
            cec.communicate(input = cecCommand.encode('UTF-8'))
        except OSError as e:
            print('CEC wakeup failed:', e)
        except:
            print('CEC wakeup failed.')

        print('CEC command finished.')
