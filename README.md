# screen-record

Simple python program to record video from screen to h264/h265 video with sound from pulseaudio. Usefull for recording podcasts and meeting and lectures. Will stop the recording automaticly when silence is detected after initial 60 seconds of recording. Requires gstreamer stack and ffmpeg. 

On ubuntu:

  apt-get update && apt-get install -y --no-install-recommends \
    python3-mutagen \
    python3-gi \
    python3-gi-cairo \
    python3-dbus \
    python3-dev \
    gir1.2-gtk-3.0 \
    gir1.2-gstreamer-1.0 \
    gir1.2-gst-plugins-base-1.0 \
    gstreamer1.0-plugins-base \
    gstreamer1.0-plugins-good \
    gstreamer1.0-plugins-ugly \
    gstreamer1.0-pulseaudio \
    gstreamer1.0-plugins-bad \
    gstreamer1.0-libav \
    gstreamer1.0-rtsp \
    gstreamer1.0-opencv \
    gstreamer1.0-tools \
    gstreamer1.0-vaapi \
    ffmpeg

Uses Vaapi for hardware encoding where available and libx264 if --no-hw option is specified 

To determine our audio device use the command 

pactl list | grep -A2 'Source #' | grep 'Name: 

and copy the one with ".monitor" at the end. Then provide it with --audio option or change the default DEVICE_NAME in script.

Example usage: python3 ./screen-record.py -o now.mp4
