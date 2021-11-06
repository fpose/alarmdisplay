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
from tzlocal import get_localzone
import re

from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtNetwork import *

from CalendarGrid import *
from CalendarList import *

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

        self.networkAccessManager = QNetworkAccessManager()
        self.networkAccessManager.finished.connect(self.handleResponse)

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

        self.listWidget = CalendarList(self, self.config, self.logger)
        self.listWidget.setStyleSheet("""
            font-size: 20px;
            padding: 10px 10px 10px 10px;
            """)
        horLayout.addWidget(self.listWidget, 2)

        self.caldav_calendars = []
        self.ics_calendars = []

        self.events = []

        self.request_events = []
        self.request_calendars = set()

        if self.config.has_section('idle'):
            calRe = re.compile('calendar[0-9]+')
            icsRe = re.compile('ics[0-9]+')

            for key, value in self.config.items('idle'):
                ma = calRe.fullmatch(key)
                if ma:
                    self.logger.info("Using CalDAV calendar %s", value)
                    self.caldav_calendars.append(value)
                    continue
                ma = icsRe.fullmatch(key)
                if ma:
                    self.logger.info("Using ICS calendar %s", value)
                    self.ics_calendars.append(value)

        self.request()

    def localStart(self, event, tz, now_loc):
        if 'DTSTART' not in event:
            return now_loc
        dt = event['DTSTART'].dt
        if isinstance(dt, datetime.datetime):
            dt_loc = dt.astimezone(tz)
        else:
            dt_loc = datetime.datetime(dt.year, dt.month, dt.day)
            dt_loc = tz.localize(dt_loc)
        return dt_loc

    def localEnd(self, event, tz, now_loc):
        if 'DTEND' not in event:
            return now_loc
        dt = event['DTEND'].dt
        if isinstance(dt, datetime.datetime):
            dt_loc = dt.astimezone(tz)
        else:
            dt_loc = datetime.datetime(dt.year, dt.month, dt.day)
            dt_loc = tz.localize(dt_loc)
        return dt_loc

    def request(self):
        self.request_events = []
        start = datetime.datetime.now()
        end = start + datetime.timedelta(days = 62)

        for url in self.caldav_calendars:
            try:
                self.loadCalDavEvents(url, start, end)
            except:
                self.logger.error('Failed to load CalDAV events from %s:',
                        url, exc_info = True)

        self.request_calendars = set()

        for url in self.ics_calendars:
            try:
                self.loadIcsEvents(url, start, end)
            except:
                self.logger.error('Failed to load ICS events from %s:', url,
                        exc_info = True)
            self.request_calendars.add(url)

        if not self.request_calendars:
            self.updateEvents()

    def updateEvents(self):
        if not self.request_events:
            return

        tz = get_localzone()
        now = tz.localize(datetime.datetime.now())

        sorted_events = sorted(self.request_events,
                key = lambda e: self.localStart(e, tz, now))

        # Filter out events that ended in the past
        self.events = list(filter(lambda e: self.localEnd(e, tz, now) >= now,
            sorted_events))

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

        self.listWidget.events = self.events
        self.listWidget.update()

    def loadCalDavEvents(self, url, start, end):
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
        self.request_events.extend(events)

    def loadIcsEvents(self, url, start, end):
        req = QNetworkRequest(QUrl(url))
        self.networkAccessManager.get(req)

    def handleResponse(self, reply):
        req = reply.request()
        er = reply.error()
        url = req.url().toString()
        if er == QNetworkReply.NoError:
            ics = reply.readAll().data()
            ok = True
            try:
                cal = icalendar.Calendar.from_ical(ics)
            except:
                self.logger.error('Failed to load ICS events from %s:', url,
                        exc_info = True)
                ok = False
            if ok:
                for e in cal.walk('vevent'):
                    if 'DTSTART' in e:
                        self.request_events.append(e)
                    else:
                        self.logger.error('Skipping %s', repr(e))

        try:
            self.request_calendars.remove(url)
        except:
            self.logger.error('Failed to remove %s.', url,
                    exc_info = True)
        if not self.request_calendars:
            self.updateEvents()

        reply.deleteLater()

    def start(self):
        self.viewTimer.start()

    def stop(self):
        self.viewTimer.stop()

    def viewTimeout(self):
        self.finished.emit()

#-----------------------------------------------------------------------------
