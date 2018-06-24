# -*- coding: utf-8 -*-

#-----------------------------------------------------------------------------
#
# Main Widget
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

import os
import math
import subprocess
import datetime

from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

from IdleWidget import IdleWidget
from AlarmWidget import AlarmWidget
from Map import getRoute
from AlarmReceiver import AlarmReceiver
from ImapMonitor import ImapMonitor
from SocketListener import SocketListener
from AlarmReport import AlarmReport
from CecCommand import CecCommand
from Alarm import Alarm, EinsatzMittel

#-----------------------------------------------------------------------------

class MainWidget(QWidget):

    def __init__(self, config, logger):
        super(MainWidget, self).__init__()

        self.config = config
        self.logger = logger

        self.imageDir = self.config.get("display", "image_dir",
                fallback = "images")

        self.alarm = None
        self.route = ([], None, None)
        self.seenPager = False
        self.seenXml = False
        self.reportDone = False
        self.alarmDateTime = None

        self.reportTimer = QTimer(self)
        self.reportTimer.setInterval( \
            self.config.getint("report", "timeout", fallback = 20) * 1000)
        self.reportTimer.setSingleShot(True)
        self.reportTimer.timeout.connect(self.generateReport)

        self.simTimer = QTimer(self)
        self.simTimer.setInterval(10000)
        self.simTimer.setSingleShot(True)
        self.simTimer.timeout.connect(self.simTimeout)
        #self.simTimer.start()

        self.idleTimer = QTimer(self)
        idleTimeout = self.config.getint("display", "idle_timeout",
                fallback = 30)
        self.idleTimer.setInterval(idleTimeout * 60000)
        self.idleTimer.setSingleShot(True)
        self.idleTimer.timeout.connect(self.idleTimeout)

        self.screenTimer = QTimer(self)
        screenTimeout = self.config.getint("display", "screen_timeout",
                fallback = 0)
        self.screenTimer.setInterval(screenTimeout * 60000)
        self.screenTimer.setSingleShot(True)
        self.screenTimer.timeout.connect(self.screenTimeout)
        if self.screenTimer.interval() > 0:
            self.screenTimer.start()

        self.logger.info('Setting up X server...')

        subprocess.call(['xset', 's', 'off'])
        subprocess.call(['xset', 's', 'noblank'])
        subprocess.call(['xset', 's', '0', '0'])
        subprocess.call(['xset', '-dpms'])

        self.move(0, 0)
        self.resize(1920, 1080)

        self.setWindowTitle('Alarmdisplay')

        self.setStyleSheet("""
            font-size: 60px;
            background-color: rgb(0, 34, 44);
            color: rgb(2, 203, 255);
            font-family: "DejaVu Sans";
            """)

        # Sub-widgets --------------------------------------------------------

        layout = QVBoxLayout(self)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)

        self.stackedWidget = QStackedWidget(self)
        layout.addWidget(self.stackedWidget)

        self.idleWidget = IdleWidget(self)
        self.idleWidget.start()
        self.stackedWidget.addWidget(self.idleWidget)

        self.alarmWidget = AlarmWidget(self)
        self.stackedWidget.addWidget(self.alarmWidget)

        # Shortcuts ----------------------------------------------------------

        action = QAction(self)
        action.setShortcut(QKeySequence("1"))
        action.setShortcutContext(Qt.ApplicationShortcut)
        action.triggered.connect(self.exampleJugend)
        self.addAction(action)

        action = QAction(self)
        action.setShortcut(QKeySequence("2"))
        action.setShortcutContext(Qt.ApplicationShortcut)
        action.triggered.connect(self.exampleEngels)
        self.addAction(action)

        action = QAction(self)
        action.setShortcut(QKeySequence("3"))
        action.setShortcutContext(Qt.ApplicationShortcut)
        action.triggered.connect(self.exampleSack)
        self.addAction(action)

        action = QAction(self)
        action.setShortcut(QKeySequence("4"))
        action.setShortcutContext(Qt.ApplicationShortcut)
        action.triggered.connect(self.exampleWolfsgrabenPager)
        self.addAction(action)

        action = QAction(self)
        action.setShortcut(QKeySequence("5"))
        action.setShortcutContext(Qt.ApplicationShortcut)
        action.triggered.connect(self.exampleWolfsgrabenMail)
        self.addAction(action)

        action = QAction(self)
        action.setShortcut(QKeySequence("6"))
        action.setShortcutContext(Qt.ApplicationShortcut)
        action.triggered.connect(self.exampleWald)
        self.addAction(action)

        action = QAction(self)
        action.setShortcut(QKeySequence("7"))
        action.setShortcutContext(Qt.ApplicationShortcut)
        action.triggered.connect(self.exampleStadtwerkePager)
        self.addAction(action)

        action = QAction(self)
        action.setShortcut(QKeySequence("8"))
        action.setShortcutContext(Qt.ApplicationShortcut)
        action.triggered.connect(self.exampleLebenshilfe)
        self.addAction(action)

        action = QAction(self)
        action.setShortcut(QKeySequence("9"))
        action.setShortcutContext(Qt.ApplicationShortcut)
        action.triggered.connect(self.exampleHuissen)
        self.addAction(action)

        # Threads ------------------------------------------------------------

        self.receiverThread = QThread()
        self.alarmReceiver = AlarmReceiver(self.logger)
        self.alarmReceiver.receivedAlarm.connect(self.receivedPagerAlarm)
        self.alarmReceiver.moveToThread(self.receiverThread)
        self.alarmReceiver.finished.connect(self.receiverThread.quit)
        self.receiverThread.started.connect(self.alarmReceiver.receive)
        self.receiverThread.start()

        self.imapThread = QThread()
        self.imapMonitor = ImapMonitor(self.config, self.logger)
        self.imapMonitor.receivedAlarm.connect(self.receivedXmlAlarm)
        self.imapMonitor.moveToThread(self.imapThread)
        self.imapMonitor.finished.connect(self.imapThread.quit)
        self.imapThread.started.connect(self.imapMonitor.start)
        self.imapThread.start()

        self.socketListener = SocketListener(self.logger)
        self.socketListener.receivedAlarm.connect(self.receivedPagerAlarm)

        self.cecThread = QThread()
        self.cecThread.start()

        self.cecCommand = CecCommand(self.logger)
        self.cecCommand.moveToThread(self.cecThread)

        self.report = AlarmReport(self.config, self.logger)

        self.logger.info('Setup finished.')

    def receivedPagerAlarm(self, pagerStr):
        self.logger.info('Received alarm: %s', repr(pagerStr))

        alarm = Alarm(self.config)
        alarm.fromPager(pagerStr, self.logger)

        self.processAlarm(alarm)

    def receivedXmlAlarm(self, xmlContent):
        self.logger.info('Received XML alarm.')

        alarm = Alarm(self.config)

        try:
            alarm.fromXml(xmlContent, self.logger)
        except:
            self.logger.error('Failed to parse XML:', exc_info = True)
            return

        self.processAlarm(alarm)

    def processAlarm(self, newAlarm):
        try:
            newAlarm.save()
        except:
            self.logger.error('Failed to save alarm:', exc_info = True)

        if not self.alarm or not self.alarm.matches(newAlarm):
            self.logger.info("Processing new alarm.")
            self.startTimer()
            self.alarm = newAlarm
            self.route = ([], None, None)
            self.seenPager = False
            self.seenXml = False
            self.reportDone = False
            self.reportTimer.start()
            self.report.wakeupPrinter()
        else:
            self.alarm.merge(newAlarm, self.logger)

        if newAlarm.source == 'pager':
            self.seenPager = True
        elif newAlarm.source == 'xml':
            self.seenXml = True

        self.idleWidget.stop()
        self.stackedWidget.setCurrentWidget(self.alarmWidget)
        self.alarmWidget.processAlarm(self.alarm)

        QApplication.processEvents()

        self.alarmWidget.setRoute(self.route)

        if not self.route[0]:
            QApplication.processEvents()
            self.logger.info('Route query...')
            self.route = getRoute(self.alarm.lat, self.alarm.lon, self.config,
                    self.logger)
            self.alarmWidget.setRoute(self.route)
            self.logger.info('Route ready.')

        if self.seenPager and self.seenXml and not self.reportDone:
            self.reportTimer.stop()
            QApplication.processEvents()
            self.generateReport()

    def generateReport(self):
        self.logger.info('Report...')
        self.report.generate(self.alarm, self.route)
        self.reportDone = True
        self.logger.info('Finished.')

    def resizeEvent(self, event):
        self.logger.debug('Resizing main window to %u x %u.',
            event.size().width(), event.size().height())

    def startTimer(self):
        self.alarmDateTime = QDateTime.currentDateTime()
        if self.idleTimer.interval() > 0:
            self.idleTimer.start()
        if self.screenTimer.interval() > 0:
            self.screenTimer.start()
        self.alarmWidget.startTimer(self.alarmDateTime)
        self.logger.info(u'Alarm at %s', self.alarmDateTime)
        self.cecCommand.switchOn()

    def simTimeout(self):
        self.exampleJugend()

    def idleTimeout(self):
        self.stackedWidget.setCurrentWidget(self.idleWidget)
        self.idleWidget.start()

    def screenTimeout(self):
        self.cecCommand.switchOff()

    def exampleJugend(self):
        alarm = Alarm(self.config)
        alarm.number = '40001'
        alarm.datetime = datetime.datetime.now()
        alarm.art = 'B'
        alarm.stichwort = '3'
        alarm.diagnose = 'Wohnungsbrand'
        alarm.strasse = 'St.-Anna-Berg'
        alarm.ort = 'Kleve'
        alarm.hausnummer = '5'
        alarm.objektname = 'Jugendherberge'
        alarm.besonderheit = 'lt. Betreiber 34 Personen gemeldet'
        alarm.objektnummer = 'KLV 02/140'
        alarm.lat = 51.78317
        alarm.lon = 6.10695

        self.processAlarm(alarm)

    def exampleEngels(self):
        alarm = Alarm(self.config)
        alarm.number = '40002'
        alarm.datetime = datetime.datetime.now()
        alarm.art = 'H'
        alarm.stichwort = '1'
        alarm.diagnose = 'Tierrettung'
        alarm.ort = 'Kleve'
        alarm.ortsteil = 'Reichswalde'
        alarm.strasse = 'Engelsstraße'
        alarm.hausnummer = '5'
        alarm.ort = 'Kleve'
        alarm.besonderheit = 'Katze auf Baum'
        alarm.sondersignal = '0'
        alarm.lat = 51.75065
        alarm.lon = 6.11170

        self.processAlarm(alarm)

    def exampleSack(self):
        self.logger.info('Example Sackstrasse')

        alarm = Alarm(self.config)
        alarm.number = '40003'
        alarm.datetime = datetime.datetime.now()
        alarm.art = 'B'
        alarm.stichwort = '2'
        alarm.diagnose = 'Garagenbrand'
        alarm.strasse = 'Sackstraße'
        alarm.hausnummer = '173'
        alarm.ort = 'Kleve'
        alarm.besonderheit = 'Kfz brennt unter Carport'
        alarm.lat = 51.77190
        alarm.lon = 6.12305

        self.processAlarm(alarm)

    def exampleWolfsgrabenPager(self):

        pagerStr = '21-12-17 11:55:10 LG Reichswalde Geb{udesteuerung' + \
            ' #K01;N5175638E0611815; *40004*B2 Kaminbrand**Kleve*' + \
            'Reichswalde*Wolfsgraben*11**'

        alarm = Alarm(self.config)
        alarm.fromPager(pagerStr, self.logger)

        self.processAlarm(alarm)

    def exampleWolfsgrabenMail(self):

        alarm = Alarm(self.config)
        alarm.datetime = datetime.datetime.now()
        alarm.art = 'B'
        alarm.stichwort = '2'
        alarm.diagnose = 'Kaminbrand'
        alarm.besonderheit = 'keine Personen mehr im Gebäude'
        alarm.ortsteil = 'Reichswalde'
        alarm.strasse = 'Wolfsgraben'
        alarm.hausnummer = '11'
        alarm.ort = 'Kleve'
        alarm.lat = 51.75638
        alarm.lon = 6.11815
        alarm.meldender = 'Müller'
        alarm.rufnummer = '0179 555 364532'
        alarm.number = '1170040004'
        alarm.sondersignal = '1'
        em = EinsatzMittel()
        em.org = 'FW'
        em.ort = 'KLV'
        em.zusatz = '05'
        em.typ = 'LF10'
        em.kennung = '1'
        alarm.einsatzmittel.append(em)
        em = EinsatzMittel()
        em.org = 'FW'
        em.ort = 'KLV'
        em.zusatz = '02'
        em.typ = 'LF20'
        em.kennung = '1'
        alarm.einsatzmittel.append(em)

        self.processAlarm(alarm)

    def exampleWald(self):
        pagerStr = '16-12-17 18:55:10 LG Reichswalde Gebäudesteuerung' + \
            ' #K01;N5173170E0606900; *40005*H1 Hilfeleistung*' + \
            'Eichhörnchen auf Baum*Kleve*Reichswalde*' + \
            'Grunewaldstrasse***Waldweg C'

        alarm = Alarm(self.config)
        alarm.fromPager(pagerStr, self.logger)

        self.processAlarm(alarm)

    def exampleStadtwerkePager(self):

        pagerStr = '21-12-17 11:55:10 LG Reichswalde Gebäudesteuerung' + \
            ' #K01;N5179473E0613985; *40006*B3 Brand Bürogebäude*' + \
            'Stadtwerke Kleve GmbH*Kleve*Kleve*Flutstraße*36**'

        alarm = Alarm(self.config)
        alarm.fromPager(pagerStr, self.logger)

        self.processAlarm(alarm)

    def exampleLebenshilfe(self):

        pagerStr = '22-03-17 10:12:38 LG Reichswalde  Gebäudesteuerung' + \
            ' #K01;N5177287E0611253;*40007*B2 Brandmeldeanlage 2' + \
            ' **Kleve*Materborn*Dorfstrasse*27*KLV 02/103' + \
            '*Materborner Allee - Saalstrasse'

        alarm = Alarm(self.config)
        alarm.fromPager(pagerStr, self.logger)

        self.processAlarm(alarm)

    def exampleHuissen(self):

        f = open("alarm_db/2018-06-24-04-13-11.xml", "rb")
        xmlContent = f.read()
        f.close()

        alarm = Alarm(self.config)

        try:
            alarm.fromXml(xmlContent, self.logger)
        except:
            self.logger.error('Failed to parse XML:', exc_info = True)
            return

        self.processAlarm(alarm)

#-----------------------------------------------------------------------------
