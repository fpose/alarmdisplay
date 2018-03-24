# -*- coding: utf-8 -*-

import os
import codecs
import tempfile
from Cheetah.Template import Template
import subprocess
import shutil

import Map
from LaTeX import escapeLaTeX

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
        devNull = open(os.devnull, 'w')

        targetPixmap = Map.getTargetPixmap(alarm.lat, alarm.lon,
                self.map_width, self.map_height,
                route[0], self.config, self.logger)
        targetPixmap.save(os.path.join(tempDir, 'target.png'))

        cmd = ['convert', 'target.png', 'target.eps']
        self.logger.info(u'Running %s', cmd)
        convert = subprocess.Popen(cmd, cwd = tempDir, stdout = devNull)
        convert.wait()

        if convert.returncode != 0:
            self.logger.error(u'convert failed')
            return

        routePixmap, markerRects = Map.getRoutePixmap(alarm.lat, alarm.lon,
                self.map_width, self.map_height,
                route[0], self.config, self.logger)
        routePixmap.save(os.path.join(tempDir, 'route.png'))

        cmd = ['convert', 'route.png', 'route.eps']
        self.logger.info(u'Running %s', cmd)
        convert = subprocess.Popen(cmd, cwd = tempDir, stdout = devNull)
        convert.wait()

        if convert.returncode != 0:
            self.logger.error(u'convert failed')
            return

        # Lokale Einheiten FIXME config
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
        variables['title'] = escapeLaTeX(alarm.title())
        variables['address'] = escapeLaTeX(alarm.address())
        variables['object_name'] = escapeLaTeX(alarm.objektname)
        variables['escalation'] = escapeLaTeX(alarm.eskalation)
        variables['attention'] = escapeLaTeX(alarm.attention())
        variables['location_hint'] = escapeLaTeX(alarm.ortshinweis)
        variables['contact'] = escapeLaTeX(alarm.callerInfo())
        variables['object_plan'] = escapeLaTeX(alarm.objektnummer)
        sig = 'ja'
        if alarm.sondersignal == '0':
            sig = 'nein'
        variables['signal'] = escapeLaTeX(sig)
        variables['resources'] = escapeLaTeX(alarm.einheiten(einheit,
                lambda x: False, self.logger))
        if alarm.datetime:
            variables['datetime'] = \
                alarm.datetime.strftime('%Y-%m-%d %H:%M:%S')
        else:
            variables['datetime'] = ''
        variables['number'] = escapeLaTeX(alarm.number)
        image = alarm.imageBase()
        if image:
            variables['image'] = image
        else:
            variables['image'] = ''

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

        cmd = ['latex', '-interaction=batchmode', texPath]
        self.logger.info(u'Running %s', cmd)
        latex = subprocess.Popen(cmd, cwd = tempDir, stdout = devNull,
                env = latexEnv)
        latex.wait()

        if latex.returncode != 0:
            logPath = os.path.join(tempDir, texBase) + '.log'
            self.logger.error(u'LaTeX processing failed; see log in %s',
                    logPath)
            return


        cmd = ['dvips', texBase + '.dvi']
        self.logger.info(u'Running %s', cmd)
        dvips = subprocess.Popen(cmd, cwd = tempDir, stdout = devNull)
        dvips.wait()
        devNull.close()

        if dvips.returncode != 0:
            self.logger.error(u'DVIPS processing failed.')
            return

        self.logger.info(u'Copying PS file...')

        targetDir = '.' # TODO
        psPath = os.path.join(tempDir, texBase + '.ps')
        psTarget = os.path.join(targetDir, texBase + '.ps')
        shutil.copy(psPath, psTarget)

        self.logger.info(u'Deleting temporary directory...')
        #shutil.rmtree(tempDir)

        self.logger.info(u'PS file %s was created.', psTarget)

        printOut = self.config.get("report", "print", fallback = False)
        if printOut:
            self.logger.info("Printing PS file.")

            printCmd = ['lpr']
            printer = self.config.get("report", "printer", fallback = "")
            if printer:
                printCmd.append('-P')
                printCmd.append(printer)
            options = self.config.get("report", "print_options", fallback = "")
            if options:
                for opt in options.split():
                    printCmd.append('-o')
                    printCmd.append(opt)
            printCmd.append(psTarget)

            self.logger.info("Print command: %s", repr(printCmd))

            lpr = subprocess.Popen(printCmd)
            lpr.wait()
            if lpr.returncode != 0:
                self.logger.error('lpr failed.')

            self.logger.info("Print ready.")
