# -*- coding: utf-8 -*-

#-----------------------------------------------------------------------------
#
# Calendar List Widget
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
from tzlocal import get_localzone

from PyQt5.QtWidgets import QFrame
from PyQt5.QtGui import QPainter, QFontMetrics, QColor, QIcon
from PyQt5.QtCore import Qt, QPoint, QSize, QRect

#-----------------------------------------------------------------------------

class CalendarList(QFrame):

    def __init__(self, parent, config, logger):
        super(CalendarList, self).__init__(parent)

        self.config = config
        self.logger = logger
        self.events = []

    def resizeEvent(self, event):
        pass

    def paintEvent(self, event):
        painter = QPainter(self)
        margin = 25
        pad = 10
        cr = self.contentsRect()
        size = cr.size()

        top = cr.top() + margin

        wholeDay = '(ganztägig)'
        fm = QFontMetrics(painter.font())
        textRect = fm.boundingRect(wholeDay)
        textRect = fm.boundingRect(textRect, 0, wholeDay)
        timeWidth = textRect.width() + 20

        date = None
        tz = get_localzone()
        for event in self.events:
            if 'DTSTART' not in event:
                continue

            dt = event['DTSTART'].dt
            if isinstance(dt, datetime.datetime):
                dtl = dt.astimezone(tz)
                (top, abort) = self.dateLine(date, dtl.date(), painter, top)
                date = dtl.date()
                timeText = dtl.strftime('%H:%M Uhr')
            else:
                (top, abort) = self.dateLine(date, dt, painter, top)
                date = dt
                timeText = wholeDay

            if abort:
                break

            summaryHeight = 0
            if 'SUMMARY' in event:
                text = event['SUMMARY']
                font = painter.font()
                font.setBold(True)
                fm = QFontMetrics(font)
                rect = QRect(cr.left() + timeWidth, top,
                        cr.width() - timeWidth, cr.height() - top)
                rect = fm.boundingRect(rect, Qt.TextWordWrap, text)
                painter.save()
                painter.setFont(font)
                painter.drawText(rect, Qt.TextWordWrap, text)
                painter.restore()
                summaryHeight = rect.height()

            text = ''
            if 'LOCATION' in event:
                loc = event['LOCATION']
                if loc:
                    if text:
                        text += '\n'
                    text += 'Ort: %s' % (loc)
            if 'DESCRIPTION' in event:
                desc = event['DESCRIPTION']
                if desc:
                    if text:
                        text += '\n'
                    text += desc

            fm = QFontMetrics(painter.font())
            rect = QRect(cr.left() + timeWidth, top + summaryHeight,
                    cr.width() - timeWidth, cr.height() - top - summaryHeight)
            textRect = fm.boundingRect(rect, Qt.TextWordWrap, text)

            timeRect = QRect(cr.left(), top, timeWidth,
                    summaryHeight + textRect.height())
            if timeRect.bottom() > cr.bottom():
                break
            painter.drawText(timeRect, Qt.AlignLeft, timeText)

            top += summaryHeight
            if text:
                painter.drawText(rect, Qt.AlignLeft, text)
                top += textRect.height()

            painter.drawLine(timeRect.right() - 10, timeRect.top(),
                    timeRect.right() - 10, top)

    def dateLine(self, curDate, nextDate, painter, top):
        if curDate and nextDate <= curDate:
            return (top, False)

        text = nextDate.strftime('%A, %d. %B')
        cr = self.contentsRect()
        top += 10 # gap
        fm = QFontMetrics(painter.font())
        textRect = fm.boundingRect(text)
        textRect = fm.boundingRect(textRect, 0, text)
        rect = QRect(cr.left(), top, cr.width(), textRect.height())
        if rect.bottom() >= cr.bottom():
            return (top, True)
        painter.fillRect(rect, QColor(0, 0, 120))
        painter.drawText(rect, Qt.AlignLeft, text)
        return (top + rect.height(), False)

#-----------------------------------------------------------------------------
