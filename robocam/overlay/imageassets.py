import os
import time

import cv2
import numpy as np
import robocam.overlay.bases as base
from robocam.overlay import shapes as shapes
from robocam.helpers import utilities as utils

#Todo: make this more easily resizeable
class ImageAsset(base.Writer):

    def __init__(self,
                 src,
                 position = (100,100),
                 bit=0, #let's you flip the bit-mask 0, 1, or None
                 size = None, #if none stays the same, otherwise change
                 loc = (100, 100) #location of center
                 ):
        """
        src is the path to a directory that contains exactly 2 image files. The image or bitmap to be used and a 2D
        bit-mask that directs
        the writer which pixels to write and which to ignore. The naming convention is: name_of_image.jpg and
        name_of_image_mask.jpg
        :param src:S
        """
        files = os.listdir(src)
        files.sort(key=len)
        self.img = cv2.imread(os.path.join(src, files[0]))

        self.bit = bit
        if bit in [0, 1] and len(files)>1:
            self.mask = cv2.imread(os.path.join(src, files[1]))
            self.mask[self.mask <128] = 0
            self.mask[self.mask >=128] = 255
            self.locs = np.asarray(np.nonzero(self.mask == self.bit))
        else:
            self.mask = None
            self.locs = None

        #this might be wrong
        self.center = self.img.shape[0] // 2, self.img.shape[1] // 2
        self.dim = self.img.shape[:2][::-1]
        self.position = position

    #TODO THIS IS FLIPPING COORDINATEES
    def _c_to_tl_on_frame(self, f_center):
        """
        find the position of the frame that represents the top corner of hte image asset given
        the position of the center of the asset on the frame
        :return:
        """
        img_c = self.center
        return f_center[0] - img_c[1], f_center[1] - img_c[0]

    def write(self, frame, position=None, pos_type='c'):
        """
        loc type can either be 'c' for center or 'tl' for top right. must be given in absolute frame
        coords
        :param frame:
        :param pos:
        :param pos_type:
        :return:
        """
        v, h, _ = self.img.shape
        pos = self.position if position is None else position
        t, l = pos_type if pos_type == 'tl' else self._c_to_tl_on_frame(pos[::-1])
        b = t + v
        r = l + h

        if self.mask is None:
            frame[t:b, l:r] = self.img

        else:
            loc_y = self.locs[0]
            loc_x = self.locs[1]

            frame[t + loc_y, l + loc_x] = self.img[loc_y, loc_x]


if __name__=='__main__':
    import robocam.camera as camera
    Capture = camera.ThreadedCameraPlayer(0, dim=(1920, 1080)).start()
    Pie = ImageAsset('./photo_asset_files/pie_asset')

    while True:
        Capture.read()
        frame = Capture.frame
        tick = time.time()
        Pie.write(frame, (860, 540))
        tock = int(1000*(time.time() - tick))
        shapes.write_text(frame, str(tock))
        shapes.write_text(frame, str(Capture.latency), pos=(10, 200))

        cv2.imshow('test', frame)

        if utils.cv2waitkey():
            break

    Capture.stop()
