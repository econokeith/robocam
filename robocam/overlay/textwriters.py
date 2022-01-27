import time
from queue import Queue

import cv2
import numpy as np

import robocam.helpers.utility as uti
import robocam.helpers.timers as timers
import robocam.overlay.colortools as ctools
import robocam.overlay.writer_base as base


class TextWriter(base.Writer):

    def __init__(self,
                 pos,  #position
                 font=cv2.FONT_HERSHEY_DUPLEX,
                 color='r',  # must be either string in color hash or bgr value
                 scale=1,  # font scale,
                 ltype=2,  # line type
                 ):

        self.font = font
        
        if isinstance(color, str):
            self.color = ctools.COLOR_HASH[color]
        else:
            self.color = color

        self.pos = pos
        self.scale = scale
        self.ltype = ltype
        self._line = None
        self.text_function = None

    @property
    def line(self):
        return self._line

    @line.setter
    def line(self, new_text):
        self._line = new_text

    def write(self, frame : np.array, text=None, color=None):
        """

        :type frame: np.array
        """
        col = color if color is not None else self.color
        text = text if text is not None else self.line

        if text is not None:
            cv2.putText(frame,
                        text,
                        self.pos,
                        self.font, self.scale, col, self.ltype)

    def write_fun(self, frame, *args, **kwargs):
        self.line = self.text_function(*args, **kwargs)
        self.write(frame)

        
class TypeWriter(TextWriter):

    def __init__(self,
                 pos,  #position
                 font=cv2.FONT_HERSHEY_DUPLEX,
                 color='r',  # must be either string in color hash or bgr value
                 scale=1,  # font scale,
                 ltype=2,
                 dt=None,
                 rand = [.1,.3],
                 pause=1,
                 loop=False,
                 ):
        
        super().__init__(pos=pos, font=font, color=color, scale=scale, ltype=ltype)
        
        self.dt = dt
        self.rand = rand
        self.wait = sum(rand)/2 if dt is None else dt
        self.pause = pause
        self.loop = loop
        self.line_iter = None
        self.done = False
        self.output = ""
        self.cursor = Cursor()
        self.script = Queue()

    @property
    def line(self):
        return self._line

    @line.setter
    def line(self, new_text):
        # updates text_generator when text is updated
        self._line = new_text
        self.tick = time.time()
        
        if new_text is None:
            self.line_iter = None
            self.done = True
            self.output = None
            
        else:
            self.line_iter = uti.iter_none(new_text)
            self.done = False
            self.output = ""

    def add_lines(self, new_lines):
        """
        adds lines to the queue if lines is either a string or
        an iterable object full of strings
        :param new_lines:
        :return:
        """
        if not isinstance(new_lines, str):
            for new_line in new_lines:
                self.add_lines(new_line)
        else:
            self.line = self.script.put(new_lines)

    def typeLine(self, frame):

        # if there's more in the text generator, it will continue to type new letters
        # then will show the full message for length of time self.end_pause
        # then finally stop shows
        if self.done is True and self.script.empty():
            return

        elif self.done is True and not self.script.empty():
            self.line = self.script.get()

        # update if there is more to teh line and t > wait
        elif self.line_iter is not None and time.time() - self.tick >= self.wait:
            char = next(self.line_iter)
            #if the line_iter returns None, then it is done
            if char is None:
                self.line_iter = None
            else:
                self.output += char
                # set random wait time
                if self.dt is None:
                    self.wait = np.random.rand() * (self.rand[1] - self.rand[0]) + self.rand[0]

            self.write(frame, self.output)
            self.tick= time.time()

        #write old output if there is more to write but it isn't update time
        elif self.line_iter is not None:
            self.write(frame, self.output)
        #if the line is done, but the end pause is still going. write whole line with cursor
        elif self.line_iter is None and time.time() - self.tick < self.pause:
            self.write(frame, self.output+self.cursor())

        #empty line generator and t > pause sets the line to done
        else:
            self.done = True

class FPSWriter(TextWriter):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.clock = timers.LastCallTimer()
        self.text_function =  lambda fps : f'FPS = {int(1/fps)}'

    def write(self, frame: np.array, text=None, color=None):
        fps = self.text_function(self.clock())
        super().write(frame, fps)


class Cursor(timers.Blinker):

    def __init__(self, cycle=.53, char_1='_', char_0=' '):
        """
        returns char_1 if on and char_0 if off
        :param cycle: if float, [on_time, off_time] = [cycle, cycle], else on_time, off_time = cycle
        :param char_1:
        :param char_0:
        """
        super().__init__(cycle=cycle)
        self.char_0 = char_0
        self.char_1 = char_1

    def __call__(self):
        if super().__call__():
            return self.char_1
        else:
            return self.char_0



if __name__ == '__main__':
    pass