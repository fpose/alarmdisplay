#!/usr/bin/python -u
# vim: set fileencoding=utf-8 sw=4 expandtab ts=4 :

#-----------------------------------------------------------------------------
#
# Alarm and Resources
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

import os
import re
import xml.dom.minidom
import datetime
import pytz
from tzlocal import get_localzone

from PyQt5.QtCore import *

#-----------------------------------------------------------------------------

class Alarm:

    images = {
        'B': 'feuer',
        'C': 'abc',
        'H': 'hilfe'
    }

    coordRe = re.compile('#K01;N(\d+)E(\d+);')
    alarmRe = re.compile( \
            '.*(\d\d-\d+-\d+ \d+:\d+:\d+)\s+' \
            '(.*)\s*\*' \
            '(.*)\*' \
            '(..)\s+' \
            '(.*)\*' \
            '(.*)\*' \
            '(.*)\*' \
            '(.*)\*' \
            '(.*)\*' \
            '(.*)\*' \
            '(.*)\*' \
            '(.*)')
    dateRe = re.compile('\d\d\d\d-\d\d-\d\d-\d\d-\d\d-\d\d')

    def __init__(self, config, receiveTimeStamp = None):
        self.number = None
        self.datetime = None
        self.art = None
        self.stichwort = None
        self.diagnose = None
        self.eskalation = None
        self.besonderheit = None
        self.sondersignal = None
        self.meldender = None
        self.rufnummer = None
        self.plz = None
        self.ort = None
        self.ortsteil = None
        self.strasse = None
        self.hausnummer = None
        self.ortshinweis = None
        self.objektname = None
        self.objektnummer = None
        self.lat = 0.0
        self.lon = 0.0
        self.einsatzmittel = []
        self.receiveTimeStamp = receiveTimeStamp
        self.xml = None
        self.config = config
        self.source = None
        self.pager = None
        self.fallbackStr = None

    def fromPager(self, pagerStr, logger, dateTime = None):
        # '16-12-17 18:55:10 DME-Text
        # #K01;N5174110E0608130; *57274*H1 Hilfeleistung*
        # Hinweis*Stadt*Ortsteil*Straße*
        # *Objektplan*Ortshinweis

        self.pager = pagerStr
        self.source = 'pager'

        ma = self.coordRe.search(pagerStr)
        if ma:
            coord = ma.group(1)
            coord = coord[:2] + '.' + coord[2:]
            self.lat = float(coord)
            coord = ma.group(2)
            coord = coord[:2] + '.' + coord[2:]
            self.lon = float(coord)
            span = ma.span()
            pagerStr = pagerStr[: span[0]] + pagerStr[span[1] :]

        ma = self.alarmRe.match(pagerStr)
        if not ma:
            logger.warn('Alarmtext nicht erkannt!')
            self.fallbackStr = pagerStr
            return

        #  1) Datum/Uhrzeit TT-MM-YY HH:MM:SS
        #  2) Einheit, Funktion (RIC)
        #  .) Koordinaten (zuerst entfernt)
        #  3) Einsatznummer
        #  4) Einsatzart und Stichwort
        #  5) Diagnose und Eskalationsstufe
        #  6) Hinweis (Freitext)
        #  7) Stadt
        #  8) Ortsteil
        #  9) Straße
        # 10) Hausnummer
        # 11) Objektplan
        # 12) Ortshinweis

        if dateTime:
            self.datetime = dateTime
        else:
            useHostClock = self.config.get('pager', 'use_host_clock',
                    fallback = False)
            if useHostClock:
                now = datetime.datetime.now()
                local_tz = get_localzone()
                self.datetime = local_tz.localize(now)
            else:
                dt_naive = datetime.datetime.strptime(ma.group(1),
                        '%d-%m-%y %H:%M:%S')
                zoneStr = self.config.get('pager', 'time_zone',
                        fallback = 'Europe/Berlin')
                tz = pytz.timezone(zoneStr)
                self.datetime = tz.localize(dt_naive)

        einheit = ma.group(2).strip() # unused
        self.number = ma.group(3)
        self.art = ma.group(4)[0]
        self.stichwort = ma.group(4)[1]
        self.diagnose = ma.group(5) # Diagnose und Eskalationsstufe
        self.besonderheit = ma.group(6) # Hinweis (Freitext)
        self.ort = ma.group(7)
        self.ortsteil = ma.group(8)
        self.strasse = ma.group(9)
        self.hausnummer = ma.group(10)
        self.objektnummer = ma.group(11)
        self.ortshinweis = ma.group(12)

    def fromXml(self, xmlString, logger):
        self.xml = xmlString
        self.source = 'xml'

        doc = xml.dom.minidom.parseString(xmlString)
        elemDaten = doc.firstChild
        assert elemDaten.localName == 'daten'

        for child in elemDaten.childNodes:
            if child.nodeType != child.ELEMENT_NODE:
                continue
            if child.localName == 'einsatz':
                self.parseEinsatz(child, logger)
            elif child.localName == 'einsatzort':
                self.parseEinsatzOrt(child, logger)
            elif child.localName == 'einsatzmittel':
                self.parseEinsatzMittel(child, logger)

    def parseEinsatz(self, elem, logger):
        for child in elem.childNodes:
            if child.nodeType != child.ELEMENT_NODE:
                continue
            if child.localName == 'timestamp':
                c = content(child)
                dt_naive = datetime.datetime.strptime(c, '%Y%m%d%H%M%S')
                dt_utc = pytz.utc.localize(dt_naive)
                zoneStr = self.config.get('email', 'time_zone',
                        fallback = 'Europe/Berlin')
                tz = pytz.timezone(zoneStr)
                self.datetime = dt_utc.astimezone(tz)
            elif child.localName == 'einsatznummer':
                self.number = content(child)
            elif child.localName == 'einsatzart':
                self.art = content(child)
            elif child.localName == 'einsatzstichwort':
                self.stichwort = content(child)
            elif child.localName == 'diagnose':
                self.diagnose = content(child)
            elif child.localName == 'eskalation':
                self.eskalation = content(child)
            elif child.localName == 'besonderheit':
                self.besonderheit = content(child)
            elif child.localName == 'sondersignal':
                self.sondersignal = content(child)
            elif child.localName == 'meldender':
                self.meldender = content(child)
            elif child.localName == 'rufnummer':
                self.rufnummer = content(child)

    def parseEinsatzOrt(self, elem, logger):
        for child in elem.childNodes:
            if child.nodeType != child.ELEMENT_NODE:
                continue
            if child.localName == 'plz':
                self.plz = content(child)
            elif child.localName == 'ort':
                self.ort = content(child)
            elif child.localName == 'ortsteil':
                self.ortsteil = content(child)
            elif child.localName == 'strasse':
                self.strasse = content(child)
            elif child.localName == 'hausnummer':
                self.hausnummer = content(child)
            elif child.localName == 'objekt':
                self.parseObjekt(child)
            elif child.localName == 'koordinaten':
                c = content(child)
                #POINT (6.16825119 51.80245845)
                m = re.search('\((.*)\s+(.*)\)', c)
                if m:
                    try:
                        self.lon = float(m.group(1))
                        self.lat = float(m.group(2))
                    except:
                        logger.error(u'Unbekanntes Koordinaten-Format: %s', c)
                else:
                    logger.error(u'Unbekanntes Koordinaten-Format: %s', c)

    def parseObjekt(self, elem):
        for child in elem.childNodes:
            if child.nodeType != child.ELEMENT_NODE:
                continue
            if child.localName == 'o_name':
                self.objektname = content(child)
            elif child.localName == 'o_nummer':
                self.objektnummer = content(child)

    def parseEinsatzMittel(self, elem, logger):
        for child in elem.childNodes:
            if child.nodeType != child.ELEMENT_NODE:
                continue
            if child.localName == 'em':
                em = EinsatzMittel(child)
                self.einsatzmittel.append(em)

    def out(self, logger):
        logger.info(u'Sondersignal: %s', repr(self.sondersignal))
        logger.info(u'Besonderheit: %s', repr(self.besonderheit))
        for em in self.einsatzmittel:
            logger.info(em.asString())

    def save(self):
        path = self.config.get('db', 'path', fallback = None)
        if not path:
            return

        contents = None
        if self.source == 'pager':
            ext = '.dme'
            contents = self.pager # str
            encoding = 'utf-8'
            binary = ''
        elif self.source == 'xml':
            ext = '.xml'
            contents = self.xml # bytes
            encoding = None
            binary = 'b'

        if not contents:
            return

        local_tz = get_localzone()
        fileDateTime = self.datetime.astimezone(local_tz)
        fileName = fileDateTime.strftime('%Y-%m-%d-%H-%M-%S') + ext

        f = open(os.path.join(path, fileName), 'w' + binary,
                encoding = encoding)
        f.write(contents)
        f.close()

    def load(self, path, logger):
        f = open(path, 'r', encoding = 'utf-8')
        contents = f.read()
        f.close()

        ma = self.dateRe.search(path)
        dt_naive = datetime.datetime.strptime(ma.group(),
                '%Y-%m-%d-%H-%M-%S')
        local_tz = get_localzone()
        dateTime = local_tz.localize(dt_naive)

        if path.endswith('.dme'):
            self.fromPager(contents, logger, dateTime = dateTime)

        if path.endswith('.xml'):
           self.fromXml(contents, logger)

    def matches(self, other):
        return self.number and other.number and \
            self.number[-5 :] == other.number[-5 :]

    def merge(self, other, logger):
        logger.info('Merging alarms...')

        if other.number:
            if not self.number or len(self.number) < len(other.number):
                logger.info('preferring number %s over %s.',
                    other.number, self.number)
                self.number = other.number

        # self.datetime
        # self.lat
        # self.lon

        stringVars = [
            'art',
            'stichwort',
            'diagnose',
            'eskalation',
            'besonderheit',
            'sondersignal',
            'meldender',
            'rufnummer',
            'plz',
            'ort',
            'ortsteil',
            'strasse',
            'hausnummer',
            'ortshinweis',
            'objektname',
            'objektnummer'
            ]

        selfVars = vars(self)
        otherVars = vars(other)
        for key in stringVars:
            if key not in otherVars.keys() or not otherVars[key]:
                continue

            if not selfVars[key]:
                logger.info('Setting %s to %s.', key, otherVars[key])
                selfVars[key] = otherVars[key]
                continue

            if selfVars[key] != otherVars[key]:
                logger.info('%s is differing: %s / %s.', key,
                        repr(selfVars[key]), repr(otherVars[key]))

        logger.info('Merge complete.')

    def title(self):
        if self.art and self.stichwort and self.diagnose:
            return self.art + self.stichwort + ' ' + self.diagnose
        else:
            return ''

    def imageBase(self):
        if not self.art:
            return None
        alarmType = self.art.upper()
        if alarmType not in self.images:
            return None
        return self.images[alarmType]

    def address(self):
        ret = self.strasse
        if self.hausnummer:
            if ret:
                ret += ' '
            ret += self.hausnummer
        if self.ortsteil:
            if ret:
                ret += ', '
            ret += self.ortsteil
        if self.ort:
            homeTown = self.config.get('display', 'home_town', fallback = '')
            if self.ort != homeTown:
                if ret:
                    ret += ', '
                ret += self.ort
        return ret

    def location(self):
        ret = self.address()
        if self.objektname:
            ret += ' (' + self.objektname + ')'
        return ret

    def attention(self):
        ret = self.besonderheit
        return ret

    def callerInfo(self):
        ret = ''
        if self.meldender:
            ret += self.meldender
        if self.rufnummer:
            if ret:
                ret += ' / '
            ret += self.rufnummer
        return ret

    def betroffen(self, org, ort, ortZusatz):
        for em in self.einsatzmittel:
            if em.betroffen(org, ort, ortZusatz):
                return True
        return False

    def einheiten(self, einheit, ignore, logger):
        zusatz = []
        for em in self.einsatzmittel:
            if ignore(em):
                continue
            if em.zusatz in zusatz:
                continue # schon gesehen
            if em.zusatz not in einheit:
                logger.error(u'Unbekannter Zusatz %s!', em.zusatz)
                continue
            zusatz.append(em.zusatz)

        ret = u''
        for z in sorted(zusatz):
            if ret != u'':
                ret += u', '
            ret += einheit[z]

        return ret

    def filterEinsatzMittel(self, ignore):
        emFiltered = []
        for em in self.einsatzmittel:
            if not ignore(em):
                emFiltered.append(em)
        self.einsatzmittel = emFiltered

    def isTest(self):
        try:
            intNum = int(self.number)
            return intNum < 1160000000
        except:
            return False

#-----------------------------------------------------------------------------

class EinsatzMittel:
    def __init__(self, elem = None):
        self.org = None
        self.ort = None
        self.zusatz = None
        self.typ = None
        self.kennung = None
        self.gesprochen = None

        if not elem:
            return

        for child in elem.childNodes:
            if child.nodeType != child.ELEMENT_NODE:
                continue
            if child.localName == 'em_organisation':
                self.org = content(child)
            elif child.localName == 'em_ort':
                self.ort = content(child)
            elif child.localName == 'em_ort_zusatz':
                self.zusatz = content(child)
            elif child.localName == 'em_typ':
                self.typ = content(child)
            elif child.localName == 'em_ordnungskennung':
                self.kennung = content(child)
            elif child.localName == 'em_opta_gesprochen':
                self.gesprochen = content(child)

    def asString(self):
        ret = u''

        if self.org:
            ret += self.org
        else:
            ret += u'**'
        ret += u' '

        if self.ort:
            ret += self.ort
        else:
            ret += u'***'
        ret += u' '

        if self.zusatz:
            ret += self.zusatz
        else:
            ret += u'**'
        ret += u' '

        if self.typ:
            ret += u'{0:<6}'.format(self.typ)
        else:
            ret += u'******'
        ret += u' '

        if self.kennung:
            ret += self.kennung
        else:
            ret += u'**'

        if self.gesprochen:
            ret += u' '
            ret += self.gesprochen

        return ret

    def betroffen(self, org, ort, ortZusatz):
        try:
            intZusatz = int(self.zusatz)
        except:
            return False
        return self.org == org and self.ort == ort and intZusatz == ortZusatz

#-----------------------------------------------------------------------------

def content(elem):
    value = ''
    for text in elem.childNodes:
        assert text.nodeType == text.TEXT_NODE
        value += text.data
    return value.strip()

#-----------------------------------------------------------------------------
