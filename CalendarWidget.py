# -*- coding: utf-8 -*-

#-----------------------------------------------------------------------------
#
# Calendar Widget
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

import datetime
import caldav
import icalendar
import babel.dates
from tzlocal import get_localzone
import re

from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

from CalendarGrid import *

#-----------------------------------------------------------------------------

class CalendarWidget(QWidget):

    finished = pyqtSignal()

    def __init__(self, config, logger):
        super(CalendarWidget, self).__init__()

        self.config = config
        self.logger = logger

        self.imageDir = self.config.get("display", "image_dir",
                fallback = "images")

        self.updateTimer = QTimer(self)
        self.updateTimer.setInterval(60 * 60000)
        self.updateTimer.setSingleShot(False)
        self.updateTimer.timeout.connect(self.request)
        self.updateTimer.start()

        self.viewTimer = QTimer(self)
        self.viewTimer.setInterval(10000)
        self.viewTimer.setSingleShot(True)
        self.viewTimer.timeout.connect(self.viewTimeout)

        verLayout = QVBoxLayout(self)
        verLayout.setSpacing(0)
        verLayout.setContentsMargins(0, 0, 0, 0)

        label = QLabel(self)
        label.setText('Nächste Termine')
        label.setIndent(0)
        label.setStyleSheet("""
            font-size: 50px;
            padding: 10px 10px 10px 60px;
            """)
        verLayout.addWidget(label, 1)

        horLayout = QHBoxLayout()
        horLayout.setSpacing(0)
        horLayout.setContentsMargins(0, 0, 0, 0)
        verLayout.addLayout(horLayout, 7)

        self.grid = CalendarGrid(self, self.config, self.logger)
        self.grid.setStyleSheet("""
            font-size: 20px;
            """)
        horLayout.addWidget(self.grid, 1)

        self.listLabel = QLabel(self)
        self.listLabel.setIndent(0)
        self.listLabel.setSizePolicy(QSizePolicy.Ignored,
                QSizePolicy.Ignored)
        self.listLabel.setStyleSheet("""
            font-size: 20px;
            padding: 10px 10px 10px 10px;
            """)
        horLayout.addWidget(self.listLabel, 2)

        self.events = []
        self.calendars = []
        if self.config.has_section('idle'):
            calRe = re.compile('calendar[0-9]+')

            for key, value in self.config.items('idle'):
                ma = calRe.fullmatch(key)
                if not ma:
                    continue
                self.logger.info("Using calendar %s", value)
                self.calendars.append(value)

        if self.calendars:
            self.request()

    def localDt(self, event, tz):
        if 'DTSTART' not in event:
            return datetime.datetime.now()
        dt = event['DTSTART'].dt
        if isinstance(dt, datetime.datetime):
            dtl = dt.astimezone(tz)
        else:
            dtl = datetime.datetime(dt.year, dt.month, dt.day)
            dtl = tz.localize(dtl)
        return dtl

    def request(self):
        events = []
        start = datetime.datetime.now()
        end = start + datetime.timedelta(days = 62)
        for url in self.calendars:
            try:
                events.extend(self.loadEvents(url, start, end))
            except:
                self.logger.error('Failed to load events from %s', url)
        if events:
            tz = get_localzone()
            self.events = sorted(events, key = lambda e: self.localDt(e, tz))

            busyDays = set()
            for event in self.events:
                if 'DTSTART' in event:
                    dt = event['DTSTART'].dt
                    if isinstance(dt, datetime.datetime):
                        dt = dt.astimezone(tz)
                        date = dt.date()
                    else:
                        date = dt
                    if date not in busyDays:
                        busyDays.add(date)
            self.grid.busyDays = busyDays
            self.grid.update()

    def loadEvents(self, url, start, end):
        client = caldav.DAVClient(url)
        calendar = caldav.Calendar(client = client, url = url)
        results = calendar.date_search(start, end)
        events = []
        for event in results:
            cal = icalendar.Calendar.from_ical(event.data)
            for e in cal.walk('vevent'):
                if 'DTSTART' in e:
                    events.append(e)
                else:
                    self.logger.error('Skipping %s', repr(e))
        return events

    def dateLine(self, curDate, nextDate):
        if not curDate or nextDate > curDate:
            return nextDate.strftime('\n%A, %d. %B\n')
        else:
            return ''

    def start(self):
        text = ''
        date = None
        tz = get_localzone()
        for event in self.events:
            if 'DTSTART' in event:
                dt = event['DTSTART'].dt
                if isinstance(dt, datetime.datetime):
                    dtl = dt.astimezone(tz)
                    text += self.dateLine(date, dtl.date())
                    date = dtl.date()
                    text += dtl.strftime('%H:%M Uhr | ')
                else:
                    text += self.dateLine(date, dt)
                    date = dt
                    text += '(ganztägig) | '
            if 'SUMMARY' in event:
                 text += event['SUMMARY'] + '\n'
            if 'LOCATION' in event:
                 text += 'Ort: %s\n' % (event['LOCATION'])
            if 'DESCRIPTION' in event:
                 text += event['DESCRIPTION'] + '\n'
            text += '\n'
        self.listLabel.setText(text)

    def stop(self):
        pass

    def viewTimeout(self):
        self.finished.emit()

#-----------------------------------------------------------------------------
