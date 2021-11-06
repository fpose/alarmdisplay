#-----------------------------------------------------------------------------
#
# LaTeX helper functions
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

def escapeLaTeX(text):

    if text is None:
        return None

    inQuote = False
    ret = ''
    for c in text:
        if c == '"':
            if inQuote:
                ret += '\'\''
            else:
                ret += '``'
            inQuote = not inQuote
        elif c == u'&':
            ret += '\&'
        elif c == u'\u202f':
            ret += '\\,'
        elif c == u'%':
            ret += '\\%'
        elif c == u'\\':
            ret += '\\textbackslash{}'
        elif c == u'^':
            ret += '\\textasciicircum{}'
        elif c == u'~':
            ret += '\\textasciitilde{}'
        elif c == u'$':
            ret += '\\$'
        elif c == u'#':
            ret += '\\#'
        elif c == u'_':
            ret += '\\_'
        elif c == u'{':
            ret += '\\{'
        elif c == u'}':
            ret += '\\}'
        else:
            ret += c
    return ret

#-----------------------------------------------------------------------------
