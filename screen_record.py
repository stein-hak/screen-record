#!/usr/bin/python3

import sys

sys.path.append('/opt/lib/')
import os
import ffprobe
import gi
from execute import execute

gi.require_version('Gst', '1.0')
from gi.repository import Gst, Gio
from datetime import datetime, timedelta
import time
import shutil
import argparse
import tempfile
import signal
from datetime import datetime

Gst.init(None)

# pactl list | grep -A2 'Source #' | grep 'Name: '
# Find your pulse audio device. Example below

DEVICE_NAME = 'alsa_output.pci-0000_00_1f.3.analog-stereo.monitor'

def files_concat_to_mp4(file_list,out_file,encoder=None,hw_accel=None,audio=False,timeout=90):
    out = ''
    err = ''
    rc = 1
    if file_list:
        if len(file_list) == 1:

            if os.path.exists(file_list[0]):

                cmd = ['ffmpeg', '-hide_banner', '-i', file_list[0]]

                if not encoder:
                    if not audio:
                        cmd += ['-vcodec', 'copy', '-an', '-f', 'mp4', '-fflags', '+genpts', '-movflags', 'faststart', '-y', out_file]
                    else:
                        cmd += ['-vcodec', 'copy', '-acodec', 'aac', '-strict', '-2', '-f', 'mp4', '-fflags', '+genpts', '-movflags', 'faststart',
                                '-y', out_file]

                out, err, rc = execute(cmd)


        else:
            temp = tempfile.NamedTemporaryFile(delete=False)
            for f in file_list:
                if os.path.exists(f):
                    line = 'file ' + "'" + f + "'" + '\n'
                    temp.write(line.encode())
                    temp.flush()

            cmd = ['ffmpeg', '-hide_banner', '-f', 'concat', '-safe', '0', '-i', temp.name]

            if not encoder:
                if not audio:
                    cmd += ['-vcodec', 'copy', '-an', '-f', 'mp4', '-fflags', '+genpts', '-movflags', 'faststart', '-y', out_file]
                else:
                    cmd += ['-vcodec', 'copy', '-acodec', 'aac', '-strict', '-2', '-f', 'mp4', '-fflags', '+genpts', '-movflags', 'faststart',
                            '-y', out_file]

            out, err, rc = execute(cmd)

            temp.close()
            os.remove(temp.name)

    return out, err ,rc

class ScreenCast():

    def __init__(self, out_file=None, workdir=None, display_name=':0', pulse_device=DEVICE_NAME, segment_duration=300,
                 hw_accell=False, fps=60,bitrate= 4096):
        self.out_file = out_file
        self.workdir = workdir
        self.display_name = display_name
        self.pulse_device = pulse_device
        self.segment_duration = segment_duration
        self.hw_accell = hw_accell
        self.fps = fps
        self.bitrate = bitrate
        self.file_list = []
        self.interrupt = False


        if not self.workdir:
            self.workdir = os.getcwd()

        if not self.out_file:

            self.out_file = os.path.join(self.workdir,'screen_record_final_' + datetime.now().strftime('%y%m%d_%H%M%S') + '.mp4')

    def setup_pipeline(self):
        if not self.hw_accell:
            pipeline_str = 'ximagesrc use-damage=0 do-timestamp=1 name=video_source ! video/x-raw,framerate=%d/1 ! videoscale ! videoconvert ! x264enc tune=zerolatency bitrate=%d speed-preset=superfast !  h264parse  ! queue  ! persist. pulsesrc name=audio_source buffer-time=20000000 ! tee name=audio audio. ! queue ! audioconvert ! avenc_ac3 ! ac3parse ! queue ! persist.audio_0  splitmuxsink muxer=matroskamux name=persist audio. ! queue ! audioconvert ! level name=sound_level ! fakesink' % (int(self.fps),int(self.bitrate))

        else:
            pipeline_str = 'ximagesrc use-damage=0 do-timestamp=1 name=video_source ! video/x-raw,framerate=%d/1 ! videoscale ! videoconvert ! vaapih265enc bitrate=%d !  h265parse config-interval=-1 ! queue  ! persist. pulsesrc name=audio_source buffer-time=20000000 !  tee name=audio audio. ! queue ! audioconvert ! avenc_ac3 ! ac3parse ! queue ! persist.audio_0  splitmuxsink muxer=matroskamux name=persist audio. ! queue ! audioconvert ! level name=sound_level ! fakesink' % (int(self.fps),int(self.bitrate))

        print(pipeline_str)
        self.pipeline = Gst.parse_launch(pipeline_str)
        self.video_source = self.pipeline.get_by_name('video_source')
        self.audio_source = self.pipeline.get_by_name('audio_source')
        self.persist = self.pipeline.get_by_name('persist')
        self.level = self.pipeline.get_by_name('sound_level')
        self.level.set_property('interval',1*Gst.SECOND)

        self.video_source.set_property('display-name',self.display_name)
        self.audio_source.set_property('device',self.pulse_device)
        #
        self.persist.set_property('location', '%05d.mp4')
        self.persist.set_property('max_size_time', self.segment_duration * Gst.SECOND)
        self.bus = self.pipeline.get_bus()
        self.bus.add_signal_watch()
        self.persist.connect('format-location-full', self.on_new_file)
        self.is_silent = False
        self.last_sound_time = None


    def on_new_file(self, sink, id, sample):

        file_name = os.path.join(self.workdir,'%05d.mp4' % id)


        self.file_list.append(file_name)

        recording_time = datetime.now() - self.start_time

        print('Recording. Total record time is %d ' % recording_time.total_seconds())

    def silense_detect(self):
        if datetime.now() - self.start_time > timedelta(seconds=60):
            if self.is_silent:
                if not self.last_sound_time:
                    print('Silence datected on screen recorder. Stopping record')
                    self.stop()
                elif datetime.now() - self.last_sound_time > timedelta(seconds=30):
                    print('Silence datected on screen recorder. Stopping record')
                    self.stop()

    def stop(self):
        self.interrupt = True
        time.sleep(5)
        recording_time = datetime.now() - self.start_time
        print('Finishing screen recording to file %s' % self.out_file)
        print('Total time %d' % recording_time.total_seconds())
        files_concat_to_mp4(self.file_list,self.out_file,audio=True)
        for f in self.file_list:
            if os.path.exists(f):
                os.remove(f)

    def run(self):

        self.setup_pipeline()
        self.pipeline.set_state(Gst.State.PLAYING)
        self.start_time = datetime.now()
        print('Starting screen recording')
        print('X screen name : %s' % self.video_source.get_property('display-name'))
        print('Audio device name : %s' % self.audio_source.get_property('device'))

        while not self.interrupt:
            message = self.bus.timed_pop_filtered(1*Gst.SECOND,
                                                  Gst.MessageType.ERROR | Gst.MessageType.EOS | Gst.MessageType.ELEMENT)

            if message:
                if message.type == Gst.MessageType.ELEMENT:
                    struct = message.get_structure()
                    if struct.get_name() == 'level':
                        peak = struct.get_value('peak')[0]
                        if peak < -50:
                            #print('Silence detected')
                            self.is_silent = True
                        else:
                            #print('Sound detected')
                            self.is_silent = False
                            self.last_sound_time = datetime.now()
                        self.silense_detect()
                pass

        self.pipeline.set_state(Gst.State.NULL)
        self.bus.remove_signal_watch()
        self.bus = None


if __name__ == '__main__':




    def signal_handler(signal, frame):
        record.stop()


    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    parser = argparse.ArgumentParser(description='Screen recording tool.')
    parser.add_argument('--no-hw', action='store_true', help='Disable hardware encoding')
    parser.add_argument('-o', '--out', help='Out file for record')
    parser.add_argument('-w', '--workdir', help='Workdir for record')
    parser.add_argument('-b', '--bitrate', type=int, default=8096, help='Video bitrate')
    parser.add_argument('--display', default=':0', help='Display name')
    parser.add_argument('--audio', help='Pulse audio device')
    parser.add_argument('--fps',type=int,default=60,help='FPS for video')
    parser.add_argument('--segment-duration', type=int, default=300, help='Segment duration for each file')
    args = parser.parse_args()

    if args.no_hw:
        hw_accell = False
    else:
        hw_accell = True

    if not args.audio:
        pulse_audio = DEVICE_NAME
    else:
        pulse_audio = args.audio


    record = ScreenCast(workdir=args.workdir,out_file=args.out,hw_accell=hw_accell,display_name=args.display,pulse_device=pulse_audio,segment_duration=args.segment_duration,bitrate=args.bitrate)

    record.run()
