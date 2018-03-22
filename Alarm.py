#!/usr/bin/python -u
# vim: set fileencoding=utf-8 sw=4 expandtab ts=4 :

#-----------------------------------------------------------------------------
#
# Alarm and Resources
#
# Florian Pose <florian@pose.nrw>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301  USA
#
#-----------------------------------------------------------------------------

import re
import xml.dom.minidom
import datetime
import pytz

from PyQt5.QtCore import *
#-----------------------------------------------------------------------------

class Alarm:
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

    def fromPager(self, pagerStr, logger):
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
                '.*(\d\d-\d+-\d+ \d+:\d+:\d+)\s+' \
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
        ma = alarmRe.match(pagerStr)
        if not ma:
            logger.warn('Alarmtext nicht erkannt!')
            return

        logger.debug(ma.groups())

        dt_naive = datetime.datetime.strptime(ma.group(1), '%d-%m-%y %H:%M:%S')
        logger.debug('Date naive %s', dt_naive)
        zoneStr = self.config.get('email', 'time_zone',
                fallback = 'Europe/Berlin')
        tz = pytz.timezone(zoneStr)
        logger.debug('Timezone %s', tz)
        self.datetime = tz.localize(dt_naive)
        logger.debug('Date %s', self.datetime)

        einheit = ma.group(2).strip() # unused
        coord = ma.group(3)
        coord = coord[:2] + '.' + coord[2:]
        self.lat = float(coord)
        coord = ma.group(4)
        coord = coord[:2] + '.' + coord[2:]
        self.lon = float(coord)
        logger.debug('Coordinates: lon=%f lat=%f', self.lon, self.lat)
        self.number = ma.group(5)
        self.art = ma.group(6)[0]
        self.stichwort = ma.group(6)[1]
        self.diagnose = ma.group(7) # Diagnose und Eskalationsstufe
        self.besonderheit = ma.group(8) # Hinweis (Freitext)
        self.ort = ma.group(9)
        self.ortsteil = ma.group(10)
        self.strasse = ma.group(11)
        self.hausnummer = ma.group(12)
        self.objektnummer = ma.group(13)
        self.ortshinweis = ma.group(14)

    def fromXml(self, xmlString, logger):
        self.xml = xmlString

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

    def title(self):
        return self.art + self.stichwort + ' ' + self.diagnose

    def imageBase(self):
        if not self.art:
            return None
        alarmType = self.art.upper()
        if alarmType == 'B':
            return 'feuer'
        if alarmType == 'H':
            return 'hilfe'
        return None

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

#----------------------------------------------------------------------------
