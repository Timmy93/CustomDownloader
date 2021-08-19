import youtube_dl
# Install ffmpeg-python (https://github.com/kkroening/ffmpeg-python)
import os
from datetime import timedelta


def my_hook(d):
	time = str("{:0>8}".format(str(timedelta(seconds=d['elapsed'])))) if 'elapsed' in d else ""
	size_in_bytes = d["total_bytes"] if 'total_bytes' in d else 0.00001
	size = sizeof_fmt(size_in_bytes)
	complete_filename = d['filename']
	filename = os.path.basename(complete_filename)
	if d['status'] == 'finished':
		print(
			"Download complete [" + filename + "] - " + size + " in " + time)
		# self.logging(
		# 	"Download complete [" + os.path.basename(d['filename']) + "] - " + d["_total_bytes_str"] + " in "
		# 	+ d["_elapsed_str"])
	elif d['status'] == 'downloading':
		print(
			"Downloading " + str(round(float(d['downloaded_bytes']) / size_in_bytes * 100, 1)) + "% [" + filename +
			"] - Elapsed: " + time + "s - ETA: " + d['eta'] + "s")
	else:
		print("Unexpected error during download: " + str(d))
		# self.logging("Unexpected error during download: " + str(d))


def sizeof_fmt(num, suffix='B'):
	for unit in ['', 'Ki', 'Mi', 'Gi', 'Ti', 'Pi', 'Ei', 'Zi']:
		if abs(num) < 1024.0:
			return "%3.1f%s%s" % (num, unit, suffix)
		num /= 1024.0
	return "%.1f%s%s" % (num, 'Yi', suffix)


class CrunchyrollDownloader:

	def __init__(self, output_dir, logging_handler):
		self.logging = logging_handler
		self.urls = []
		self.outputDir = output_dir
		self.options = {
			# 	'simulate': True,
			# 	'listsubtitles': True,
			'outtmpl': self.outputDir + '/%(title)s.%(ext)s',
			'quiet': True,
			'subtitleslangs': ['itIT'],
			'subtitlesformat': 'ass',
			'progress_hooks': [my_hook],
			'logger': self.logging.getLogger(),
			'writesubtitles': True,
			'postprocessors': [{
				'key': 'FFmpegEmbedSubtitle',
				# 'format': 'srt',
			}]
		}

	def request_download(self, url):
		self.urls.append(url)

	# Execute the download
	def start_download(self):
		with youtube_dl.YoutubeDL(self.options) as ydl:
			for url in self.urls:
				print("Downloading: " + url)
				ydl.download([url])
				print("Done!")
