# RasPipBoy: A Pip-Boy 3000 implementation for Raspberry Pi
#   Neal D Corbett, 2013
# Screen header/footer

import pygame
import config
import main

cornerPadding = 10


class Header:

    headerStrings = []

    def __init__(self, *args, **kwargs):
        self.parent = args[0]
        self.rootParent = self.parent.rootParent
        self.canvas = pygame.Surface((config.WIDTH, config.HEIGHT))

    def drawHeader(self):
        self.canvas.fill((0, 0, 0))
        headerStrings = self.headerStrings

        # Draw lines:
        lineDn = (cornerPadding + (config.charHeight * 1.6))
        midLineDn = (cornerPadding + (config.charHeight * 1.2))
        lineX = config.WIDTH - cornerPadding

        HalfCharHeight = (config.charHeight / 2)
        TitleTextY = (cornerPadding - HalfCharHeight)
        TextPad = ((lineDn - cornerPadding) / 2) - HalfCharHeight
        UnderTextY = cornerPadding + TextPad

        # Draw header-text list in reverse order, from right to left:
        rightIdx = (len(headerStrings)-1)
        for n in range(rightIdx, -1, -1):

            thisText = headerStrings[n]
            textImg = config.FONT_LRG.render(thisText, True, config.DRAWCOLOUR)

            TextWidth = (textImg.get_width())
            TextHeight = (textImg.get_height())
            TextX, TextY = 0, 0

            if n == 0:
                TextX = lineDn
                TextY = TitleTextY

                TextRect = (TextX - 2, TextY - 2, TextWidth + 4, config.charHeight + 4)
                pygame.draw.rect(self.canvas, (0, 0, 0), TextRect, 0)
            else:
                TextX = (lineX - TextPad - TextWidth)
                TextY = UnderTextY

                thisLineDn = midLineDn
                if n == rightIdx:
                    thisLineDn = lineDn

                if n == 1:
                    pygame.draw.lines(self.canvas, config.DRAWCOLOUR, False, [(lineX, thisLineDn), (lineX, cornerPadding), (cornerPadding, cornerPadding), (cornerPadding, lineDn), ], 2)
                else:
                    lineLeft = (TextX - TextPad)
                    pygame.draw.lines(self.canvas, config.DRAWCOLOUR, False, [(lineX, thisLineDn), (lineX, cornerPadding), (lineLeft, cornerPadding)], 2)

            self.canvas.blit(textImg, (TextX, TextY))

            lineX = (lineLeft - 6)
        return self.canvas

    def getHeader(self):

        newHeaderStrings = self.parent.getHeaderText()
        changed = (newHeaderStrings != self.headerStrings)

        # Only redraw header if text has changed:
        if changed:
            self.headerStrings = newHeaderStrings
            self.drawHeader()

        return self.canvas, changed


def genFooterImgs(ModeNames):
    '''Generates footer-image'''

    footerImgs = []

    for thisModeNum, mode_name in enumerate(ModeNames):
        img = pygame.Surface((config.WIDTH, config.HEIGHT))
        footerImgs.append(img)

        TextXPadding = (config.charHeight * 1)
        TextCentreDiff = ((config.WIDTH - (TextXPadding * 2)) / 5)
        TextCentreX = TextXPadding + (TextCentreDiff / 2)
        TextY = (config.HEIGHT - config.charHeight - 4)

        # Draw lines:
        btmPad = config.HEIGHT - cornerPadding
        rgtPad = config.WIDTH - cornerPadding
        lineUp = (btmPad - (config.charHeight * 1.6))
        pygame.draw.lines(img, config.DRAWCOLOUR, False,
                          [
                              (cornerPadding, lineUp),
                              (cornerPadding, btmPad),
                              (rgtPad, btmPad),
                              (rgtPad, lineUp)
                          ], 2)

        # Draw mode-names, with box around selected one
        for ModeNum in range(0, 5):

            doSelBox = (ModeNum == thisModeNum)
            BoxGrey = 0
            if doSelBox:
                BoxGrey = config.SELBOXGREY
            BoxColour = (BoxGrey, BoxGrey, BoxGrey)

            thisText = ModeNames[ModeNum]
            # print(thisText)

            textImg = config.FONT_LRG.render(thisText, True, config.DRAWCOLOUR, BoxColour)

            TextWidth = (textImg.get_width())
            TextX = (TextCentreX - (TextWidth / 2))
            textPos = (TextX, TextY)

            TextRect = (TextX - 2, TextY - 2, TextWidth + 4, config.charHeight + 4)
            pygame.draw.rect(img, BoxColour, TextRect, 0)
            if doSelBox:
                TextRect = (TextRect[0] - 2, TextRect[1], TextRect[2] + 2, TextRect[3])
                pygame.draw.rect(img, config.DRAWCOLOUR, TextRect, 2)
            img.blit(textImg, textPos)

            TextCentreX += TextCentreDiff

    return footerImgs
