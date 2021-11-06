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
        }

#-----------------------------------------------------------------------------

class alarmdisplayTests(unittest.TestCase):

    def test_einsatzmittel(self):
        json_str = r'{"unitCode": "LZ Kleve", "COBRA_state": "ALERT", "timestamp": "1635865439209", "einsatzmittel": "FW KLV01 DLK23 1\nFW KLV Ger\u00e4tewarte\nLZ KLV S\u00fcd\nLZ Kleve\nRD KLV01 RTW 1", "userName": "Admin", "time": "16:03", "COBRA_keyword_1_text": "Brandschutz", "COBRA_keyword_2": "", "tvp": "TVPN031613beE005d5ea2", "location_dest_long": "Ackerstrasse 299, 47533 Kleve\nKreuzung: \nSektion: \nAnwesen: \nStock: \nKommentar: ", "address": "LZ Kleve", "COBRA_keyword_1": "3", "house": "299", "COBRA_keyword_additional_2": "", "city_abbr": "Kleve", "dbId": "9471fb068f4aff5554723efc7b7a9336367f660a5675f375956d66d9d3195f77", "COBRA_keyword_ident_2": "", "location_URL": "https://maps.google.de/maps?q=51.77849377,6.11907405", "COBRA_keyword_description_2": "", "COBRA_LOCATION_SUBPROPERTY_2": "", "clock_long": "16:03:58", "keyword_1_long": "Einsatzart: B\nStichwort: 3\nMeldebild: Zimmerbrand\nKlartext: Feuer gro\u00df", "COBRA_ADDITIONAL_special_rights": "Ja", "city": "Kleve", "COBRA_LOCATION_SUBPROPERTY_4": "", "pluginmessage": " Ackerstrasse 299, 47533 Kleve -- Alarmiert: FW KLV01 DLK23 1;\nFW KLV Ger\u00e4tewarte;\nLZ KLV S\u00fcd;\nLZ Kleve;\nRD KLV01 RTW 1", "COBRA_reporter_name": "Klink", "keyword": "B3 Zimmerbrand", "COBRA_ADDITIONAL_callback": "", "COBRA_keyword_ident_1": "B", "street": "Ackerstrasse", "gps": "GPSN51778494E06119074", "COBRA_LOCATION_SUBPROPERTY_1": "", "alertedRessources": "FW KLV01 DLK23 1;\nFW KLV Ger\u00e4tewarte;\nLZ KLV S\u00fcd;\nLZ Kleve;\nRD KLV01 RTW 1", "keyword_misc": "Feuer gro\u00df", "COBRA_LOCATION_property": "", "COBRA_LOCATION_SUBPROPERTY_5": "", "origin": " Ackerstrasse 299, 47533 Kleve -- Alarmiert: FW KLV01 DLK23 1;\nFW KLV Ger\u00e4tewarte;\nLZ KLV S\u00fcd;\nLZ Kleve;\nRD KLV01 RTW 1", "COBRA_keyword_additional_1": "Zimmerbrand", "keyword_ident": "B3 Zimmerbrand", "COBRA_reporter": "Klink 017641941580", "alarmState": "NEW", "location_dest": "Ackerstrasse 299, 47533 Kleve", "alarmType": "ALARM", "keyword_description": "Feuer gro\u00df", "COBRA_id": "de0513000000kvi80klp00", "keyword_category": "\ud83d\udd25", "COBRA_keyword_description_1": "Feuer gro\u00df", "postalCode": "47533", "lng": "6.11907405", "COBRA_LOCATION_comment": "", "COBRA_sender_client_id": "KLE_LTS", "COBRA_ADDITIONAL_comment": "", "COBRA_LOCATION_section": "", "COBRA_LOCATION_crossing": "", "COBRA_LOCATION_floor": "", "COBRA_receiver_client_id": "KLE_ALAMOS", "COBRA_all_previous_alerted_resources": "", "COBRA_reporter_phone": "017641941580", "COBRA_ADDITIONAL_priority": "0", "keyword_2_long": "Einsatzart: \nStichwort: \nMeldebild: \nKlartext: ", "building": "", "COBRA_ADDITIONAL_comment_callback": "", "lat": "51.77849377", "keyword_color": "#FF0000", "COBRA_name": "1210057913", "COBRA_LOCATION_SUBPROPERTY_3": "", "unit": "01 - LZ Kleve"}'

        config = configparser.ConfigParser()
        alarm = Alarm(config)
        alarm.fromAlamos(json.loads(json_str), logger)
        mittel = set((
                EinsatzMittel('FW', 'KLV', '01', 'DLK23', '1',
                    'FW KLV01 DLK23 1'),
                EinsatzMittel(None, None, None, None, None,
                    'FW KLV Gerätewarte'),
                EinsatzMittel(None, None, None, None, None,
                    'LZ KLV Süd'),
                EinsatzMittel(None, None, None, None, None,
                    'LZ Kleve'),
                EinsatzMittel('RD', 'KLV', '01', 'RTW', '1',
                    'RD KLV01 RTW 1')))
        self.assertEqual(alarm.einsatzmittel, mittel)
        eh = alarm.einheiten(einheit, lambda x: False, logger, sonder)
        self.assertEqual(eh, 'LZ Kleve, LZ Materborn, LG Reichswalde')

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
        em = EinsatzMittel('FW', 'KLV', '05', 'LF10', '1', None)
        alarm.einsatzmittel.add(em)
        em = EinsatzMittel('FW', 'KLV', '02', 'LF20', '1', None)
        alarm.einsatzmittel.add(em)
        # adding the same twice
        em = EinsatzMittel('FW', 'KLV', '02', 'LF20', '1', None)
        alarm.einsatzmittel.add(em)
        self.assertEqual(len(alarm.einsatzmittel), 2)

    def test_einsatzMittelImmutable(self):
        em = EinsatzMittel('FW', 'KLV', '02', 'LF20', '1', None)
        with self.assertRaises(AttributeError):
            em.typ = 'RD'
        with self.assertRaises(AttributeError):
            del em.typ

#-----------------------------------------------------------------------------

if __name__ == '__main__':
    unittest.main()

#-----------------------------------------------------------------------------
