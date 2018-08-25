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

        fm = QFontMetrics(painter.font())

        prevDate = None
        tz = get_localzone()
        for event in self.events:
            if 'DTSTART' not in event:
                continue

            dt = event['DTSTART'].dt
            if isinstance(dt, datetime.datetime):
                dtl = dt.astimezone(tz)
                eventDate = dtl.date()
                timeText = dtl.strftime('%H:%M Uhr')
            else:
                eventDate = dt
                timeText = wholeDay

            dateText = ''
            if not prevDate or eventDate > prevDate:
                dateText = eventDate.strftime('%A, %d. %B')
                top += 10
                rect = fm.boundingRect(dateText)
                rect = fm.boundingRect(rect, 0, dateText)
                dateRect = QRect(cr.left(), top, cr.width(), rect.height())
                top += dateRect.height()
            prevDate = eventDate

            summaryHeight = 0
            if 'SUMMARY' in event:
                summary = event['SUMMARY']
                boldFont = painter.font()
                boldFont.setBold(True)
                boldMetrics = QFontMetrics(boldFont)
                sumRect = QRect(cr.left() + timeWidth, top,
                        cr.width() - timeWidth, cr.height() - top)
                sumRect = boldMetrics.boundingRect(sumRect, Qt.TextWordWrap,
                        summary)
                summaryHeight = sumRect.height()

            detailText = ''
            if 'LOCATION' in event:
                loc = event['LOCATION']
                if loc:
                    if detailText:
                        detailText += '\n'
                    detailText += 'Ort: %s' % (loc)
            if 'DESCRIPTION' in event:
                desc = event['DESCRIPTION']
                if desc:
                    if detailText:
                        detailText += '\n'
                    detailText += desc

            detailRect = QRect(cr.left() + timeWidth, top + summaryHeight,
                    cr.width() - timeWidth, cr.height() - top - summaryHeight)
            detailRect = fm.boundingRect(detailRect, Qt.TextWordWrap,
                    detailText)

            timeRect = QRect(cr.left(), top, timeWidth,
                    summaryHeight + detailRect.height())

            if timeRect.bottom() > cr.bottom():
                break

            # actual drawing

            if dateText:
                painter.fillRect(dateRect, QColor(0, 0, 120))
                painter.drawText(dateRect, Qt.AlignLeft, dateText)

            if summary:
                painter.save()
                painter.setFont(boldFont)
                painter.drawText(sumRect, Qt.TextWordWrap, summary)
                painter.restore()

            painter.drawText(timeRect, Qt.AlignLeft, timeText)

            top += summaryHeight
            if detailText:
                painter.drawText(detailRect, Qt.AlignLeft, detailText)
                top += detailRect.height()

            painter.drawLine(timeRect.right() - 10, timeRect.top(),
                    timeRect.right() - 10, top)

#-----------------------------------------------------------------------------
