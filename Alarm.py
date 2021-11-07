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
import json
from collections import namedtuple
from tzlocal import get_localzone

#-----------------------------------------------------------------------------

class Alarm:

    images = {
        'B': 'feuer',
        'C': 'abc',
        'H': 'hilfe',
        'R': 'hilfe',
    }

    coordRe = re.compile('#K01;N(\d+)E(\d+);')
    alarmRe = re.compile( \
            '.*(\d\d-\d+-\d+ \d+:\d+:\d+)\s+' \
            '(.*?)\s*?\*' \
            '(.*?)\*' \
            '(..)\s+' \
            '(.*?)\*' \
            '(.*?)\*' \
            '(.*?)\*' \
            '(.*?)\*' \
            '(.*?)\*' \
            '(.*?)\*' \
            '(.*?)\*' \
            '(.*)')
    dateRe = re.compile('\d\d\d\d-\d\d-\d\d-\d\d-\d\d-\d\d')

    # <o_nummer>[My ignored object name] KLV 06/666</o_nummer>
    objectNumberRe = re.compile('\s*(\[.*\])\s*(.*)')

    # FW KLV01 DLK23 1
    einsatzMittelRe = re.compile(('\s*'
        '([A-Z]+)' # 1) FW
        '\s+'
        '([A-Z]+)' # 2) KLV
        '\s*'
        '([0-9]+)' # 3) 01
        '\s+'
        '([A-Z0-9\-]+)' # 4) DLK23 / TSF-W / ELW1
        '\s+'
        '([0-9]+)' # 5) 1
        '\s*'))

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
        self.einsatzmittel = set()
        self.receiveTimeStamp = receiveTimeStamp
        self.xml = None
        self.config = config
        self.source = None
        self.sources = set()
        self.pager = None
        self.json = None
        self.fallbackStr = None

    def fromPager(self, pagerStr, logger = None, dateTime = None):
        # '16-12-17 18:55:10 DME-Text
        # #K01;N5174110E0608130; *57274*H1 Hilfeleistung*
        # Hinweis*Stadt*Ortsteil*Straße*
        # *Objektplan*Ortshinweis

        self.pager = pagerStr
        self.source = 'pager'
        self.sources.add(self.source)

        useHostClock = self.config.getboolean('pager', 'use_host_clock',
                fallback = False)
        if dateTime:
            self.datetime = dateTime
        elif useHostClock:
            now = datetime.datetime.now()
            local_tz = get_localzone()
            self.datetime = local_tz.localize(now)

        ma = self.coordRe.search(pagerStr)
        if ma:
            coord = ma.group(1)
            coord = coord[:2] + '.' + coord[2:]
            self.lat = float(coord)
            coord = ma.group(2)
            coord = coord[:2] + '.' + coord[2:]
            self.lon = float(coord)
            span = ma.span()
            pagerStr = pagerStr[: span[0]] + pagerStr[span[1]:]

        ma = self.alarmRe.match(pagerStr)
        if not ma:
            if logger:
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

        if not dateTime and not useHostClock:
            dt_naive = datetime.datetime.strptime(ma.group(1),
                    '%d-%m-%y %H:%M:%S')
            zoneStr = self.config.get('pager', 'time_zone',
                    fallback = 'Europe/Berlin')
            tz = pytz.timezone(zoneStr)
            self.datetime = tz.localize(dt_naive)

        #einheit = ma.group(2).strip() # unused
        self.number = ma.group(3).strip()
        self.art = ma.group(4)[0]
        self.stichwort = ma.group(4)[1]
        self.diagnose = ma.group(5).strip() # Diagnose und Eskalationsstufe
        self.besonderheit = ma.group(6).strip() # Hinweis (Freitext)
        self.ort = ma.group(7).strip()
        self.ortsteil = ma.group(8).strip()
        self.strasse = ma.group(9).strip()
        self.hausnummer = ma.group(10).strip()
        self.objektnummer = ma.group(11).strip()
        self.ortshinweis = ma.group(12).strip()

    def fromXml(self, xmlString, logger = None):
        self.xml = xmlString
        self.source = 'xml'
        self.sources.add(self.source)

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
                if self.eskalation == '-':
                    self.eskalation = ''
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
                self.parseObjekt(child, logger)
            elif child.localName == 'koordinaten':
                c = content(child)
                if not c:
                    continue
                #POINT (6.16825119 51.80245845)
                m = re.search('\((.*)\s+(.*)\)', c)
                if m:
                    try:
                        self.lon = float(m.group(1))
                        self.lat = float(m.group(2))
                    except:
                        if logger:
                            logger.error( \
                                    u'Unbekanntes Koordinaten-Format "%s"', c)
                else:
                    if logger:
                        logger.error(u'Unbekanntes Koordinaten-Format: "%s"',
                                c)

    def parseObjekt(self, elem, logger):
        for child in elem.childNodes:
            if child.nodeType != child.ELEMENT_NODE:
                continue
            if child.localName == 'o_name':
                self.objektname = content(child)
            elif child.localName == 'o_nummer':
                o_num = content(child)
                m = self.objectNumberRe.fullmatch(o_num)
                if m:
                    self.objektnummer = m.group(2)
                else:
                    self.objektnummer = o_num

    def parseEinsatzMittel(self, elem, logger):
        for child in elem.childNodes:
            if child.nodeType != child.ELEMENT_NODE:
                continue
            if child.localName == 'em':
                em = EinsatzMittel.fromXml(child)
                self.einsatzmittel.add(em)

    def fromAlamos(self, data, logger):
        self.source = 'json'
        self.sources.add(self.source)
        self.json = json.dumps(data)

        self.number = data.get("COBRA_name", "")
        #address = data.get("address") FIXME Alarmiertes Einsatzmittel
        einsatzmittel = data.get("einsatzmittel")
        em_list = list(filter(None, einsatzmittel.split('\n')))
        for em in em_list:
            m = self.einsatzMittelRe.fullmatch(em)
            if m:
                # FW KLV01 DLK23 1
                mittel = EinsatzMittel(m.group(1), m.group(2), m.group(3),
                        m.group(4), m.group(5), em)
            else:
                mittel = EinsatzMittel(None, None, None, None, None, em)
            self.einsatzmittel.add(mittel)
        self.art = data.get("COBRA_keyword_ident_1", "")
        ts = int(data.get("timestamp").strip()) / 1000.0
        dt_naive = datetime.datetime.fromtimestamp(ts)
        zoneStr = self.config.get('websocket', 'time_zone',
                fallback = 'Europe/Berlin')
        tz = pytz.timezone(zoneStr)
        self.datetime = tz.localize(dt_naive)
        self.stichwort = data.get("COBRA_keyword_1", "")
        self.diagnose = data.get("COBRA_keyword_additional_1", "")
        self.eskalation = '' # FIXME
        self.besonderheit = data.get("COBRA_ADDITIONAL_comment", "")
        self.sondersignal = \
            data.get("COBRA_ADDITIONAL_special_rights") == 'Ja'
        self.meldender = data.get("COBRA_reporter_name", "")
        self.rufnummer = data.get("COBRA_reporter_phone", "")
        self.plz = data.get("postalCode", "")
        self.ort = data.get("city", "")
        self.ortsteil = data.get("city_abbr", "")
        self.strasse = data.get("street", "")
        self.hausnummer = data.get("house", "")
        self.objektname = data.get("building", "")
        self.objektnummer = '' # FIXME
        self.ortshinweis = data.get("COBRA_LOCATION_floor", "")
        self.lon = float(data.get("lng", "0.0"))
        self.lat = float(data.get("lat", "0.0"))

    def out(self, logger):
        logger.info(u'Sondersignal: %s', repr(self.sondersignal))
        logger.info(u'Besonderheit: %s', repr(self.besonderheit))
        for em in self.einsatzmittel:
            logger.info(em)

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
        elif self.source == 'json':
            ext = '.json'
            contents = self.json # str
            encoding = 'utf-8'
            binary = ''

        if not contents:
            return

        fileName = self.dateString() + ext
        f = open(os.path.join(path, fileName), 'w' + binary,
                encoding = encoding)
        f.write(contents)
        f.close()

    def dateString(self):
        local_tz = get_localzone()
        dt = self.datetime.astimezone(local_tz)
        return dt.strftime('%Y-%m-%d-%H-%M-%S')

    def load(self, path, logger = None):
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

        if path.endswith('.json'):
            data = json.loads(contents)
            self.fromAlamos(data, logger)

    def matches(self, other):
        return self.number and other.number and \
            self.number[-5:] == other.number[-5:]

    def merge(self, other, logger = None):
        if logger:
            logger.info('Merging alarms...')

        if other.number:
            if not self.number or len(self.number) < len(other.number):
                if logger:
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

        # Non-merged fields:
        # self.number = None
        # self.datetime = None
        # self.receiveTimeStamp = receiveTimeStamp
        # self.xml = None
        # self.config = config
        # self.source = None
        # self.pager = None
        # self.json = None
        # self.fallbackStr = None
        # self.lat = 0.0
        # self.lon = 0.0

        selfVars = vars(self)
        otherVars = vars(other)
        for key in stringVars:
            if key not in otherVars.keys() or not otherVars[key]:
                continue

            if not selfVars[key]:
                if logger:
                    logger.info('Setting %s to %s.', key, otherVars[key])
                selfVars[key] = otherVars[key]
                continue

            if selfVars[key] != otherVars[key]:
                if logger:
                    logger.info('%s is differing: %s / %s.', key,
                            repr(selfVars[key]), repr(otherVars[key]))

        # merge sources
        self.sources = self.sources.union(other.sources)

        # merge resources
        self.einsatzmittel = self.einsatzmittel.union(other.einsatzmittel)

        if logger:
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

    def einheiten(self, einheit, ignore, logger, sonder = dict()):
        zusatz = set()
        for em in self.einsatzmittel:
            if em.gesprochen in sonder:
                for z in sonder[em.gesprochen]:
                    zusatz.add(z)
            if ignore(em):
                continue
            if not em.zusatz:
                continue # leer oder None
            if em.zusatz not in einheit:
                logger.error(u'Unbekannter Zusatz "%s"!', em.zusatz)
                continue
            zusatz.add(em.zusatz)

        ret = ''
        for z in sorted(zusatz):
            if ret != '':
                ret += ', '
            ret += einheit[z]

        return ret

    def alarmiert(self):
        mittel_prio = []
        for em in self.einsatzmittel:
            g = em.gesprochen
            if not g:
                continue
            if g.startswith('LZ'):
                prio = 1
            elif g.startswith('LG'):
                prio = 2
            elif g.startswith('FW'):
                prio = 3
            elif g.startswith('RD'):
                prio = 4
            else:
                prio = 5
            mittel_prio.append((g, prio))
        mittel = sorted(mittel_prio, key=lambda x: (x[1], x[0]))
        return ', '.join(m[0] for m in mittel)

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

    def spoken(self):
        text = 'Einsatz! '

        if self.art and self.stichwort:
            text += '(' + self.art + self.stichwort + '). ' # B3

        if self.diagnose:
            text += '(' + self.diagnose + '). ' # Wohnungsbrand

        if self.eskalation:
            text += '(' + self.eskalation + '). '

        ort = None
        if self.ort and self.ort != 'Kleve':
            ort = self.ort

        ortstext = ''
        if ort and self.ortsteil:
            ortstext = ort + '-' + self.ortsteil
        elif ort and not self.ortsteil:
            ortstext = ort
        elif not ort and self.ortsteil:
            ortstext = self.ortsteil
        text += ortstext

        if self.strasse:
            if ortstext:
                text += ', '
            text += '(' + self.strasse
            if self.hausnummer:
                text += ' ' + self.hausnummer
            text += ')'
        text += '. '

        if self.objektname:
            text += '(' + self.objektname + '). '

        if self.besonderheit:
            text += '(' + self.besonderheit + '). '

        if self.sondersignal is not None and not self.sondersignal:
            text += 'Ohne Sondersignal. '

        return text

#-----------------------------------------------------------------------------

class EinsatzMittel(namedtuple('EinsatzMittel',
        'org ort zusatz typ kennung gesprochen')):

    @classmethod
    def fromXml(cls, elem):
        org = None
        ort = None
        zusatz = None
        typ = None
        kennung = None
        gesprochen = None
        for child in elem.childNodes:
            if child.nodeType != child.ELEMENT_NODE:
                continue
            if child.localName == 'em_organisation':
                org = content(child)
            elif child.localName == 'em_ort':
                ort = content(child)
            elif child.localName == 'em_ort_zusatz':
                zusatz = content(child)
            elif child.localName == 'em_typ':
                typ = content(child)
            elif child.localName == 'em_ordnungskennung':
                kennung = content(child)
            elif child.localName == 'em_opta_gesprochen':
                gesprochen = content(child)
        return cls(org, ort, zusatz, typ, kennung, gesprochen)

    def __repr__(self):
        ret = ''

        if self.org:
            ret += self.org
        else:
            ret += '**'
        ret += ' '

        if self.ort:
            ret += self.ort
        else:
            ret += '***'
        ret += ' '

        if self.zusatz:
            ret += self.zusatz
        else:
            ret += '**'
        ret += ' '

        if self.typ:
            ret += '{0:<6}'.format(self.typ)
        else:
            ret += '******'
        ret += ' '

        if self.kennung:
            ret += '{0:<2}'.format(self.kennung)
        else:
            ret += '**'

        if self.gesprochen:
            ret += ' '
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
