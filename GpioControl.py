# -*- coding: utf-8 -*-

#-----------------------------------------------------------------------------
#
# GPIO control
#
# Copyright (C) 2020 Florian Pose
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

from PyQt5.QtCore import *

#-----------------------------------------------------------------------------

class GpioControl(QObject):

    def __init__(self, config, logger):
        super(GpioControl, self).__init__()
        self.config = config
        self.logger = logger

        self.channel = self.config.getint("gpio", "channel", fallback = -1)
        self.on_time = self.config.getint("gpio", "on_time", fallback = 1)
        self.delay_time = self.config.getint("gpio", "on_delay", fallback = 0)

        if self.channel < 0:
            return

        self.gpio = None

        try:
            import RPi.GPIO as GPIO
        except RuntimeError:
            self.logger.error("Error importing RPi.GPIO.")
            return

        self.gpio = GPIO

        self.logger.info("Initialising GPIO.")
        self.gpio.setmode(self.gpio.BOARD)
        self.gpio.setup(self.channel, self.gpio.OUT, initial = self.gpio.LOW)

        self.on_timer = QTimer(self)
        self.on_timer.setInterval(self.delay_time * 1000)
        self.on_timer.setSingleShot(True)
        self.on_timer.timeout.connect(self.switch_on)

        self.off_timer = QTimer(self)
        self.off_timer.setInterval(self.on_time * 1000)
        self.off_timer.setSingleShot(True)
        self.off_timer.timeout.connect(self.switch_off)

    def __del__(self):
        if self.channel < 0 or not self.gpio:
            return

        self.logger.info("Cleaning up GPIO.")
        self.gpio.output(self.channel, self.gpio.LOW)
        self.gpio.cleanup()

    def trigger(self):
        if self.channel < 0 or not self.gpio:
            return

        self.logger.info("Triggering GPIO switch-on timer.")
        self.on_timer.start()

    def switch_on(self):
        self.logger.info("Switching on GPIO %u." % self.channel)
        self.gpio.output(self.channel, self.gpio.HIGH)
        self.off_timer.start()

    def switch_off(self):
        if self.channel < 0 or not self.gpio:
            return

        self.logger.info("Switching off GPIO %u." % self.channel)
        self.gpio.output(self.channel, self.gpio.LOW)

#-----------------------------------------------------------------------------
