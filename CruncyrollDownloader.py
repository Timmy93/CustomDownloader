import youtube_dl
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


class MissingRequiredParameter(Exception):
	pass


class CrunchyrollDownloader:

	requiredParameters = [
		'outtmpl',
	]

	optionalParameters = [
		'subtitleslangs',
		'quiet',
		'subtitlesformat',
		'writesubtitles',
		'restrictfilenames',
		'ignoreerrors',
		'sleep_interval',
	]

	def __init__(self, settings, logging_handler):
		self.logging = logging_handler
		self.urls = []
		self.options = self.compose_option(settings)

	def request_download(self, url):
		"""
		Add the requested url to the list of files to download
		:param url: The url to manage
		:return:
		"""
		self.urls.append(url)

	def start_download(self) -> None:
		"""
		Start the download of requested url
		:return:
		"""
		with youtube_dl.YoutubeDL(self.options) as ydl:
			for url in self.urls:
				print("Downloading: " + url)
				result = ydl.extract_info("{}".format(url))
				title = ydl.prepare_filename(result)
				self.logging.info("Preparing download of: " + str(title))
				print("Preparing download of: " + str(title))
				ydl.download([url])
				print("Done!")
				# TODO Use title to move file from and to temp directory

	def compose_option(self, settings):
		"""
		Creates the option to pass to youtube_dl
		:param settings: An object containing a list of settings
		:return: A parsed object ready to be passed to youtube-dl
		"""
		output_settings = {
			'progress_hooks': [my_hook],
			'logger': self.logging.getLogger()
		}
		# Fill required parameters
		for key in self.requiredParameters:
			if key in settings:
				output_settings[key] = settings[key]
			else:
				self.logging.error("Missing parameter " + key)
				raise MissingRequiredParameter("Missing parameter " + key)

		# Fill optional parameters
		for key in self.optionalParameters:
			if key in settings:
				output_settings[key] = settings[key]
			else:
				self.logging.debug("Missing optional parameter " + key + " - Skip")

		# Execute further checks
		if 'subtitleslangs' in output_settings and not isinstance(output_settings['subtitleslangs'], list):
			self.logging.warning("Requested subtitles as list, not as single value - Try repairing")
			output_settings['subtitleslangs'] = [output_settings['subtitleslangs']]

		if 'impress_sub' in settings:
			if settings['impress_sub'] is True:
				output_settings['postprocessors'] = [{'key': 'FFmpegEmbedSubtitle'}]
		else:
			if 'subtitleslangs' in settings:
				self.logging.warning("Requested subtitles but not impressing in the video source")

		return output_settings
