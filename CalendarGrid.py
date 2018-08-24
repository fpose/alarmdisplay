# -*- coding: utf-8 -*-

#-----------------------------------------------------------------------------
#
# Calendar Grid Widget
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

from PyQt5.QtWidgets import QFrame
from PyQt5.QtGui import QPainter, QFontMetrics, QColor, QIcon
from PyQt5.QtCore import Qt, QPoint, QSize, QRect

#-----------------------------------------------------------------------------

class CalendarGrid(QFrame):

    def __init__(self, parent, config, logger):
        super(CalendarGrid, self).__init__(parent)

        self.config = config
        self.logger = logger
        self.busyDays = set()

    def resizeEvent(self, event):
        pass

    def paintEvent(self, event):
        painter = QPainter(self)
        margin = 25
        pad = 10
        ind = 50
        cr = self.contentsRect()
        size = cr.size()
        boxWidth = (size.width() - 2 * margin - ind - 6 * pad) / 7
        boxHeight = boxWidth / 1.618

        date = datetime.date.today()
        prevMonth = date.month - 1
        top = cr.top() + margin

        while True:
            if not date.weekday():
                top += boxHeight + pad
            if prevMonth != date.month:
                top += boxHeight + pad

            rect = QRect(cr.left() + margin + ind + \
                    date.weekday() * (boxWidth + pad),
                    top, boxWidth, boxHeight)

            if rect.bottom() > cr.bottom() - margin:
                break

            if prevMonth != date.month:
                monRect = QRect(cr.left() + margin, top,
                        ind, boxHeight)
                painter.drawText(monRect, Qt.AlignCenter, date.strftime('%b'))
            elif not date.weekday():
                monRect = QRect(cr.left() + margin, top, ind, boxHeight)
                painter.drawText(monRect, Qt.AlignCenter, date.strftime('%V'))

            if date in self.busyDays:
                color = QColor(200, 100, 100)
            elif date.weekday() > 4:
                color = QColor(0, 0, 120)
            else:
                color = QColor(60, 60, 180)

            painter.fillRect(rect, color)
            painter.drawText(rect, Qt.AlignCenter, str(date.day))

            prevMonth = date.month
            date += datetime.timedelta(days = 1)

#-----------------------------------------------------------------------------
