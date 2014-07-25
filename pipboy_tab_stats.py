# RasPipBoy: A Pip-Boy 3000 implementation for Raspberry Pi
#   Neal D Corbett, 2013
# Class for 'Stats' tab

import pygame
import os
import time
import random
import math
import string
import numpy
from pygame.locals import *

import config
import pipboy_headFoot as headFoot


class Tab_Stats:

    name = "STATS"

    class Mode_Status:
        '''Status page includes further sub-pages...'''

        class Condition:

            changed = True
            pageListImg = None

            def __init__(self, *args, **kwargs):
                self.parent = args[0]
                self.rootParent = self.parent.rootParent
                self.name = 'CND'
                self.pageCanvas = pygame.Surface((config.WIDTH, config.HEIGHT))

            def drawPage(self):
                pageChanged = self.changed
                self.changed = False

                if pageChanged:
                    # Draw status-boy to image:
                    self.pageCanvas.fill((0, 0, 0))
                    imageSize = config.HEIGHT
                    image = config.IMAGES["statusboy"]
                    image = pygame.transform.smoothscale(image, (imageSize, imageSize))
                    self.pageCanvas.blit(image, (((config.WIDTH - imageSize) / 2), 0), None, pygame.BLEND_ADD)

                    # Print player-name/level under statusboy:
                    text = ("%s - LEVEL %s" % (config.PLAYERNAME, config.PLAYERLEVEL))
                    textImg = config.FONT_LRG.render(text, True, config.DRAWCOLOUR, (0, 0, 0))
                    self.pageCanvas.blit(textImg,
                                         ((config.WIDTH - textImg.get_width()) / 2, config.HEIGHT * 0.805),
                                         None,
                                         pygame.BLEND_ADD)

                    # Add page-list:
                    self.pageCanvas.blit(self.pageListImg, (0, 0), None, pygame.BLEND_ADD)

                return self.pageCanvas, pageChanged

            def resetPage(self):
                '''Called every view changes to this sub-page:'''
                True

            def ctrlEvents(self, events):
                '''Consume events passed to this sub-page:'''
                True

        class StatLine:
            '''Used for line-based stats:'''

            changed = True
            firstDraw = True

            # Default values:
            curVal = -1
            minVal = 0
            maxVal = 100

            setVal = maxVal
            frameNum = 0

            def __init__(self, *args, **kwargs):
                self.parent = args[0]
                self.rootParent = self.parent.rootParent
                self.name = args[1]
                self.pageCanvas = pygame.Surface((config.WIDTH, config.HEIGHT))

            def updateStatus(self):
                newVal = -1

                if self.name == 'BAT':    # Show Battery status

                    newVal = self.setVal

                    if config.USE_SERIAL:
                        # Only do this every so often...
                        if self.frameNum == 0:
                            # Send query to Teensy to get current battery voltage:
                            self.rootParent.ser.write("volts\n")
                            # (value is returned and set via page-events queue)
                        elif self.frameNum == 15:
                            self.frameNum = -1
                        self.frameNum += 1

                elif self.name == 'TMP':  # Show Temperature

                    newVal = self.setVal

                    if config.USE_SERIAL:
                        # Only do this every so often...
                        if self.frameNum == 0:
                            # Send query to Teensy to get current temperature:
                            self.rootParent.ser.write("temp\n")
                            # (value is returned and set via page-events queue)
                        elif self.frameNum == 15:
                            self.frameNum = -1
                        self.frameNum += 1

                elif self.name == 'WAN':  # Show WiFi signal-level
                    newVal = 0
                    if config.USE_INTERNET:
                        # Get relevant line from proc:
                        line = ""
                        try:
                            with open('/proc/net/wireless', 'r') as f:
                                f.readline()
                                f.readline()
                                line = f.readline()

                            # Get 'Quality:Level' value:
                            tokens = string.split(line)
                            token = tokens[3]
                            token = string.replace(token, ".", "")
                            newVal = string.atoi(token)
                        except:
                            pass
                else:
                    newVal = self.minVal

                if newVal != self.curVal:
                    self.curVal = newVal
                    self.changed = True

            def drawPage(self):

                # Draw initial line-gauge:
                if self.firstDraw:

                    self.firstDraw = False
                    img = self.pageListImg

                    cornerPadding = headFoot.cornerPadding
                    charWidth = config.charWidth
                    charHeight = config.charHeight

                    lineY = (config.HEIGHT * 0.66)
                    lineYDn = (lineY + (charHeight * 1.6))
                    lineDnAX = (config.WIDTH * 0.33)
                    lineRtX = (config.WIDTH - cornerPadding)

                    # Draw page-name under gauge:
                    textImg = config.FONT_LRG.render(self.name, True, config.DRAWCOLOUR, (0, 0, 0))
                    img.blit(textImg, (lineDnAX + 6, lineY + 4))

                    pygame.draw.lines(img,
                                      config.DRAWCOLOUR,
                                      False,
                                      [(cornerPadding, lineY), (lineDnAX, lineY), (lineDnAX, lineYDn)],
                                      2)
                    pygame.draw.lines(img,
                                      config.DRAWCOLOUR,
                                      False,
                                      [(lineDnAX + 6, lineY), (lineRtX, lineY), (lineRtX, lineYDn)],
                                      2)

                    # Draw subdivision-lines:
                    divHeight = (charHeight * 0.6)
                    gaugeStartX = (config.WIDTH * 0.5)
                    gaugeEndX = (lineRtX - (divHeight * 2))

                    self.gaugeStartX = gaugeStartX
                    self.gaugeEndX = gaugeEndX

                    divWidth = (gaugeEndX - gaugeStartX) / 15
                    divPosX = gaugeStartX
                    divYA = (lineY + divHeight)
                    divYB = (lineY + (divHeight * 0.3))

                    # Set up values for drawing pointer-arrow later:
                    self.arrowTopY = (lineY + divHeight)
                    self.arrowHeadX = (divHeight * 0.65)
                    self.arrowHeadY = (self.arrowTopY + (self.arrowHeadX))
                    self.arrowBtmY = (self.arrowHeadY + (2 * divHeight))
                    self.arrowTextY = (self.arrowBtmY - (0.9 * config.charHeight))

                    for n in range(0, 5):
                        for n in range(0, 2):
                            divPosX += divWidth
                            pygame.draw.lines(img, config.DRAWCOLOUR, False, [(divPosX, lineY), (divPosX, divYB)], 2)

                        divPosX += divWidth
                        if divPosX < self.gaugeEndX:
                            pygame.draw.lines(img, config.DRAWCOLOUR, False, [(divPosX, lineY), (divPosX, divYA)], 2)

                    # Draw range-end triangles:
                    pygame.draw.polygon(img,
                                        config.DRAWCOLOUR,
                                        [
                                            (gaugeStartX, lineY),
                                            (gaugeStartX, lineY+divHeight),
                                            (gaugeStartX-divHeight, lineY)
                                        ],
                                        0)
                    pygame.draw.polygon(img,
                                        config.DRAWCOLOUR,
                                        [
                                            (gaugeEndX, lineY),
                                            (gaugeEndX, lineY+divHeight),
                                            (gaugeEndX+divHeight, lineY)
                                        ],
                                        0)
                else:
                    # Only bother acquiring stats after first page-draw call...
                    self.updateStatus()

                pageChanged = self.changed
                self.changed = False

                if pageChanged:
                    self.pageCanvas = self.pageListImg.convert()

                    # Draw value arrow/text:
                    valXPos = int(numpy.interp(self.curVal,
                                               [self.minVal, self.maxVal], [self.gaugeStartX, self.gaugeEndX]))

                    textImg = config.FONT_LRG.render(str(self.curVal), True, config.DRAWCOLOUR, (0, 0, 0))
                    textPosX = (valXPos - self.arrowHeadX - textImg.get_width() + 2)
                    self.pageCanvas.blit(textImg, (textPosX, self.arrowTextY))

                    pygame.draw.polygon(self.pageCanvas,
                                        config.DRAWCOLOUR,
                                        [
                                            (valXPos, self.arrowTopY),
                                            (valXPos-self.arrowHeadX, self.arrowHeadY),
                                            (valXPos+self.arrowHeadX, self.arrowHeadY)
                                        ],
                                        0)
                    valXPos -= 1
                    pygame.draw.lines(self.pageCanvas,
                                      config.DRAWCOLOUR,
                                      False,
                                      [(valXPos, self.arrowHeadY), (valXPos, self.arrowBtmY)],
                                      2)

                return self.pageCanvas, pageChanged

            def resetPage(self):
                '''Called every view changes to this sub-page:'''
                True

            def ctrlEvents(self, events):
                '''Consume events passed to this sub-page:'''

                if self.name == 'BAT':    # Get battery-status events
                    for event in events:
                        if (type(event) is str) and (event.startswith('volts')):
                            print(event)   # DEBUG PRINT
                            tokens = string.split(event)

                            batVolts = float(tokens[1])
                            minVolts = 6.30
                            maxVolts = 7.68
                            self.setVal = int(100 * ((batVolts - minVolts) / (maxVolts - minVolts)))
                elif self.name == 'TMP':  # Get temperature-status events
                    for event in events:
                        if (type(event) is str) and (event.startswith('temp')):
                            print(event)  # DEBUG PRINT
                            tokens = string.split(event)

                            tempVal = float(tokens[1])
                            minTemp = -40.0
                            maxTemp = 125.0
                            self.setVal = tempVal
                            # int(100 * ((tempVal - minTemp) / (maxTemp - minTemp)));

        ######################################

        changed = True
        subPageNum = 0
        curSubPage = None

        def __init__(self, *args, **kwargs):
            self.parent = args[0]
            self.rootParent = self.parent.rootParent
            self.name = "Status"

            # Set up list of sub-pages:
            Condition = self.Condition
            StatLine = self.StatLine
            self.subPages = [Condition(self),
                             StatLine(self, 'RAD'),
                             StatLine(self, 'TMP'),
                             StatLine(self, 'BAT'),
                             StatLine(self, 'WAN'),
                             StatLine(self, 'GPS')]

            # Generate list-image for each sub-page:
            for thisPageNum, page in enumerate(self.subPages):

                thisPage = self.subPages[thisPageNum]
                thisPage.pageListImg = pygame.Surface((config.WIDTH, config.HEIGHT))

                TextX = (config.charWidth * 2.9)
                TextY = (config.charHeight * 3)

                # Draw page-names, with box around selected one
                for subPageNum, page in enumerate(self.subPages):

                    doSelBox = (subPageNum == thisPageNum)

                    BackColour = None
                    if doSelBox:
                        BoxColour = (config.SELBOXGREY, config.SELBOXGREY, config.SELBOXGREY)

                    thisText = self.subPages[subPageNum].name
                    # print(thisText)

                    textImg = config.FONT_LRG.render(thisText, True, config.DRAWCOLOUR, (0, 0, 0))

                    TextWidth = (textImg.get_width())
                    textPos = (TextX, TextY)

                    if doSelBox:
                        TextRect = (TextX - 2, TextY - 2, TextWidth + 4, config.charHeight + 4)
                        pygame.draw.rect(thisPage.pageListImg, BoxColour, TextRect, 0)
                        TextRect = (TextRect[0] - 2, TextRect[1], TextRect[2] + 2, TextRect[3])
                        pygame.draw.rect(thisPage.pageListImg, config.DRAWCOLOUR, TextRect, 2)

                    thisPage.pageListImg.blit(textImg, textPos, None, pygame.BLEND_ADD)

                    TextY += (config.charHeight * 1.5)

                # Do initial page-draw, caching for later use:
                thisPage.drawPage()

        def drawPage(self):
            # Pass sub-page canvas up to tab-draw function...
            subPageCanvas, subPageChanged = self.curSubPage.drawPage()

            pageChanged = (self.changed or subPageChanged)
            self.changed = False

            return subPageCanvas, pageChanged

        def resetPage(self):
            '''Called every time view changes to this page:'''
            self.subPageNum = 0
            self.curSubPage = self.subPages[self.subPageNum]

        def ctrlEvents(self, events):
            '''Consume events passed to this page:'''

            for event in events:

                # Arrow-keys change subpage-number:
                if type(event) is list:

                    listMove = event[2]
                    newPageNum = self.subPageNum - listMove

                    if newPageNum < 0:
                        newPageNum = 0
                    elif newPageNum >= len(self.subPages):
                        newPageNum = len(self.subPages) - 1

                    if newPageNum != self.subPageNum:
                        if config.USE_SOUND:
                            config.SOUNDS["changemode"].play()
                        self.subPageNum = newPageNum
                        self.curSubPage = self.subPages[newPageNum]
                        self.changed = True

            # Pass events to subpage too, just in case I've set them up as consumers too:
            self.curSubPage.ctrlEvents(events)

    class Mode_SPECIAL:

        changed = True

        def __init__(self, *args, **kwargs):
            self.parent = args[0]
            self.rootParent = self.parent.rootParent
            self.name = "S.P.E.C.I.A.L."
            self.pageCanvas = pygame.Surface((config.WIDTH, config.HEIGHT))

        def drawPage(self):
            pageChanged = self.changed
            self.changed = False
            if pageChanged:
                True
            return self.pageCanvas, pageChanged

        def resetPage(self):
            '''Called every view changes to this page:'''
            True

        def ctrlEvents(self, events):
            '''Consume events passed to this page:'''
            True

    class Mode_Skills:

        changed = True

        def __init__(self, *args, **kwargs):
            self.parent = args[0]
            self.rootParent = self.parent.rootParent
            self.name = "Skills"
            self.pageCanvas = pygame.Surface((config.WIDTH, config.HEIGHT))

        def drawPage(self):
            pageChanged = self.changed
            self.changed = False
            if pageChanged:
                True
            return self.pageCanvas, pageChanged

        def resetPage(self):
            '''Called every view changes to this page:'''
            True

        def ctrlEvents(self, events):
            '''Consume events passed to this page:'''
            True

    class Mode_Perks:

        changed = True

        def __init__(self, *args, **kwargs):
            self.parent = args[0]
            self.rootParent = self.parent.rootParent
            self.name = "Perks"
            self.pageCanvas = pygame.Surface((config.WIDTH, config.HEIGHT))

        def drawPage(self):
            pageChanged = self.changed
            self.changed = False
            if pageChanged:
                True
            return self.pageCanvas, pageChanged

        def resetPage(self):
            '''Called every view changes to this page:'''
            True

        def ctrlEvents(self, events):
            '''Consume events passed to this page:'''
            True

    class Mode_General:

        changed = True

        def __init__(self, *args, **kwargs):
            self.parent = args[0]
            self.rootParent = self.parent.rootParent
            self.name = "General"
            self.pageCanvas = pygame.Surface((config.WIDTH, config.HEIGHT))

        def drawPage(self):
            pageChanged = self.changed
            self.changed = False
            if pageChanged:
                True
            return self.pageCanvas, pageChanged

        def resetPage(self):
            '''Called every view changes to this page:'''
            True

        def ctrlEvents(self, events):
            '''Consume events passed to this page:'''
            True

    def getHeaderText(self):
        '''Generate text for header:'''
        return [self.name, "LVL %s" % (config.PLAYERLEVEL), "HP 210/210", "AP 92/92", "XP 719/1000"]

    def drawPage(self, modeNum):
        '''Trigger page-functions'''
        pageCanvas, pageChanged = self.modes[modeNum].drawPage()
        return pageCanvas, pageChanged

    def resetPage(self, modeNum):
        self.modes[modeNum].resetPage()

    def ctrlEvents(self, pageEvents, modeNum):
        self.modes[modeNum].ctrlEvents(pageEvents)

    # Tab init:
    def __init__(self, *args, **kwargs):
        self.parent = args[0]
        self.rootParent = self.parent.rootParent
        self.canvas = pygame.Surface((config.WIDTH, config.HEIGHT))
        self.drawnPageNum = -1

        self.modes = [self.Mode_Status(self),
                      self.Mode_SPECIAL(self),
                      self.Mode_Skills(self),
                      self.Mode_Perks(self),
                      self.Mode_General(self)]

        self.modeNames = ["", "", "", "", ""]
        for n in range(0, 5):
            self.modeNames[n] = self.modes[n].name

        self.header = headFoot.Header(self)

        # Generate footers for mode-pages:
        self.footerImgs = headFoot.genFooterImgs(self.modeNames)
