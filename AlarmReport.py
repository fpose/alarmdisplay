# -*- coding: utf-8 -*-

import os
import codecs
import tempfile
from Cheetah.Template import Template
import subprocess
import shutil

import Map

class AlarmReport:

    def __init__(self, config, logger):
        self.config = config
        self.logger = logger

        res = 200 / 25.4 # [px / mm]
        self.map_width = res * 120
        self.map_height = res * 120

        # Load Template
        templateDir = self.config.get("report", "template_dir",
                fallback = "report")
        templatePath = os.path.join(templateDir, 'template.tex')
        templateFile = codecs.open(templatePath, encoding="utf-8", mode = 'r')
        self.template = templateFile.read()
        templateFile.close()

    def generate(self, alarm, route):

        tempDir = tempfile.mkdtemp(prefix = 'alarm-')

        targetPixmap = Map.getTargetPixmap(alarm.lat, alarm.lon,
                self.map_width, self.map_height,
                route[0], self.config, self.logger)
        targetPixmap.save(os.path.join(tempDir, 'target.png'))

        routePixmap, markerRects = Map.getRoutePixmap(alarm.lat, alarm.lon,
                self.map_width, self.map_height,
                route[0], self.config, self.logger)
        routePixmap.save(os.path.join(tempDir, 'route.png'))

        # Lokale Einheiten
        einheit = {
            u'01': u'LZ Kleve',
            u'02': u'LZ Materborn',
            u'03': u'LZ Kellen',
            u'04': u'LZ Rindern',
            u'05': u'LG Reichswalde',
            u'06': u'LG Donsbrüggen',
            u'07': u'LG Wardhausen-Brienen',
            u'08': u'LG Griethausen',
            u'09': u'LG Düffelward',
            u'10': u'LG Keeken',
            u'11': u'LG Schenkenschanz',
            u'12': u'LG Warbeyen'
            }

        variables = {}
        variables['title'] = alarm.title()
        variables['address'] = alarm.address()
        variables['attention'] = alarm.attention()
        variables['location_hint'] = alarm.objektname
        variables['contact'] = alarm.meldender
        variables['object_plan'] = alarm.objektnummer
        variables['signal'] = alarm.sondersignal
        variables['resources'] = alarm.einheiten(einheit,
                lambda x: False, self.logger)
        if alarm.datetime:
            variables['datetime'] = \
                alarm.datetime.strftime('%Y-%m-%d %H:%M:%S')
        else:
            variables['datetime'] = ''
        variables['number'] = alarm.number

        try:
            templateOutput = Template(self.template, searchList = variables)
        except:
            self.logger.error('Failed to process template', exc_info = True)
            return

        texBase = 'alarm'
        texPath = os.path.join(tempDir, texBase) + '.tex'
        self.logger.info(u'Creating LaTeX file %s', texPath)

        outFile = codecs.open(texPath, encoding='utf-8', mode = 'w')
        outFile.write(str(templateOutput))
        outFile.close()

        self.logger.info(u'Starting LaTeX processing...')

        templateDir = self.config.get("report", "template_dir",
                fallback = "report")
        imageDir = self.config.get("display", "image_dir",
                fallback = "images")
        inputPaths = [templateDir, imageDir]
        inputs = '.:'
        for path in inputPaths:
            inputs += ':' + path
        latexEnv = os.environ
        self.logger.info(u'TEXINPUTS=%s', inputs)
        latexEnv['TEXINPUTS'] = inputs

        devNull = open(os.devnull, 'w')

        cmd = ['pdflatex', '-interaction=batchmode', texPath]
        self.logger.info(u'Running %s', cmd)
        latex = subprocess.Popen(cmd, cwd = tempDir, stdout = devNull,
                env = latexEnv)
        latex.wait()
        devNull.close()

        if latex.returncode != 0:
            logPath = os.path.join(tempDir, texBase) + '.log'
            self.logger.error(u'LaTeX processing failed; see log in %s',
                    logPath)
            return

        self.logger.info(u'Copying PDF file...')

        targetDir = '.' # TODO
        pdfPath = os.path.join(tempDir, texBase + '.pdf')
        pdfTarget = os.path.join(targetDir, texBase + '.pdf')
        shutil.copy(pdfPath, pdfTarget)

        self.logger.info(u'Deleting temporary directory...')
        shutil.rmtree(tempDir)

        self.logger.info(u'PDF file %s was created.', pdfTarget)

        printImmediately = False # TODO
        if printImmediately:
            self.logger.info("Printing PDF file.")
            lpr = subprocess.Popen(['lpr', pdfTarget])
            lpr.wait()
            if lpr.returncode != 0:
                self.logger.error('lpr failed.')
