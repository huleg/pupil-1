'''
Functions to display certain recurring instances throughout the different tests
(e.g. countdowns, menu, etc.)
'''
from psychopy import visual, core, event


def getWindows(controller):
    if controller.testing:
        testWin = visual.Window(
            size=(640, 400), monitor="testMonitor", units="pix", pos=(640, 50))
    else:  # not testing (i.e. working on tobii tracker)
        testWin = visual.Window(
            size=(1920, 1080), monitor="testMonitor", units="pix", screen=0, fullscr=True)
    return testWin


def countdown(controller):
    # countdown time in seconds
    count_time = controller.settings['Countdown Time']
    win = controller.testWin
    countdown_text = visual.TextStim(win, text=str(count_time),
                                     font='Helvetica', alignHoriz='center', alignVert='center', units='norm',
                                     pos=(0, 0), height=0.2, color=[178, 34, 34], colorSpace='rgb255',
                                     wrapWidth=2)
    for i in range(count_time):
        countdown_text.text = str(count_time)
        countdown_text.draw()
        win.flip()
        core.wait(1.0)
        count_time -= 1
    win.flip(clearBuffer=True)  # clears countdown off of the screen


def fill_screen(win, window_color):
    # set rect to fill window with color
    rect = visual.Rect(
        win, 2, 2, units='norm', fillColor=window_color, lineColor=None)
    rect.draw()
    win.flip()


def text_keypress(win, text):
    display_text = visual.TextStim(win, text=text,
                                   font='Helvetica', alignHoriz='center', alignVert='center', units='norm',
                                   pos=(0, 0), height=0.1, color=[255, 255, 255], colorSpace='rgb255',
                                   wrapWidth=2)
    display_text.draw()
    win.flip()
    event.waitKeys()
    win.flip()


def image_keypress(win, image_loc):
    image_disp = visual.ImageStim(win, image=image_loc)
    image_disp.draw()
    win.flip()
    event.waitKeys()
    win.flip()


def text(win, text):
    display_text = visual.TextStim(win, text=text,
                                   font='Helvetica', alignHoriz='center', alignVert='center', units='norm',
                                   pos=(0, 0), height=0.2, color=[0, 255, 0], colorSpace='rgb255',
                                   wrapWidth=2)
    display_text.draw()
    win.flip()


def cross(win):
    cross = visual.TextStim(win, text='+',
                            font='Helvetica', alignHoriz='center', alignVert='center', units='norm',
                            pos=(0, 0), height=0.3, color=[255, 255, 255], colorSpace='rgb255',
                            wrapWidth=2)
    cross.draw()
    win.flip()
