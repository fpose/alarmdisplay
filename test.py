#!/usr/bin/python3
# -*- coding: utf-8 -*-

#-----------------------------------------------------------------------------
#
# Unit tests
#
# Copyright (C) 2018-2021 Florian Pose
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

import unittest
import sys
import configparser
import logging
import datetime
from tzlocal import get_localzone
import json
import PyQt5.QtWidgets
from Map import getRoute
from AlarmReport import AlarmReport
from Alarm import Alarm, EinsatzMittel

#-----------------------------------------------------------------------------

logger = logging.getLogger('alarmdisplay_test')
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s %(message)s')
streamHandler = logging.StreamHandler()
streamHandler.setLevel(logging.DEBUG)
streamHandler.setFormatter(formatter)
#logger.addHandler(streamHandler)

#-----------------------------------------------------------------------------

# Lokale Einheiten
einheit = {
    '01': 'LZ Kleve',
    '02': 'LZ Materborn',
    '03': 'LZ Kellen',
    '04': 'LZ Rindern',
    '05': 'LG Reichswalde',
    '06': 'LG Donsbrüggen',
    '07': 'LG Wardhausen-Brienen',
    '08': 'LG Griethausen',
    '09': 'LG Düffelward',
    '10': 'LG Keeken',
    '11': 'LG Schenkenschanz',
    '12': 'LG Warbeyen'
    }

# Besondere Einheitenzuordnungen
sonder = {
        'LZ Kleve': ['01'],
        'LZ KLV Süd': ['02', '05'],
        'LZ KLV West': ['04', '06'],
        }

#-----------------------------------------------------------------------------

class alarmdisplayTests(unittest.TestCase):

    def test_einsatzmittel(self):
        json_str = (r'{'
            r'"unitCode": "LZ Kleve",'
            r'"COBRA_state": "ALERT",'
            r'"timestamp": "1635865439209",'
            r'"einsatzmittel": "FW KLV01 DLK23 1\nFW KLV Ger\u00e4tewarte\n'
            r'LZ KLV S\u00fcd\nLZ Kleve\nRD KLV01 RTW 1",'
            r'"userName": "Admin",'
            r'"time": "16:03",'
            r'"COBRA_keyword_1_text": "Brandschutz",'
            r'"COBRA_keyword_2": "",'
            r'"tvp": "TVPN031613beE005d5ea2",'
            r'"location_dest_long": "Ackerstrasse 299, 47533 Kleve\n'
            r'Kreuzung: \nSektion: \nAnwesen: \nStock: \nKommentar: ",'
            r'"address": "LZ Kleve",'
            r'"COBRA_keyword_1": "3",'
            r'"house": "299",'
            r'"COBRA_keyword_additional_2": "",'
            r'"city_abbr": "Kleve",'
            r'"dbId": "9471fb068f4aff5554723efc7b7a9336367f660'
            r'a5675f375956d66d9d3195f77",'
            r'"COBRA_keyword_ident_2": "",'
            r'"location_URL": '
            r'"https://maps.google.de/maps?q=51.77849377,6.11907405",'
            r'"COBRA_keyword_description_2": "",'
            r'"COBRA_LOCATION_SUBPROPERTY_2": "",'
            r'"clock_long": "16:03:58",'
            r'"keyword_1_long": "Einsatzart: B\nStichwort: 3\n'
            r'Meldebild: Zimmerbrand\nKlartext: Feuer gro\u00df",'
            r'"COBRA_ADDITIONAL_special_rights": "Ja",'
            r'"city": "Kleve",'
            r'"COBRA_LOCATION_SUBPROPERTY_4": "",'
            r'"pluginmessage": " Ackerstrasse 299, 47533 Kleve -- '
            r'Alarmiert: FW KLV01 DLK23 1;\nFW KLV Ger\u00e4tewarte;\n'
            r'LZ KLV S\u00fcd;\nLZ Kleve;\nRD KLV01 RTW 1",'
            r'"COBRA_reporter_name": "Müller",'
            r'"keyword": "B3 Zimmerbrand",'
            r'"COBRA_ADDITIONAL_callback": "",'
            r'"COBRA_keyword_ident_1": "B",'
            r'"street": "Ackerstrasse",'
            r'"gps": "GPSN51778494E06119074",'
            r'"COBRA_LOCATION_SUBPROPERTY_1": "",'
            r'"alertedRessources": "FW KLV01 DLK23 1;\n'
            r'FW KLV Ger\u00e4tewarte;\nLZ KLV S\u00fcd;\nLZ Kleve;\n'
            r'RD KLV01 RTW 1",'
            r'"keyword_misc": "Feuer gro\u00df",'
            r'"COBRA_LOCATION_property": "",'
            r'"COBRA_LOCATION_SUBPROPERTY_5": "",'
            r'"origin": " Ackerstrasse 299, 47533 Kleve -- Alarmiert: '
            r'FW KLV01 DLK23 1;\nFW KLV Ger\u00e4tewarte;\nLZ KLV S\u00fcd;\n'
            r'LZ Kleve;\nRD KLV01 RTW 1",'
            r'"COBRA_keyword_additional_1": "Zimmerbrand",'
            r'"keyword_ident": "B3 Zimmerbrand",'
            r'"COBRA_reporter": "Müller 017612345678",'
            r'"alarmState": "NEW",'
            r'"location_dest": "Ackerstrasse 299, 47533 Kleve",'
            r'"alarmType": "ALARM",'
            r'"keyword_description": "Feuer gro\u00df",'
            r'"COBRA_id": "de0513000000kvi80klp00",'
            r'"keyword_category": "\ud83d\udd25",'
            r'"COBRA_keyword_description_1": "Feuer gro\u00df",'
            r'"postalCode": "47533",'
            r'"lng": "6.11907405",'
            r'"COBRA_LOCATION_comment": "",'
            r'"COBRA_sender_client_id": "KLE_LTS",'
            r'"COBRA_ADDITIONAL_comment": "",'
            r'"COBRA_LOCATION_section": "",'
            r'"COBRA_LOCATION_crossing": "",'
            r'"COBRA_LOCATION_floor": "",'
            r'"COBRA_receiver_client_id": "KLE_ALAMOS",'
            r'"COBRA_all_previous_alerted_resources": "",'
            r'"COBRA_reporter_phone": "017612345678",'
            r'"COBRA_ADDITIONAL_priority": "0",'
            r'"keyword_2_long": "Einsatzart: \nStichwort: \nMeldebild: \n'
            r'Klartext: ",'
            r'"building": "",'
            r'"COBRA_ADDITIONAL_comment_callback": "",'
            r'"lat": "51.77849377",'
            r'"keyword_color": "#FF0000",'
            r'"COBRA_name": "1210057913",'
            r'"COBRA_LOCATION_SUBPROPERTY_3": "",'
            r'"unit": "01 - LZ Kleve"'
            r'}')

        config = configparser.ConfigParser()
        alarm = Alarm(config)
        alarm.fromAlamos(json.loads(json_str), logger)
        mittel = set((
                EinsatzMittel('FW', 'KLV', '01', 'DLK23', '1',
                    'FW KLV01 DLK23 1'),
                EinsatzMittel('', '', '', '', '',
                    'FW KLV Gerätewarte'),
                EinsatzMittel('', '', '', '', '',
                    'LZ KLV Süd'),
                EinsatzMittel('', '', '', '', '',
                    'LZ Kleve'),
                EinsatzMittel('RD', 'KLV', '01', 'RTW', '1',
                    'RD KLV01 RTW 1')))
        self.assertEqual(alarm.einsatzmittel, mittel)
        eh = alarm.einheiten(einheit, lambda x: False, logger, sonder)
        self.assertEqual(eh, 'LZ Kleve, LZ Materborn, LG Reichswalde')
        mittel_txt = alarm.alarmiert()
        self.assertEqual(mittel_txt, ('LZ KLV Süd, LZ Kleve, '
            'FW KLV Gerätewarte, FW KLV01 DLK23 1, RD KLV01 RTW 1'))

    def test_report(self):
        pager_str = ('12-05-18 19:54:02 LG Reichswalde       '
            'Gebäudesteuerung     #K01;N5177520E0611037;*23538*'
            'B2 Brandmeldeanlage 2 **Kleve*Materborn*Kirchweg*99*'
            'KLV 02/108*Königsallee - Dorfstrasse')
        xml_str = """<?xml version="1.0" encoding="UTF-8"?>
            <daten>
            <einsatz>
            <timestamp>20180512175326</timestamp>
            <einsatznummer>1180023538</einsatznummer>
            <einsatzart>B</einsatzart>
            <einsatzstichwort>2</einsatzstichwort>
            <diagnose>Brandmeldeanlage 2</diagnose>
            <eskalation>-</eskalation>
            <besonderheit></besonderheit>
            <sondersignal>1</sondersignal>
            <meldender>F1 Feueralarm</meldender>
            <rufnummer></rufnummer>
            </einsatz>
            <einsatzort>
            <plz>[47533]</plz>
            <ort>Kleve</ort>
            <ortsteil>Materborn</ortsteil>
            <strasse>Kirchweg</strasse>
            <hausnummer>99</hausnummer>
            <objekt>
            <o_name>Seniorenheim</o_name>
            <o_nummer></o_nummer>
            <o_gefahren>
            <gefahr></gefahr>
            <brennbar></brennbar>
            <chemie></chemie>
            <radioaktiv></radioaktiv>
            </o_gefahren>
            </objekt>
            <koordinaten>POINT (6.11037019 51.77519572)</koordinaten>
            </einsatzort>
            <einsatzmittel>
            <em>
            <em_organisation></em_organisation>
            <em_ort></em_ort>
            <em_ort_zusatz></em_ort_zusatz>
            <em_typ></em_typ>
            <em_ordnungskennung></em_ordnungskennung>
            <em_opta_gesprochen>LZ Materborn</em_opta_gesprochen>
            </em>
            <em>
            <em_organisation>FW</em_organisation>
            <em_ort>KLV</em_ort>
            <em_ort_zusatz>01</em_ort_zusatz>
            <em_typ>LEITER</em_typ>
            <em_ordnungskennung>01</em_ordnungskennung>
            <em_opta_gesprochen>KLV Leiter</em_opta_gesprochen>
            </em>
            <em>
            <em_organisation>FW</em_organisation>
            <em_ort>KLV</em_ort>
            <em_ort_zusatz>02</em_ort_zusatz>
            <em_typ>LF20</em_typ>
            <em_ordnungskennung>01</em_ordnungskennung>
            <em_opta_gesprochen>KLV 2 LF20 1</em_opta_gesprochen>
            </em>
            <em>
            <em_organisation></em_organisation>
            <em_ort></em_ort>
            <em_ort_zusatz></em_ort_zusatz>
            <em_typ></em_typ>
            <em_ordnungskennung></em_ordnungskennung>
            <em_opta_gesprochen></em_opta_gesprochen>
            </em>
            <em>
            <em_organisation></em_organisation>
            <em_ort>KLV</em_ort>
            <em_ort_zusatz>01</em_ort_zusatz>
            <em_typ></em_typ>
            <em_ordnungskennung></em_ordnungskennung>
            <em_opta_gesprochen>KLV 1</em_opta_gesprochen>
            </em>
            <em>
            <em_organisation>FW</em_organisation>
            <em_ort>KLV</em_ort>
            <em_ort_zusatz>02</em_ort_zusatz>
            <em_typ>LF10</em_typ>
            <em_ordnungskennung>01</em_ordnungskennung>
            <em_opta_gesprochen>KLV 2 LF10 1</em_opta_gesprochen>
            </em>
            <em>
            <em_organisation></em_organisation>
            <em_ort></em_ort>
            <em_ort_zusatz></em_ort_zusatz>
            <em_typ></em_typ>
            <em_ordnungskennung></em_ordnungskennung>
            <em_opta_gesprochen>LZ Reichswalde</em_opta_gesprochen>
            </em>
            <em>
            <em_organisation>FW</em_organisation>
            <em_ort>KLV</em_ort>
            <em_ort_zusatz>05</em_ort_zusatz>
            <em_typ>LF10</em_typ>
            <em_ordnungskennung>01</em_ordnungskennung>
            <em_opta_gesprochen>KLV 5 LF10 1</em_opta_gesprochen>
            </em>
            </einsatzmittel>
            </daten>"""

        config = configparser.ConfigParser()

        app = PyQt5.QtWidgets.QApplication(sys.argv)

        report = AlarmReport(config, logger)

        logger.info('Load')
        alarm = Alarm(config)
        alarm.fromPager(pager_str, logger)
        alarm2 = Alarm(config)
        alarm2.fromXml(xml_str, logger)
        alarm.merge(alarm2)

        logger.info('Route')
        route = getRoute(alarm.lat, alarm.lon, config, logger)

        logger.info('Generate')
        report.generate(alarm, route)

        eh = alarm.einheiten(einheit, lambda x: False, logger)
        self.assertEqual(eh, 'LZ Kleve, LZ Materborn, LG Reichswalde')

        del app

    def test_wolfsgraben(self):
        config = configparser.ConfigParser()

        alarm = Alarm(config)
        alarm.source = 'xml'
        alarm.sources.add(alarm.source)
        now = datetime.datetime.now()
        local_tz = get_localzone()
        alarm.datetime = local_tz.localize(now)
        alarm.art = 'B'
        alarm.stichwort = '2'
        alarm.diagnose = 'Kaminbrand'
        alarm.besonderheit = 'keine Personen mehr im Gebäude'
        alarm.ortsteil = 'Reichswalde'
        alarm.strasse = 'Wolfsgraben'
        alarm.hausnummer = '11'
        alarm.ort = 'Kleve'
        alarm.lat = 51.75638
        alarm.lon = 6.11815
        alarm.meldender = 'Müller'
        alarm.rufnummer = '0179 555 364532'
        alarm.number = '1170040004'
        alarm.sondersignal = '1'
        em = EinsatzMittel('FW', 'KLV', '05', 'LF10', '1', '')
        alarm.einsatzmittel.add(em)
        em = EinsatzMittel('FW', 'KLV', '02', 'LF20', '1', '')
        alarm.einsatzmittel.add(em)
        # adding the same twice
        em = EinsatzMittel('FW', 'KLV', '02', 'LF20', '1', '')
        alarm.einsatzmittel.add(em)
        self.assertEqual(len(alarm.einsatzmittel), 2)

    def test_einsatzMittelImmutable(self):
        em = EinsatzMittel('FW', 'KLV', '02', 'LF20', '1', '')
        with self.assertRaises(AttributeError):
            em.typ = 'RD'
        with self.assertRaises(AttributeError):
            del em.typ

    def test_pommes(self):
        config = configparser.ConfigParser()
        alarm = Alarm(config)
        alarm.load('test_data/test01-1.json', logger)
        mittel = set((
                EinsatzMittel('FW', 'KLV', '01', 'DLK23', '1',
                    'FW KLV01 DLK23 1'),
                EinsatzMittel('', '', '', '', '',
                    'FW KLV Gerätewarte'),
                EinsatzMittel('', '', '', '', '',
                    'LZ KLV Süd'),
                EinsatzMittel('', '', '', '', '',
                    'FW KLV Leiter')))
        self.assertEqual(alarm.einsatzmittel, mittel)
        eh = alarm.einheiten(einheit, lambda x: False, logger, sonder)
        self.assertEqual(eh, 'LZ Kleve, LZ Materborn, LG Reichswalde')
        mittel_txt = alarm.alarmiert()
        self.assertEqual(mittel_txt, ('LZ KLV Süd, '
            'FW KLV Gerätewarte, FW KLV Leiter, FW KLV01 DLK23 1'))

        alarm2 = Alarm(config)
        alarm2.load('test_data/test01-2.dme', logger)
        alarm.merge(alarm2)

        self.assertEqual(alarm.einsatzmittel, mittel)
        eh = alarm.einheiten(einheit, lambda x: False, logger, sonder)
        self.assertEqual(eh, 'LZ Kleve, LZ Materborn, LG Reichswalde')
        mittel_txt = alarm.alarmiert()
        self.assertEqual(mittel_txt, ('LZ KLV Süd, '
            'FW KLV Gerätewarte, FW KLV Leiter, FW KLV01 DLK23 1'))

        alarm3 = Alarm(config)
        alarm3.load('test_data/test01-3.xml', logger)
        alarm.merge(alarm3)

        mittel.add(EinsatzMittel('RD', 'KLV', '01', 'RTW', '01',
            'KLV RTW 1'))
        mittel.add(EinsatzMittel('', '', '', '', '',
            'LZ KLV West'))
        mittel.add(EinsatzMittel('FW', 'KLV', '01', 'DLK23', '01',
            'KLV 1 DLK23 1'))
        mittel.add(EinsatzMittel('', 'KLV', '01', '', '',
            'KLV 1'))
        mittel.add(EinsatzMittel('FW', 'KLV', '01', 'LEITER', '01',
            'KLV Leiter'))
        self.assertEqual(alarm.einsatzmittel, mittel)
        eh = alarm.einheiten(einheit, lambda x: False, logger, sonder)
        self.assertEqual(eh, ('LZ Kleve, LZ Materborn, LZ Rindern,'
            ' LG Reichswalde, LG Donsbrüggen'))
        mittel_txt = alarm.alarmiert()
        self.assertEqual(mittel_txt, ('LZ KLV Süd, LZ KLV West, '
            'FW KLV Gerätewarte, FW KLV Leiter, FW KLV01 DLK23 1, KLV 1, '
            'KLV 1 DLK23 1, KLV Leiter, KLV RTW 1'))


#-----------------------------------------------------------------------------

if __name__ == '__main__':
    unittest.main()

#-----------------------------------------------------------------------------
