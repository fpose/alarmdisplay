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

class MainWidget(QWidget):

    def __init__(self, config):
        super(MainWidget, self).__init__()

        self.config = config

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

        subprocess.call(['xset', 's', 'off'])
        subprocess.call(['xset', 's', 'noblank'])
        subprocess.call(['xset', 's', '0', '0'])
        subprocess.call(['xset', '-dpms'])

        self.move(0, 0)
        self.resize(1920, 1080)

        self.setWindowTitle('Alarmdisplay')
        self.setStyleSheet("""
            font-size: 70px;
            background-color: rgb(0, 34, 44);
            color: rgb(2, 203, 255);
            font-family: "DejaVu Sans";
            """)

        verLayout = QVBoxLayout(self)
        verLayout.setContentsMargins(0, 0, 0, 0)

        self.msgLabel = QLabel(self)
        self.msgLabel.setStyleSheet("""
            color: white;
            background-color: rgb(80, 0, 0);
            """)
        verLayout.addWidget(self.msgLabel, 1)

        horLayout = QHBoxLayout(self)
        verLayout.addLayout(horLayout, 2)

        self.leftMap = MapWidget(self, self.config)
        self.leftMap.setStyleSheet("""
            background-color: rgb(80, 80, 0);
            """)
        horLayout.addWidget(self.leftMap, 2)

        centerLayout = QVBoxLayout(self)
        horLayout.addLayout(centerLayout, 1)

        logoLabel = QLabel(self)
        logo = self.config.get("display", "logo", fallback = None)
        if logo:
            imageDir = self.config.get("display", "image_dir",
                    fallback = "images")
            styleSheet = 'image: url({0});'.format( \
                    os.path.join(imageDir, logo))
            logoLabel.setStyleSheet(styleSheet)
        centerLayout.addWidget(logoLabel)

        self.timerLabel = QLabel(self)
        self.timerLabel.setAlignment(Qt.AlignCenter)
        centerLayout.addWidget(self.timerLabel)

        self.rightMap = RouteWidget(self, self.config)
        self.rightMap.setStyleSheet("""
            background-color: rgb(0, 80, 80);
            """)
        horLayout.addWidget(self.rightMap, 2)

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
        self.alarmReceiver = AlarmReceiver()
        self.alarmReceiver.receivedAlarm.connect(self.receivedAlarm)
        self.alarmReceiver.moveToThread(self.thread)
        self.alarmReceiver.finished.connect(self.thread.quit)
        self.thread.started.connect(self.alarmReceiver.receive)
        self.thread.start()

        self.report = AlarmReport(self.config)

    def receivedAlarm(self, alarm):
        print('Received alarm', alarm)

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
            print('Alarmtext nicht erkannt!')
            return

        print(ma.groups())
        datetime = QDateTime.fromString(ma.group(1), 'dd-MM-yy hh:mm:ss')
        datetime = datetime.addYears(100)
        print(datetime)
        einheit = ma.group(2).strip()
        coord = ma.group(3)
        coord = coord[:2] + '.' + coord[2:]
        lat_deg = float(coord)
        coord = ma.group(4)
        coord = coord[:2] + '.' + coord[2:]
        lon_deg = float(coord)
        print(lon_deg, lat_deg)
        text = ma.group(6) + ' ' + ma.group(7)
        address = ma.group(11)
        housenumber = ma.group(12)
        if housenumber:
            address += ' ' + housenumber
        ortshinweis = ma.group(14)
        if ortshinweis:
            address += ' (' + ortshinweis + ')'
        hinweis = ma.group(8)

        self.startTimer()
        self.msgLabel.setText(text + '\n' + address + '\n' + hinweis)
        self.leftMap.invalidate()
        self.rightMap.invalidate()
        QApplication.processEvents()

        route = getRoute(lat_deg, lon_deg, self.config)
        self.leftMap.setTarget(lat_deg, lon_deg, route)
        self.rightMap.setTarget(lat_deg, lon_deg, route)
        self.report.generate(lat_deg, lon_deg, route)

    def resizeEvent(self, event):
        print(event.size())

    def startTimer(self):
        self.alarmDateTime = QDateTime.currentDateTime()
        self.elapsedTimer.start()
        self.elapsedTimeout()
        print(u'Alarm', self.alarmDateTime)

        args = ['cec-client', '-s', '-d', '1']
        cecCommand = 'on 0'

        try:
            cec = subprocess.Popen(args, stdin = subprocess.PIPE)
            cec.communicate(input = cecCommand.encode('UTF-8'))
        except OSError as e:
            print('CEC wakeup failed:', e)
        except:
            print('CEC wakeup failed.')

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
        self.msgLabel.setText(u'B3 Wohnungsbrand\nSt.-Anna-Berg 5\n' \
                u'Jugendherberge')
        self.leftMap.invalidate()
        self.rightMap.invalidate()
        QApplication.processEvents()

        lat_deg = 51.78317
        lon_deg = 6.10695
        route = getRoute(lat_deg, lon_deg, self.config)
        self.leftMap.setTarget(lat_deg, lon_deg, route)
        self.rightMap.setTarget(lat_deg, lon_deg, route)
        self.report.generate(lat_deg, lon_deg, route)

    def exampleEngels(self):
        self.startTimer()
        self.msgLabel.setText(u'H1 Tierrettung\nEngelsstraße 5\n' \
                u'Katze auf Baum')
        self.leftMap.invalidate()
        self.rightMap.invalidate()
        QApplication.processEvents()

        lat_deg = 51.75065
        lon_deg = 6.11170
        route = getRoute(lat_deg, lon_deg, self.config)
        self.leftMap.setTarget(lat_deg, lon_deg, route)
        self.rightMap.setTarget(lat_deg, lon_deg, route)
        self.report.generate(lat_deg, lon_deg, route)

    def exampleSack(self):
        self.startTimer()
        self.msgLabel.setText(u'B2 Garagenbrand\nSackstraße 173\n' \
                u'Kfz brennt unter Carport')
        self.leftMap.invalidate()
        self.rightMap.invalidate()
        QApplication.processEvents()

        lat_deg = 51.77190
        lon_deg = 6.12305
        route = getRoute(lat_deg, lon_deg, self.config)
        self.leftMap.setTarget(lat_deg, lon_deg, route)
        self.rightMap.setTarget(lat_deg, lon_deg, route)
        self.report.generate(lat_deg, lon_deg, route)
