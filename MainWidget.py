# -*- coding: utf-8 -*-

import os
import math
import subprocess
import datetime

from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

from MapWidget import MapWidget
from RouteWidget import RouteWidget
from Map import getRoute
from AlarmReceiver import AlarmReceiver
from ImapMonitor import ImapMonitor
from SocketListener import SocketListener
from AlarmReport import AlarmReport
from CecCommand import CecCommand
from Alarm import Alarm, EinsatzMittel

class MainWidget(QWidget):

    def __init__(self, config, logger):
        super(MainWidget, self).__init__()

        self.config = config
        self.logger = logger

        self.imageDir = self.config.get("display", "image_dir",
                fallback = "images")

        self.currentAlarm = None

        self.elapsedTimer = QTimer(self)
        self.elapsedTimer.setInterval(1000)
        self.elapsedTimer.setSingleShot(False)
        self.elapsedTimer.timeout.connect(self.elapsedTimeout)
        self.alarmDateTime = None

        self.simTimer = QTimer(self)
        self.simTimer.setInterval(10000)
        self.simTimer.setSingleShot(True)
        self.simTimer.timeout.connect(self.simTimeout)
        #self.simTimer.start()

        self.screenTimer = QTimer(self)
        screenTimeout = self.config.getint("display", "screen_timeout",
                fallback = 0)
        self.screenTimer.setInterval(screenTimeout * 60000)
        self.screenTimer.setSingleShot(True)
        self.screenTimer.timeout.connect(self.screenTimeout)

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

        verLayout = QVBoxLayout(self)
        verLayout.setSpacing(0)
        verLayout.setContentsMargins(0, 0, 0, 0)

        titleLayout = QHBoxLayout(self)
        titleLayout.setSpacing(0)

        self.symbolLabel = QLabel(self)
        self.symbolLabel.setStyleSheet("""
            background-color: rgb(120, 0, 0);
            padding: 10px;
            """)
        titleLayout.addWidget(self.symbolLabel, 0)

        self.titleLabel = QLabel(self)
        self.titleLabel.setSizePolicy(QSizePolicy.Ignored,
                QSizePolicy.Preferred)
        self.titleLabel.setStyleSheet("""
            color: white;
            font-size: 80px;
            background-color: rgb(120, 0, 0);
            padding: 10px;
            """)
        titleLayout.addWidget(self.titleLabel, 1)

        self.timerLabel = QLabel(self)
        self.timerLabel.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.timerLabel.setStyleSheet("""
            color: white;
            background-color: rgb(120, 0, 0);
            padding: 10px;
            """)
        titleLayout.addWidget(self.timerLabel, 0)

        verLayout.addLayout(titleLayout, 0)

        locationLayout = QHBoxLayout(self)
        locationLayout.setSpacing(0)

        self.locationSymbolLabel = QLabel(self)
        self.locationSymbolLabel.setStyleSheet("""
            padding: 10px;
            """)
        locationLayout.addWidget(self.locationSymbolLabel, 0)

        innerLocationLayout = QVBoxLayout(self)
        innerLocationLayout.setSpacing(0)

        self.locationLabel = QLabel(self)
        self.locationLabel.setIndent(0)
        self.locationLabel.setSizePolicy(QSizePolicy.Ignored,
                QSizePolicy.Preferred)
        self.locationLabel.setStyleSheet("""
            padding: 10px;
            """)
        innerLocationLayout.addWidget(self.locationLabel, 1)

        self.locationHintLabel = QLabel(self)
        self.locationHintLabel.setIndent(0)
        self.locationHintLabel.setSizePolicy(QSizePolicy.Ignored,
                QSizePolicy.Preferred)
        self.locationHintLabel.setStyleSheet("""
            padding: 10px;
            font-size: 40px;
            """)
        innerLocationLayout.addWidget(self.locationHintLabel, 1)

        locationLayout.addLayout(innerLocationLayout, 1)

        verLayout.addLayout(locationLayout, 0)

        # Attention row ------------------------------------------------------

        attentionLayout = QHBoxLayout(self)
        attentionLayout.setSpacing(0)
        verLayout.addLayout(attentionLayout, 0)

        self.attentionSymbolLabel = QLabel(self)
        self.attentionSymbolLabel.setStyleSheet("""
            padding: 10px;
            """)
        attentionLayout.addWidget(self.attentionSymbolLabel, 0)

        self.attentionLabel = QLabel(self)
        self.attentionLabel.setIndent(0)
        self.attentionLabel.setSizePolicy(QSizePolicy.Ignored,
                QSizePolicy.Preferred)
        self.attentionLabel.setStyleSheet("""
            padding: 10px;
            font-size: 40px;
            """)
        attentionLayout.addWidget(self.attentionLabel, 1)

        self.callerSymbolLabel = QLabel(self)
        self.callerSymbolLabel.setStyleSheet("""
            padding: 10px;
            """)
        attentionLayout.addWidget(self.callerSymbolLabel, 0)

        self.callerLabel = QLabel(self)
        self.callerLabel.setIndent(0)
        self.callerLabel.setSizePolicy(QSizePolicy.Ignored,
                QSizePolicy.Preferred)
        self.callerLabel.setStyleSheet("""
            padding: 10px;
            font-size: 40px;
            """)
        attentionLayout.addWidget(self.callerLabel, 1)

        # Maps ---------------------------------------------------------------

        horLayout = QHBoxLayout(self)
        verLayout.addLayout(horLayout, 2)

        self.leftMap = MapWidget(self, self.config, self.logger)
        self.leftMap.setStyleSheet("""
            font-size: 40px;
            """)
        horLayout.addWidget(self.leftMap, 3)

        self.rightMap = RouteWidget(self, self.config, self.logger)
        self.rightMap.setStyleSheet("""
            font-size: 40px;
            """)
        horLayout.addWidget(self.rightMap, 3)

        self.setLayout(verLayout)

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
        action.triggered.connect(self.exampleWaldfee)
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

    def processAlarm(self, alarm):
        if not self.currentAlarm or not self.currentAlarm.matches(alarm):
            self.logger.info("Processing new alarm.")
            self.startTimer()
            self.currentAlarm = alarm
            self.report.wakeupPrinter()
        else:
            self.currentAlarm.merge(alarm, self.logger)
            alarm = self.currentAlarm
            # FIXME further processing if all alarm sources are present

        self.titleLabel.setText(alarm.title())

        image = alarm.imageBase()
        if image:
            image += '.svg'
            pixmap = QPixmap(os.path.join(self.imageDir, image))
        else:
            pixmap = QPixmap()
        self.symbolLabel.setPixmap(pixmap)

        self.locationLabel.setText(alarm.location())
        self.locationHintLabel.setText(alarm.ortshinweis)
        if self.locationHintLabel.text():
            self.locationHintLabel.show()
        else:
            self.locationHintLabel.hide()

        if self.locationLabel.text() or self.locationHintLabel.text():
            pixmap = QPixmap(os.path.join(self.imageDir, 'go-home.svg'))
        else:
            pixmap = QPixmap()
        self.locationSymbolLabel.setPixmap(pixmap)

        self.attentionLabel.setText(alarm.attention())
        if self.attentionLabel.text():
            pixmap = QPixmap(os.path.join(self.imageDir,
                        'emblem-important.svg'))
            self.attentionSymbolLabel.setPixmap(pixmap)
            self.attentionSymbolLabel.show()
            self.attentionLabel.show()
        else:
            pixmap = QPixmap()
            self.attentionSymbolLabel.setPixmap(pixmap)
            self.attentionSymbolLabel.hide()
            self.attentionLabel.hide()

        self.callerLabel.setText(alarm.callerInfo())
        if self.callerLabel.text():
            pixmap = QPixmap(os.path.join(self.imageDir,
                        'caller.svg'))
            self.callerSymbolLabel.setPixmap(pixmap)
            self.callerSymbolLabel.show()
            self.callerLabel.show()
        else:
            pixmap = QPixmap()
            self.callerSymbolLabel.setPixmap(pixmap)
            self.callerSymbolLabel.hide()
            self.callerLabel.hide()

        self.leftMap.invalidate()
        self.leftMap.setObjectPlan(alarm.objektnummer)

        self.rightMap.invalidate()

        QApplication.processEvents()

        route = ([], None, None)
        self.logger.info('Destination map...')
        self.leftMap.setTarget(alarm.lat, alarm.lon, route)
        self.logger.info('Route map...')
        self.rightMap.setTarget(alarm.lat, alarm.lon, route)
        self.logger.info('Maps ready.')
        QApplication.processEvents()

        self.logger.info('Route query...')
        route = getRoute(alarm.lat, alarm.lon, self.config, self.logger)
        self.logger.info('Destination map...')
        self.leftMap.setTarget(alarm.lat, alarm.lon, route)
        self.logger.info('Route map...')
        self.rightMap.setTarget(alarm.lat, alarm.lon, route)
        self.logger.info('Route ready.')
        QApplication.processEvents()

        self.logger.info('Report...')
        self.report.generate(alarm, route)
        self.logger.info('Finished.')

    def resizeEvent(self, event):
        self.logger.debug('Resizing main window to %u x %u.',
            event.size().width(), event.size().height())

    def startTimer(self):
        self.alarmDateTime = QDateTime.currentDateTime()
        self.logger.debug('Screen timeout: %u ms',
                self.screenTimer.interval())
        if self.screenTimer.interval() > 0:
            self.screenTimer.start()
        self.elapsedTimer.start()
        self.elapsedTimeout()
        self.logger.info(u'Alarm at %s', self.alarmDateTime)
        self.cecCommand.switchOn()

    def elapsedTimeout(self):
        now = QDateTime.currentDateTime()
        diffMs = self.alarmDateTime.msecsTo(now)
        seconds = math.floor(diffMs / 1000)
        hours = math.floor(seconds / 3600)
        seconds -= hours * 3600
        minutes = math.floor(seconds / 60)
        seconds -= minutes * 60
        if hours > 0:
            text = u'%u:%02u:%02u' % (hours, minutes, seconds)
        else:
            text = u'%u:%02u' % (minutes, seconds)
        self.timerLabel.setText(text)

    def simTimeout(self):
        self.exampleJugend()

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
        alarm.meldender = 'Pose'
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

    def exampleWaldfee(self):
        pagerStr = '16-12-17 18:55:10 LG Reichswalde Geb{udesteuerung' + \
            ' #K01;N5173170E0606900; *40005*H1 Hilfeleistung*' + \
            'Eichhörnchen auf Baum*Kleve*Reichswalde**' + \
            'Grunewaldstrasse***Waldweg C'

        alarm = Alarm(self.config)
        alarm.fromPager(pagerStr, self.logger)

        self.processAlarm(alarm)

    def exampleStadtwerkePager(self):

        pagerStr = '21-12-17 11:55:10 LG Reichswalde Geb{udesteuerung' + \
            ' #K01;N5179473E0613985; *40006*B3 Brand Bürogebäude*' + \
            'Stadtwerke Kleve GmbH*Kleve*Kleve*Flutstraße*36**'

        alarm = Alarm(self.config)
        alarm.fromPager(pagerStr, self.logger)

        self.processAlarm(alarm)

    def exampleLebenshilfe(self):

        pagerStr = '22-03-17 10:12:38 LG Reichswalde  Geb{udesteuerung' + \
            ' #K01;N5177287E0611253;*40007*B2 Brandmeldeanlage 2' + \
            ' **Kleve*Materborn*Dorfstrasse*27*KLV 02/103' + \
            '*Materborner Allee - Saalstrasse'

        alarm = Alarm(self.config)
        alarm.fromPager(pagerStr, self.logger)

        self.processAlarm(alarm)

