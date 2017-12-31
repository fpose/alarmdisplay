# -*- coding: utf-8 -*-

import os
import math
import subprocess

from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

from MapWidget import MapWidget
from RouteWidget import RouteWidget
from Map import getRoute
from AlarmReceiver import AlarmReceiver
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

        self.alarmDict = {}
        self.currentAlarm = None

        self.elapsedTimer = QTimer(self)
        self.elapsedTimer.setInterval(1000)
        self.elapsedTimer.setSingleShot(False)
        self.elapsedTimer.timeout.connect(self.elapsedTimeout)
        self.alarmDateTime = None

        self.simTimer = QTimer(self)
        self.simTimer.setInterval(20000)
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
        self.titleLabel.setStyleSheet("""
            color: white;
            font-size: 80px;
            background-color: rgb(120, 0, 0);
            padding: 10px;
            """)
        titleLayout.addWidget(self.titleLabel, 1)

        verLayout.addLayout(titleLayout, 0)

        locationLayout = QHBoxLayout(self)
        locationLayout.setSpacing(0)

        self.locationSymbolLabel = QLabel(self)
        self.locationSymbolLabel.setStyleSheet("""
            padding: 10px;
            """)
        locationLayout.addWidget(self.locationSymbolLabel, 0)

        self.locationLabel = QLabel(self)
        self.locationLabel.setStyleSheet("""
            padding: 10px;
            """)
        locationLayout.addWidget(self.locationLabel, 1)

        verLayout.addLayout(locationLayout, 0)

        attentionLayout = QHBoxLayout(self)
        attentionLayout.setSpacing(0)

        self.attentionSymbolLabel = QLabel(self)
        self.attentionSymbolLabel.setStyleSheet("""
            padding: 10px;
            """)
        attentionLayout.addWidget(self.attentionSymbolLabel, 0)

        self.attentionLabel = QLabel(self)
        self.attentionLabel.setStyleSheet("""
            padding: 10px;
            font-size: 40px;
            """)
        attentionLayout.addWidget(self.attentionLabel, 1)

        verLayout.addLayout(attentionLayout, 0)

        horLayout = QHBoxLayout(self)
        verLayout.addLayout(horLayout, 2)

        self.leftMap = MapWidget(self, self.config, self.logger)
        self.leftMap.setStyleSheet("""
            font-size: 40px;
            """)
        horLayout.addWidget(self.leftMap, 3)

        centerLayout = QVBoxLayout(self)
        horLayout.addLayout(centerLayout, 1)

        logoLabel = QLabel(self)
        logo = self.config.get("display", "logo", fallback = None)
        if logo:
            styleSheet = 'image: url({0});'.format( \
                    os.path.join(self.imageDir, logo))
            logoLabel.setStyleSheet(styleSheet)
        centerLayout.addWidget(logoLabel)

        self.timerLabel = QLabel(self)
        self.timerLabel.setAlignment(Qt.AlignCenter)
        centerLayout.addWidget(self.timerLabel)

        self.rightMap = RouteWidget(self, self.config, self.logger)
        self.rightMap.setStyleSheet("""
            font-size: 40px;
            """)
        horLayout.addWidget(self.rightMap, 3)

        self.setLayout(verLayout)

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

        self.thread = QThread()
        self.alarmReceiver = AlarmReceiver(self.logger)
        self.alarmReceiver.receivedAlarm.connect(self.receivedAlarm)
        self.alarmReceiver.moveToThread(self.thread)
        self.alarmReceiver.finished.connect(self.thread.quit)
        self.thread.started.connect(self.alarmReceiver.receive)
        self.thread.start()

        self.cecThread = QThread()
        self.cecThread.start()

        self.cecCommand = CecCommand(self.logger)
        self.cecCommand.moveToThread(self.cecThread)

        self.report = AlarmReport(self.config, self.logger)

        self.logger.info('Setup finished.')

    def receivedAlarm(self, pagerStr):
        self.logger.info('Received alarm: %s', repr(pagerStr))

        self.startTimer()

        alarm = Alarm(self.config)
        alarm.fromPager(pagerStr, self.logger)

        self.processAlarm(alarm)

    def processAlarm(self, alarm):
        self.titleLabel.setText(alarm.title())

        image = None
        alarmType = alarm.art.upper()
        if alarmType == 'B':
            image = 'feuer.svg'
        if alarmType == 'H':
            image = 'hilfe.svg'
        if image:
            pixmap = QPixmap(os.path.join(self.imageDir, image))
        else:
            pixmap = QPixmap()
        self.symbolLabel.setPixmap(pixmap)

        self.locationLabel.setText(alarm.location())
        if self.locationLabel.text():
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
        self.logger.debug(event.size())

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
        self.startTimer()

        alarm = Alarm(self.config)
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
        self.startTimer()

        alarm = Alarm(self.config)
        alarm.art = 'H'
        alarm.stichwort = '1'
        alarm.diagnose = 'Tierrettung'
        alarm.strasse = 'Engelsstraße'
        alarm.hausnummer = '5'
        alarm.ort = 'Kleve'
        alarm.besonderheit = 'Katze auf Baum'
        alarm.lat = 51.75065
        alarm.lon = 6.11170

        self.processAlarm(alarm)

    def exampleSack(self):
        self.startTimer()

        alarm = Alarm(self.config)
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

        pagerStr = '21-12-17 11:55:10 LG Reichswalde Geb{udesteuerung #K01;N5175638E0611815; *40000*B2 Kaminbrand**Kleve*Reichswalde*Wolfsgraben*11**'

        alarm = Alarm(self.config)
        alarm.fromPager(pagerStr, self.logger)

        self.alarmDict[alarm.number] = alarm

        if self.currentAlarm and self.currentAlarm.number != alarm.number:
            self.startTimer()
        self.currentAlarm = alarm

        self.processAlarm(alarm)

    def exampleWolfsgrabenMail(self):

        number = '40000'

        if number in self.alarmDict:
            alarm = self.alarmDict[number]
            self.logger.info('Writing into existing alarm %s.', number)
        else:
            alarm = Alarm(self.config)
            self.alarmDict[number] = alarm
            self.logger.info('Generating new alarm %s.', number)

        alarm.art = 'B'
        alarm.stichwort = '2'
        alarm.diagnose = 'Kaminbrand'
        alarm.strasse = 'Wolfsgraben'
        alarm.hausnummer = '11'
        alarm.ort = 'Kleve'
        alarm.lat = 51.75638
        alarm.lon = 6.11815
        alarm.meldender = 'Pose'
        alarm.number = str(number)
        em = EinsatzMittel()
        em.org = 'FW'
        em.ort = 'KLV'
        em.zusatz = '05'
        em.typ = 'LF10'
        em.kennung = '1'
        alarm.einsatzmittel.append(em)

        if self.currentAlarm and self.currentAlarm.number != alarm.number:
            self.startTimer()
        self.currentAlarm = alarm

        self.processAlarm(alarm)

    def exampleWaldfee(self):
        pagerStr = r'16-12-17 18:55:10 LG Reichswalde Geb{udesteuerung #K01;N5173170E0606900; *57274*H1 Hilfeleistung*Von draussen vom Walde komm ich her*Kleve*Reichswalde*Grunewaldstrasse***Waldweg C'

        self.startTimer()

        alarm = Alarm(self.config)
        alarm.fromPager(pagerStr, self.logger)

        self.processAlarm(alarm)
