# RasPipBoy: A Pip-Boy 3000 implementation for Raspberry Pi
#   Neal D Corbett, 2013
# Class for 'Data' tab

import pygame

import main
import config
import pipboy_headFoot as headFoot

import pipboy_tab_data_maps as dataMap
import pipboy_tab_data_radio as radio


class Tab_Data:

    name = "DATA"

    class Mode_Quests:

        changed = True

        def __init__(self, *args, **kwargs):
            self.parent = args[0]
            self.rootParent = self.parent.rootParent
            self.name = "Quests"
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

    class Mode_Misc:

        changed = True

        def __init__(self, *args, **kwargs):
            self.parent = args[0]
            self.rootParent = self.parent.rootParent
            self.name = "Misc"
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

    # Generate text for header:
    def getHeaderText(self):
        return [self.name, self.rootParent.gpsModule.locality, main.getTimeStr(),]

    # Trigger page-functions
    def drawPage(self, modeNum):
        pageCanvas, pageChanged = self.modes[modeNum].drawPage()
        return pageCanvas, pageChanged

    def resetPage(self, modeNum):
        self.modes[modeNum].resetPage()

    def ctrlEvents(self, pageEvents, modeNum):
        self.modes[modeNum].ctrlEvents(pageEvents)

    def __init__(self, *args, **kwargs):
        self.parent = args[0]
        self.rootParent = self.parent.rootParent
        self.canvas = pygame.Surface((config.WIDTH, config.HEIGHT))
        self.drawnPageNum = -1

        self.modes = [dataMap.Mode_Map(self, 0), dataMap.Mode_Map(self, 1), self.Mode_Quests(self), self.Mode_Misc(self), radio.Mode_Radio(self)]

        # Generate footers for mode-pages:
        self.modeNames = ["", "", "", "", ""]
        for n in range(0, 5):
            self.modeNames[n] = self.modes[n].name

        self.header = headFoot.Header(self)

        # Generate footers for mode-pages:
        self.footerImgs = headFoot.genFooterImgs(self.modeNames)
