

#!/usr/bin/env python

from subprocess import Popen, PIPE
import json
import sys
from execute import execute, execute_timeout
import os


class ffprobe():
	def __init__(self, source, timeout=60, tcp=False):

		self.source = source

		if tcp:
			com = ['ffprobe', '-hide_banner', '-loglevel', 'fatal','-show_error', '-rtsp_transport', 'tcp', '-print_format',
			       'json', '-show_format', '-show_streams', self.source]
		else:
			com = ['ffprobe', '-hide_banner', '-loglevel', 'fatal','-show_error', '-print_format', 'json', '-show_format',
			       '-show_streams', self.source]


		out, err, rc = execute_timeout(com,timeout=timeout)


		self.out = out
		self.err = None
		self.rc = rc

		try:
			self.metadata = json.loads(out)
		except:
			self.metadata = None

		self.rc = rc
		self.video_streams = []
		self.audio_streams = []
		self.format = None
		self.fps = None
		self.gop = None
		self.frames = None


		if self.is_sane():
			for stream in self.metadata['streams']:
				if stream['codec_type'] == 'video':
					self.video_streams.append(stream)
				elif stream['codec_type'] == 'audio':
					self.audio_streams.append(stream)

			self.format = self.metadata['format']
		else:
			if self.metadata:
				if self.metadata.get('error'):
					self.err= self.metadata.get('error')['string']
			else:
				self.err = 'empty metadata'

	def is_sane(self):
		if not self.metadata or self.rc != 0: #or len(self.metadata['streams']) < 1:
			return False
		else:
			return True

	def get_resolution(self, num_video_stream=0):
		if self.is_sane() and len(self.video_streams) >= num_video_stream:
			w = self.video_streams[num_video_stream]['width']
			h = self.video_streams[num_video_stream]['height']
			return w, h
		else:
			return None

	def get_bitrate(self, codec='video', num_stream=0):
		stream = None
		if codec == 'video':
			if len(self.video_streams) > num_stream:
				stream = self.video_streams[num_stream]
		elif codec == 'audio':
			if len(self.audio_streams) > num_stream:
				stream = self.audio_streams[num_stream]

		if stream and 'bit_rate' in stream.keys():
			return int(stream['bit_rate']) / 1024
		else:
			return None

	def get_video_codec(self, num_stream=0):
		stream = None
		if len(self.video_streams) > num_stream:
			stream = self.video_streams[num_stream]

		if stream and 'codec_name' in stream.keys():
			return stream['codec_name']
		else:
			return None

	def get_audio_codec(self, num_stream=0):
		stream = None
		if len(self.audio_streams) > num_stream:
			stream = self.audio_streams[num_stream]

		if stream and 'codec_name' in stream.keys():
			return stream['codec_name']
		else:
			return None

	def get_format_name(self):
		if self.format and 'format_name' in self.format.keys():
			return self.format['format_name']
		else:
			return None

	def get_duration(self):
		if self.format and 'duration' in self.format.keys():
			return float(self.format['duration'])

	def get_start_time(self):
		if self.format and 'start_time' in self.format.keys():
			return float(self.format['start_time'])

	def get_fps(self, num_stream=0):
		if self.fps:
			return self.fps
		else:
			if len(self.video_streams) > num_stream:
				stream = self.video_streams[num_stream]
			else:
				stream = None

			if stream and 'nb_frames' in stream.keys() and 'duration' in self.format.keys():
				self.fps = round(float(stream['nb_frames']) / float(self.format['duration']))

			else:
				self.fps = None

		return self.fps

	def load_frames(self):
		if self.frames:
			return self.frames

		else:
			if self.is_sane:
				if os.path.isfile(self.source):
					com = ['ffprobe', '-v', 'quiet', '-print_format', 'json','-show_frames',self.source]
					out, err, rc = execute(com)
					try:
						frames = json.loads(out)['frames']
					except:
						frames = None

					self.frames = frames

			return self.frames

	def calc_gop(self):
		numbers = []
		count = 0
		if self.gop:
			return self.gop

		else:
			if self.frames:
				pass
			else:
				self.load_frames()


			if self.frames:
				for frame in self.frames:
					if frame['key_frame']:
						if count:
							numbers.append(count)
							count = 0

					else:
						count += 1

			if count != 0:
				numbers.append(count)

			try:
				self.gop = round(float(sum(numbers)) / max(len(numbers), 1))

			except:
				self.gop = None



		return self.gop

	def estimate_offset(self):
		if self.gop and self.fps:
			pass
		else:
			self.calc_gop()
			self.get_fps()

		if self.gop and self.fps:
			return int(round(float(self.gop/self.fps) + 1))
		else:
			return None


if __name__ == '__main__':
	f = ffprobe(sys.argv[1])

