# RasPipBoy: A Pip-Boy 3000 implementation for Raspberry Pi
#   Neal D Corbett, 2013
# V.A.T.S. - Shows images from Raspberry Pi Camera

import pygame
import subprocess
import io
import Image
import threading
import config
import main

import picamera  # From: https://pypi.python.org/pypi/picamera

import pipboy_headFoot as headFoot


class VATS:

    changed = True
    header = pygame.Surface((1, 1))
    page_canvas = pygame.Surface((config.WIDTH, config.HEIGHT))
    do_init = True
    show_tint = True

    class ThreadClass(threading.Thread):

        def run(self):

            self.camera = picamera.PiCamera()
            self.camera.resolution = (config.WIDTH, config.HEIGHT)
            self.camera.rotation = 90
            self.camera.brightness = 75
            self.camera.contrast = 80

            page_visible = False

            try:
                stream = io.BytesIO()

                # Continuously loops while camera is active...
                for dummy in self.camera.capture_continuous(stream, format='jpeg'):

                    # Truncate the stream to the current position (in case prior iterations output a longer image)
                    stream.truncate()
                    stream.seek(0)

                    # Only process stream if VATS page is visible:
                    if (self.root_parent.currentTab == self.parent) or (self.parent.page_canvas is None):

                        page_visible = True

                        stream_copy = io.BytesIO(stream.getvalue())
                        image = pygame.image.load(stream_copy, 'jpeg')
                        self.parent.page_canvas = image.convert()
                        self.parent.changed = True

                    # If page is no longer visible, do something?
                    elif page_visible:
                        continue
            finally:
                self.camera.close()

    def __init__(self, *args, **kwargs):

        self.parent = args[0]
        self.root_parent = self.parent.root_parent
        self.name = "V.A.T.S."

        self.header = headFoot.Header(self)

        # Create camera-read thread: (set as daemon, so it'll die with main process)
        camthread = self.ThreadClass()
        camthread.daemon = True
        camthread.parent = self
        camthread.root_parent = self.root_parent
        camthread.start()
        self.camthread = camthread

        # Generate footers for mode-pages:
        self.footer_imgs = headFoot.genFooterImgs(["Light", "Contrast", "Exposure", "Mode", "Tinted"])

    def getHeaderText(self):
        '''Generate text for header'''
        return [self.name, "", main.getTimeStr()]

    def drawPage(self, dummy_mode_num):
        pageChanged = self.changed
        self.changed = False

        if self.do_init:
            self.do_init = False

        return self.page_canvas, pageChanged

    def resetPage(self, dummy_mode_num):
        '''Called every view changes to this page'''
        if config.USE_SOUND:
            config.SOUNDS["camerastart"].play()

    def ctrlEvents(self, events, dummy_mode_num):
        '''Consume events passed to this page'''
        for event in events:
            # TAKE PHOTO:
            if event == 'sel':
                print("Snap!")
                self.changed = True
            # SCROLL-WHEEL:
            elif type(event) is list:
                scroll_val = event[2]
                print(self.root_parent.mode_num)
                if scroll_val != 0:
                    continue
