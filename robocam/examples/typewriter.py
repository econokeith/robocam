import argparse

import cv2
import numpy as np

import robocam.camera as camera
import robocam.helpers.timers as timers
import robocam.overlay.colortools as ctools
import robocam.overlay.textwriters as writers

parser = argparse.ArgumentParser(description='Example of the TypeWriter screen object')
parser.add_argument('-d','--dim',type=tuple, default=(1280, 720),
                    help='set video dimensions. default is (1280, 720)')
parser.add_argument('-m','--max_fps', type=int, default=30, help='set max fps Default is 30')
parser.add_argument('-c','--cam',type=bool, default=False,
                    help='USE_WEBCAM = True or False. Default is False')
parser.add_argument('-s','--script',type=str,  default='robocam/examples/tw_script.txt',
                    help='location_of_script.txt, defaults to ')

args = parser.parse_args()


def main():
    with open(args.script,'r') as f:
        script = f.read().split('\n')

    video_width, video_height = args.dim

    if args.cam is True:
        capture = camera.CameraPlayer(dim=(video_width, video_height))
        capture.max_fps = args.max_fps
    else:
        frame = np.empty((video_height, video_width, 3), dtype='uint8')

    fps_writer = writers.FPSWriter((10, 60), scale=2, ltype=2, color='r')
    speaker = writers.TypeWriter((10, 400), scale=2, ltype=2, rand=(.02, .08), pause=1.5, color='g')
    speaker.add_lines(script)
    color_counter = ctools.UpDownCounter(step=1, maxi=100)
    imshow_sleeper = timers.SmartSleep(1 / args.max_fps)

    while True:
        if args.cam is True:
            grabbed, frame = capture.read()
            if grabbed is False:
                break
            #frame[:, :, :] += color_counter()
        else:
            frame[:, :, :] = color_counter()

        speaker.typeLine(frame)
        fps_writer.write(frame)
        if args.cam is False:
            imshow_sleeper()
        cv2.imshow('test', frame)
        if cv2.waitKey(1) & 0xFF in [ord('q'), ord('Q'), 27]:
            break

    if args.cam is True:
        capture.release()
    cv2.destroyAllWindows()

if __name__=='__main__':
    main()