# -*- coding: utf-8 -*-

#-----------------------------------------------------------------------------
#
# Alarm Report
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
import codecs
import tempfile
from Cheetah.Template import Template
import subprocess
import shutil

import Map
from LaTeX import escapeLaTeX

#-----------------------------------------------------------------------------

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

        cmd = ['convert', 'target.png', 'eps3:target.eps']
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

        cmd = ['convert', 'route.png', 'eps3:route.eps']
        self.logger.info(u'Running %s', cmd)
        convert = subprocess.Popen(cmd, cwd = tempDir, stdout = devNull)
        convert.wait()

        if convert.returncode != 0:
            self.logger.error(u'convert failed')
            return

        variables = {}

        logo = self.config.get("report", "logo", fallback = None)
        if logo:
            variables['logo'] = logo
        else:
            variables['logo'] = ''

        variables['title'] = escapeLaTeX(alarm.title())
        variables['address'] = escapeLaTeX(alarm.address())
        variables['object_name'] = escapeLaTeX(alarm.objektname)
        esc = alarm.eskalation
        if esc == '-':
            esc = ''
        variables['escalation'] = escapeLaTeX(esc)
        variables['attention'] = escapeLaTeX(alarm.attention())
        variables['location_hint'] = escapeLaTeX(alarm.ortshinweis)
        variables['contact'] = escapeLaTeX(alarm.callerInfo())
        variables['object_plan'] = escapeLaTeX(alarm.objektnummer)
        sig = 'ja'
        if alarm.sondersignal == '0':
            sig = 'nein'
        variables['signal'] = escapeLaTeX(sig)
        einh = alarm.alarmiert()
        variables['resources'] = escapeLaTeX(einh)
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
            inputs += ':' + os.path.abspath(path)
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
        dvips = subprocess.Popen(cmd, cwd = tempDir, stdout = devNull,
                stderr = devNull)
        dvips.wait()
        devNull.close()

        if dvips.returncode != 0:
            self.logger.error(u'DVIPS processing failed.')
            return

        psPath = os.path.join(tempDir, texBase + '.ps')
        self.logger.info(u'PS file %s was created.', psPath)

        printOut = self.config.getboolean("report", "print", fallback = False)
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
            copies = self.config.getint("report", "copies", fallback = 1)
            if copies != 1:
                printCmd.append('-#')
                printCmd.append(str(copies))
            printCmd.append(psPath)

            self.logger.info("Print command: %s", repr(printCmd))

            lpr = subprocess.Popen(printCmd)
            lpr.wait()
            if lpr.returncode != 0:
                self.logger.error('lpr failed.')

            self.logger.info("Print ready.")

        self.logger.info(u'Copying PS file...')

        targetDir = self.config.get("report", "output_dir", fallback = ".")

        psTarget = os.path.join(targetDir, alarm.dateString() + '.ps')
        shutil.copy(psPath, psTarget)
        self.logger.info(u'PS file copied to %s.', psTarget)

        self.logger.info(u'Deleting temporary directory.')
        shutil.rmtree(tempDir)

    def wakeupPrinter(self):
        printOut = self.config.getboolean("report", "print", fallback = False)
        wakeupDoc = self.config.get("report", "wakeup_document",
                fallback = "")

        if not printOut or not wakeupDoc:
            return

        self.logger.info("Waking up printer.")

        printCmd = ['lpr']
        printer = self.config.get("report", "printer", fallback = "")
        if printer:
            printCmd.append('-P')
            printCmd.append(printer)
        printCmd.append(wakeupDoc)

        self.logger.info("Wakeup command: %s", repr(printCmd))

        lpr = subprocess.Popen(printCmd)
        lpr.wait()
        if lpr.returncode != 0:
            self.logger.error('Wakeup failed.')

        self.logger.info("Wakeup succeeded.")

#-----------------------------------------------------------------------------
