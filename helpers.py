# -*- coding: utf-8 -*-

#-----------------------------------------------------------------------------
#
# Miscellaneous helper functions
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

from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtSvg import *

#-----------------------------------------------------------------------------

def pixmapFromSvg(path, width):
    renderer = QSvgRenderer(path)

    svgSize = renderer.defaultSize()
    height = svgSize.height() / svgSize.width() * width

    pixmap = QPixmap(QSize(width, height))
    painter = QPainter()

    pixmap.fill(Qt.transparent)

    painter.begin(pixmap)
    renderer.render(painter)
    painter.end()

    return pixmap

#-----------------------------------------------------------------------------
