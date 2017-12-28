# -*- coding: utf-8 -*-

import os
import math
import subprocess
import re

from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

from MapWidget import MapWidget
from RouteWidget import RouteWidget
from Map import getRoute
from AlarmReceiver import AlarmReceiver
from AlarmReport import AlarmReport
from CecCommand import CecCommand

class MainWidget(QWidget):

    def __init__(self, config, logger):
        super(MainWidget, self).__init__()

        self.config = config
        self.logger = logger

        self.imageDir = self.config.get("display", "image_dir",
                fallback = "images")

        self.alarmActive = False
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

        self.msgLabel = QLabel(self)
        self.msgLabel.setStyleSheet("""
            padding: 20px;
            """)
        verLayout.addWidget(self.msgLabel, 1)

        horLayout = QHBoxLayout(self)
        verLayout.addLayout(horLayout, 2)

        self.leftMap = MapWidget(self, self.config, self.logger)
        self.leftMap.setStyleSheet("""
            background-color: rgb(80, 80, 0);
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
            background-color: rgb(0, 80, 80);
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

    def receivedAlarm(self, alarm):
        self.logger.info('Received alarm: %s', repr(alarm))

        alarm = alarm.decode('latin1')

        # '16-12-17 18:55:10 LG Reichswalde Geb{udesteuerung
        # #K01;N5174110E0608130; *57274*H1 Hilfeleistung*
        # Holla die Waldfee*Kleve*Reichswalde*Grunewaldstrasse*
        # *KLV 03/124*Hinweis

        #  1) Datum/Uhrzeit TT-MM-YY HH:MM:SS
        #  2) Einheit, Funktion (RIC)
        #  3+4) Koordinaten
        #  5) Einsatznummer
        #  6) Einsatzart und Stichwort
        #  7) Diagnose und Eskalationsstufe
        #  8) Hinweis (Freitext)
        #  9) Stadt
        # 10) Ortsteil
        # 11) Straße
        # 12) Hausnummer
        # 13) Objektplan
        # 14) Ortshinweis
        regex = \
                '(\d+-\d+-\d+ \d+:\d+:\d+)\s+' \
                '(.*)\s*' \
                '#K01;N(\d+)E(\d+);\s*\*' \
                '(.*)\*' \
                '(..)\s+' \
                '(.*)\*' \
                '(.*)\*' \
                '(.*)\*' \
                '(.*)\*' \
                '(.*)\*' \
                '(.*)\*' \
                '(.*)\*' \
                '(.*)'
        alarmRe = re.compile(regex)
        ma = alarmRe.match(alarm)
        if not ma:
            self.logger.warn('Alarmtext nicht erkannt!')
            return

        self.logger.debug(ma.groups())
        datetime = QDateTime.fromString(ma.group(1), 'dd-MM-yy hh:mm:ss')
        datetime = datetime.addYears(100)
        self.logger.debug('Date %s', datetime)
        einheit = ma.group(2).strip()
        coord = ma.group(3)
        coord = coord[:2] + '.' + coord[2:]
        lat_deg = float(coord)
        coord = ma.group(4)
        coord = coord[:2] + '.' + coord[2:]
        lon_deg = float(coord)
        self.logger.debug('Coordinates: lon=%f lat=%f', lon_deg, lat_deg)
        text = ma.group(6) + ' ' + ma.group(7)
        address = ma.group(11)
        housenumber = ma.group(12)
        if housenumber:
            address += ' ' + housenumber
        ortshinweis = ma.group(14)
        if ortshinweis:
            address += ' (' + ortshinweis + ')'
        hinweis = ma.group(8)

        self.logger.info('Dispatching alarm...')
        self.startTimer()
        self.titleLabel.setText(text)
        msg = address
        if hinweis:
            msg += '\n' + hinweis
        self.msgLabel.setText(msg)
        self.leftMap.invalidate()
        self.leftMap.setObjectPlan(ma.group(13))
        self.rightMap.invalidate()

        self.processAlarm(lat_deg, lon_deg)

    def processAlarm(self, lat_deg, lon_deg):
        image = None
        if self.titleLabel.text():
            alarmType = self.titleLabel.text()[0].upper()
            if alarmType == 'B':
                image = 'feuer.svg'
            if alarmType == 'H':
                image = 'hilfe.svg'

        if image:
            pixmap = QPixmap(os.path.join(self.imageDir, image))
        else:
            pixmap = QPixmap()
        self.symbolLabel.setPixmap(pixmap)
        QApplication.processEvents()

        route = ([], None, None)
        self.logger.info('Destination map...')
        self.leftMap.setTarget(lat_deg, lon_deg, route)
        self.logger.info('Route map...')
        self.rightMap.setTarget(lat_deg, lon_deg, route)
        self.logger.info('Maps ready.')
        QApplication.processEvents()

        self.logger.info('Route query...')
        route = getRoute(lat_deg, lon_deg, self.config, self.logger)
        self.logger.info('Destination map...')
        self.leftMap.setTarget(lat_deg, lon_deg, route)
        self.logger.info('Route map...')
        self.rightMap.setTarget(lat_deg, lon_deg, route)
        self.logger.info('Route ready.')
        QApplication.processEvents()

        self.logger.info('Report...')
        self.report.generate(lat_deg, lon_deg, route)
        self.logger.info('Finished.')

    def resizeEvent(self, event):
        self.logger.debug(event.size())

    def startTimer(self):
        self.alarmDateTime = QDateTime.currentDateTime()
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

    def exampleJugend(self):
        self.startTimer()
        self.titleLabel.setText('B3 Wohnungsbrand')
        self.msgLabel.setText('St.-Anna-Berg 5 (Jugendherberge)\n' \
            'lt. Betreiber 34 Personen gemeldet')
        self.leftMap.invalidate()
        self.leftMap.setObjectPlan('KLV 02/140')
        self.rightMap.invalidate()

        lat_deg = 51.78317
        lon_deg = 6.10695
        self.processAlarm(lat_deg, lon_deg)

    def exampleEngels(self):
        self.startTimer()
        self.titleLabel.setText('H1 Tierrettung')
        self.msgLabel.setText('Engelsstraße 5\nKatze auf Baum')
        self.leftMap.invalidate()
        self.rightMap.invalidate()

        lat_deg = 51.75065
        lon_deg = 6.11170
        self.processAlarm(lat_deg, lon_deg)

    def exampleSack(self):
        self.startTimer()
        self.titleLabel.setText('B2 Garagenbrand')
        self.msgLabel.setText('Sackstraße 173\nKfz brennt unter Carport')
        self.leftMap.invalidate()
        self.rightMap.invalidate()

        lat_deg = 51.77190
        lon_deg = 6.12305
        self.processAlarm(lat_deg, lon_deg)
