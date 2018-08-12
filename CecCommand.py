# -*- coding: utf-8 -*-

#-----------------------------------------------------------------------------
#
# CEC Command
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

import subprocess

from PyQt5 import QtCore

#-----------------------------------------------------------------------------

class CecCommand(QtCore.QObject):

    start = QtCore.pyqtSignal(str)

    def __init__(self, logger):
        super(CecCommand, self).__init__()
        self.logger = logger
        self.start.connect(self.run)

    def switchOn(self):
        self.start.emit('on 0')

    def switchOff(self):
        self.start.emit('standby 0')

    @QtCore.pyqtSlot(str)
    def run(self, cecCommand):
        self.logger.info('CEC command started: %s', cecCommand)

        args = ['cec-client', '-s', '-d', '1']

        try:
            cec = subprocess.Popen(args, stdin = subprocess.PIPE)
            cec.communicate(input = cecCommand.encode('UTF-8'))
        except OSError as e:
            self.logger.error('CEC command failed: %s', e)
        except:
            self.logger.error('CEC command failed.')

        self.logger.info('CEC command finished.')

#-----------------------------------------------------------------------------
