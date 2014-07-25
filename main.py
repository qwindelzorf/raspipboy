# RasPipBoy: A Pip-Boy 3000 implementation for Raspberry Pi
#   Neal D Corbett, 2013
# Main file

import pygame
import os
import time
import random
import math
import datetime
from pygame.locals import *
import config

from pipboy_gps import *
from pipboy_tab_stats import *
from pipboy_tab_items import *
from pipboy_tab_data import *
from pipboy_cmdline import *

# Load optional libraries: (these will have been tested by config.py)
if config.USE_SERIAL:
    global serial
    import serial
if config.USE_CAMERA:
    from pipboy_camera import *


def getTimeStr():
    curTime = time.localtime(time.time())
    curTimeStr = "%s.%s.%s, %s:%s" % (curTime.tm_mday,
                                      curTime.tm_mon,
                                      curTime.tm_year,
                                      curTime.tm_hour,
                                      '%02d' % curTime.tm_min)
    return curTimeStr


class Engine:

    # Default page-settings:
    torch_mode = False
    tab_num = 0
    mode_num = 0
    ser_buffer = ""

    background = None

    def __init__(self, *dummy_args, **dummy_kwargs):

        if config.USE_SERIAL:
            self.ser = config.ser
            True  # self.ser.write("gaugeMode=2")

        print("Init pygame:")
        pygame.init()
        pygame.display.init()
        print("(done)")

        self.root_parent = self
        self.screen_size = (pygame.display.Info().current_w, pygame.display.Info().current_h)
        self.canvas_size = (config.WIDTH, config.HEIGHT)

        print('Resolution: {0}x{1}'.format(self.screen_size[0], self.screen_size[1]))
        print('Canvas Size: {0}x{1}'.format(self.canvas_size[0], self.canvas_size[1]))

        # Don't show mouse-pointer:
        pygame.mouse.set_visible(0)
        pygame.display.set_mode(self.screen_size, pygame.FULLSCREEN)

        # Block queuing for unused events:
        pygame.event.set_blocked(None)
        for ev in (QUIT, KEYDOWN, MOUSEMOTION, MOUSEBUTTONDOWN):
            pygame.event.set_allowed(ev)

        # Set up gps, clock, tab-list:
        self.gpsmodule = GpsModuleClass()
        self.clock = pygame.time.Clock()

        if config.USE_CAMERA:
            self.tabs = (Tab_Stats(self), VATS(self), Tab_Data(self))
        else:
            self.tabs = (Tab_Stats(self), Tab_Items(self), Tab_Data(self))

        self.current_tab = self.tabs[self.tab_num]

        self.screen = pygame.display.set_mode(self.screen_size)

        self.background = config.IMAGES["background"]
        self.background = pygame.transform.smoothscale(self.background, self.canvas_size)

        # Lighten background:
        backadd = 30
        self.background.fill((backadd, backadd, backadd), None, pygame.BLEND_RGB_ADD)

        # Untextured background:
        # self.background = pygame.Surface(self.canvas_size)
        # greyback = 100
        # self.background.fill((greyback,greyback,greyback))

        self.background = self.background.convert()

        # Scanlines:
        scanline = config.IMAGES["scanline"]
        line_count = 60  # 48 60 80
        line_height = config.HEIGHT / line_count
        scanline = pygame.transform.smoothscale(scanline, (config.WIDTH, line_height))

        self.scanlines = pygame.Surface(self.canvas_size)
        y_pos = 0
        while y_pos < config.HEIGHT:
            self.scanlines.blit(scanline, (0, y_pos))
            y_pos += line_height

        # Increase contrast, darken:
        self.scanlines.blit(self.scanlines, (0, 0), None, pygame.BLEND_RGB_MULT)

        # scan_mult = 0.5
        scan_mult = 0.7
        scan_multcolor = (scan_mult * 255, scan_mult * 255, scan_mult * 255)
        self.scanlines.fill(scan_multcolor, None, pygame.BLEND_RGB_MULT)
        self.scanlines = self.scanlines.convert()

        # Start humming sound:
        if config.USE_SOUND:
            config.SOUNDS["start"].play()
            self.humsound = config.SOUNDS["hum"]
            self.humsound.play(loops=-1)
            self.humvolume = self.humsound.get_volume()

        # Set up data for generating overlay frames
        dostort_line = config.IMAGES["distort"]
        dostort_line_height = (config.HEIGHT / 4)
        dostort_line = pygame.transform.smoothscale(dostort_line, (config.WIDTH, dostort_line_height))
        dostort_line = dostort_line.convert()
        distort_y = -dostort_line_height
        distort_speed = (config.HEIGHT / 40)
        self.overlay_frames = []

        print("START")

        cmdline = CmdLineClass(self)

        boot_print_queue = [
            "WELCOME TO ROBCO INDUSTRIES (TM) TERMLINK",
            ">SET TERMINAL/INQUIRE",
            "",
            "RIT-V300",
            "",
            ">SET FILE/PROTECTION=OWNER:RWED ACCOUNTS.F",
            ">SET HALT RESTART/MAINT",
            "",
            "Initializing Robco Industries(TM) MF Boot Agent v2.3.0",
            "RETROS BIOS",
            "RBIOS-4.02.08.00 52EE5.E7.E8",
            "Copyright 2201-2203 Robco Ind.",
            "Uppermem: 64 KB",
            "Root (5A8)",
            "Maintenance Mode",
            "",
            ">RUN DEBUG/ACCOUNTS.F",
            "**cls",
            "ROBCO INDUSTRIES UNIFIED OPERATING SYSTEM",
            "COPYRIGHT 2075-2077 ROBCO INDUSTRIES",
            "",
        ]

        # Print Robco boot-up text, interleaving lines with overlay-frame generation:
        line_num = 0
        can_print = True
        gen_overlays = True
        while can_print or gen_overlays:
            will_print = (line_num < len(boot_print_queue))
            if can_print:
                this_line = boot_print_queue[line_num]
                cmdline.printText(this_line)

                line_num += 1
                can_print = (line_num < len(boot_print_queue))

            # Generate overlays until all required frames are done:
            if gen_overlays:
                if distort_y < config.HEIGHT:
                    # Use scanlines as base:
                    this_frame = self.scanlines.convert()

                    # Add animated distortion-line:
                    this_frame.blit(dostort_line, (0, distort_y), None, pygame.BLEND_RGB_ADD)

                    # Tint screen:
                    this_frame.fill(config.TINTCOLOUR, None, pygame.BLEND_RGB_MULT)

                    this_frame = this_frame.convert()
                    self.overlay_frames.append(this_frame)

                    distort_y += distort_speed
                else:
                    gen_overlays = False

        self.anim_delay_frames = len(self.overlay_frames)
        self.overlay_frames_count = (2 * self.anim_delay_frames)
        self.frame_num = 0

        print("END GENERATE")

        # Get coordinates:
        self.gpsmodule.getCoords(cmdline)

        # Initial map-downloads:
        cmdline.printText(">MAPS.DOWNLOAD")
        cmdline.printText("\tDownloading Local map...")
        if config.USE_SOUND:
            config.SOUNDS["tapestart"].play()
        self.root_parent.localMapPage.drawPage()
        cmdline.printText("\tDownloading World map...")
        if config.USE_SOUND:
            config.SOUNDS["tapestart"].play()
        self.root_parent.worldMapPage.drawPage()
        if config.USE_SOUND:
            config.SOUNDS["tapestop"].play()

        cmdline.printText(">PIP-BOY.INIT")

        # Show Pip-Boy logo!
        if not config.QUICKLOAD:
            self.showBootLogo()

        if config.USE_SOUND:
            config.SOUNDS["start"].play()
        print("END INIT PROCESS")

        self.current_tab.resetPage(self.mode_num)
        tab_canvas, tab_changed = self.drawTab()
        self.screen_canvas = tab_canvas.convert()
        self.updateCanvas("changetab")

    def showBootLogo(self):
        '''Show bootup-logo, play sound:'''

        boot_logo = pygame.image.load('images/bootupLogo.png')
        self.focusInDraw(boot_logo)

        if config.USE_SOUND:
            boot_sound = pygame.mixer.Sound('sounds/falloutBootup.wav')
            boot_sound.play()

        pygame.display.update()
        pygame.time.wait(4200)

    def focusInDraw(self, canvas):
        '''Do focus-in effect on a page:'''

        # Reset to first animation-frame:
        self.frame_num = 0

        def divRange(val):
            while val >= 1:
                yield val
                val /= 2

        # Do focusing-in effect by scaling canvas down/up:
        max_div = 4
        hicol_canvas = canvas.convert(24)
        for res_div in divRange(max_div):

            blur_image = pygame.transform.smoothscale(hicol_canvas, (self.canvas_size[0] / res_div,
                                                                   self.canvas_size[1] / res_div))
            blur_image = pygame.transform.smoothscale(blur_image, self.canvas_size)

            # Add faded sharp image:
            mult_val = (255 / (1 * max_div))
            draw_image = canvas.convert()
            draw_image.fill((mult_val, mult_val, mult_val), None, pygame.BLEND_RGB_MULT)

            # Add blurred image:
            draw_image.blit(blur_image, (0, 0), None, pygame.BLEND_RGB_ADD)

            # Add background:
            if self.background:
                draw_image.blit(self.background, (0, 0), None, pygame.BLEND_RGB_ADD)

            # Add scanlines:
            draw_image.blit(self.overlay_frames[0], (0, 0), None, pygame.BLEND_RGB_MULT)

            # Scale up and draw:
            draw_image = pygame.transform.scale(draw_image, self.screen_size)
            self.screen.blit(draw_image, (0, 0))
            pygame.display.update()

    def updateCanvas(self, update_sound=None):
        '''Generate black & white outline-image:'''

        if config.USE_SOUND and update_sound:
            config.SOUNDS[update_sound].play()

        # Do focus-in effect when changing tab (i.e. the lit buttons)
        if update_sound == "changetab":
            self.focusInDraw(self.screen_canvas)

        # Bake the background into the canvas-image:
        if self.background:
            self.screen_canvas.blit(self.background, (0, 0), None, pygame.BLEND_RGB_ADD)

    def drawAll(self):

        # Start with copy of display-stuff:
        #   (generated by updateCanvas)
        draw_image = self.screen_canvas.convert()

        # Don't tint camera-output if VATS mode is set to untinted:
        is_vats = (self.current_tab.name == 'V.A.T.S.')
        if not is_vats or self.current_tab.showTint:

            # Add scanlines/tint:
            use_frame = 0
            if not is_vats:
                use_frame = (self.frame_num - self.anim_delay_frames)
                if use_frame < 0:
                    use_frame = 0
            draw_image.blit(self.overlay_frames[use_frame], (0, 0), None, pygame.BLEND_RGB_MULT)

        # Make screen extra-bright in torch-mode:
        if self.torch_mode:
            draw_image.fill((0, 128, 0), None, pygame.BLEND_ADD)

        draw_image = pygame.transform.scale(draw_image, self.screen_size)
        self.screen.blit(draw_image, (0, 0))
        pygame.display.update()

        # Vary hum-volume:
        if config.USE_SOUND:
            self.humvolume += (random.uniform(-0.05, 0.05))
            if self.humvolume > config.MAXHUMVOL:
                self.humvolume = config.MAXHUMVOL
            elif self.humvolume < config.MINHUMVOL:
                self.humvolume = config.MINHUMVOL
            # print self.humvolume
            self.humsound.set_volume(self.humvolume)

        self.frame_num += 1
        if self.frame_num >= self.overlay_frames_count:
            self.frame_num = 0

            # Only print FPS every so often, to avoid slowing us down:
            print("FPS: " + str(self.clock.get_fps()))

    drawn_page = []

    def drawTab(self):

        page_nums = [self.tab_num, self.mode_num]
        tab = self.current_tab

        page_canvas, page_changed = tab.drawPage(self.mode_num)
        header_canvas, header_changed = tab.header.getHeader()
        different_page = (self.drawn_page != page_nums)

        canvas_change = (page_changed or header_changed or different_page)

        if canvas_change:
            # print("%s tab_changed: Page:%s Head:%s Different:%s %s" % (tab.name,
            #                                                           page_changed,
            #                                                           header_changed,
            #                                                           different_page,
            #                                                           str(page_nums)))
            tab.canvas = page_canvas.convert()
            tab.canvas.blit(header_canvas, (0, 0), None, pygame.BLEND_ADD)
            tab.canvas.blit(tab.footerImgs[self.mode_num], (0, 0), None, pygame.BLEND_ADD)

        self.drawn_page = page_nums

        return tab.canvas, canvas_change

    def run(self):
        '''Main Loop'''
        running = True
        while running:

            tab_was = self.tab_num
            mode_was = self.mode_num
            torch_was = self.torch_mode
            mode_vals = [0, 0, 0]

            page_events = []

            do_update = False
            update_sound = None

            if config.USE_SERIAL:
                # Run through serial-buffer characters, converting to pygame events if required:
                ser = self.ser
                ser_mouse_dist = 10
                try:
                    while ser.inWaiting():
                        char = ser.read(1)

                        if char != '\n' and char != '\r':
                            self.ser_buffer = (self.ser_buffer + char)
                            # print char
                        else:
                            ser_buffer = self.ser_buffer
                            # print ser_buffer

                            if ser_buffer == 'lighton':              # Torch On
                                self.torch_mode = True
                            elif ser_buffer == 'lightoff':           # Torch Off
                                self.torch_mode = False
                            elif ser_buffer == '1':
                                self.tab_num = 0
                            elif ser_buffer == '2':
                                self.tab_num = 1
                            elif ser_buffer == '3':
                                self.tab_num = 2
                            elif ser_buffer == 'q':
                                self.mode_num = 0
                            elif ser_buffer == 'w':
                                self.mode_num = 1
                            elif ser_buffer == 'e':
                                self.mode_num = 2
                            elif ser_buffer == 'r':
                                self.mode_num = 3
                            elif ser_buffer == 't':
                                self.mode_num = 4
                            elif ser_buffer == 'select':             # Select
                                page_events.append('sel')
                            elif ser_buffer == 'cursorup':           # List up
                                mode_vals[2] += 1
                            elif ser_buffer == 'cursordown':         # List down
                                mode_vals[2] -= 1
                            elif ser_buffer == 'left':               # Mouse left
                                mode_vals[0] -= ser_mouse_dist
                            elif ser_buffer == 'right':              # Mouse right
                                mode_vals[0] += ser_mouse_dist
                            elif ser_buffer == 'up':                 # Mouse up
                                mode_vals[1] += ser_mouse_dist
                            elif ser_buffer == 'down':               # Mouse down
                                mode_vals[1] -= ser_mouse_dist
                            elif ser_buffer.startswith('volts'):     # Battery Voltage
                                page_events.append(ser_buffer)
                            elif ser_buffer.startswith('temp'):      # Temperature
                                page_events.append(ser_buffer)

                            # Clear serial buffer:
                            self.ser_buffer = ""
                except:
                    print("Serial-port failure!")
                    config.USE_SERIAL = False

            # Run through Pygame's keyboard/mouse event-queue:
            for event in pygame.event.get():
                # print event
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    page_events.append('sel')
                elif event.type == pygame.MOUSEMOTION:
                    mouse_x, mouse_y = pygame.mouse.get_rel()
                    mode_vals[0] += mouse_x
                    mode_vals[1] += mouse_y
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    elif event.key == pygame.K_o:  # Torch On
                        self.torch_mode = True
                    elif event.key == pygame.K_p:  # Torch Off
                        self.torch_mode = False
                    elif event.key == pygame.K_1:
                        self.tab_num = 0
                    elif event.key == pygame.K_2:
                        self.tab_num = 1
                    elif event.key == pygame.K_3:
                        self.tab_num = 2
                    elif event.key == pygame.K_q:
                        self.mode_num = 0
                    elif event.key == pygame.K_w:
                        self.mode_num = 1
                    elif event.key == pygame.K_e:
                        self.mode_num = 2
                    elif event.key == pygame.K_r:
                        self.mode_num = 3
                    elif event.key == pygame.K_t:
                        self.mode_num = 4
                    elif event.key == pygame.K_RETURN:
                        page_events.append('sel')
                    elif event.key == pygame.K_UP:  # List up
                        mode_vals[2] += 1
                    elif event.key == pygame.K_DOWN:  # List down
                        mode_vals[2] -= 1

            if (mode_vals != [0, 0, 0]):
                page_events.append(mode_vals)

            changed_tab = (self.tab_num != tab_was)
            changed_mode = (self.mode_num != mode_was)
            changed_torch = (self.torch_mode != torch_was)

            if changed_torch:
                if self.torch_mode:
                    update_sound = "lighton"
                else:
                    update_sound = "lightoff"

            if changed_tab:
                update_sound = "changetab"

            do_update = (changed_torch or changed_tab or changed_mode)

            if do_update:
                self.current_tab = self.tabs[self.tab_num]
                self.current_tab.resetPage(self.mode_num)

            # Update current tab, see if it's changed:
            tab_canvas, tab_changed = self.drawTab()
            if do_update or tab_changed:
                # updateCanvas will add background to this:
                self.screen_canvas = tab_canvas.convert()
                do_update = True

            if do_update or update_sound:
                self.updateCanvas(update_sound)

            if len(page_events) != 0:
                self.current_tab.ctrlEvents(page_events, self.mode_num)

            self.drawAll()

            self.clock.tick(config.FPS)

        if config.USE_SERIAL:
            self.ser.close()

        pygame.quit()

if __name__ == '__main__':
    engine = Engine()
    engine.run()
