import os
import shutil
from random import random

import youtube_dl
from datetime import timedelta

def sizeof_fmt(num, suffix='B'):
	for unit in ['', 'Ki', 'Mi', 'Gi', 'Ti', 'Pi', 'Ei', 'Zi']:
		if abs(num) < 1024.0:
			return "%3.1f%s%s" % (num, unit, suffix)
		num /= 1024.0
	return "%.1f%s%s" % (num, 'Yi', suffix)


class GenericDownloader:

	sectionName = 'GlobalSettings'

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
		'sleep_interval'
	]

	def __init__(self, settings, logging_handler, download_manager):
		self.download_manager = download_manager
		self.logging = logging_handler
		self.file_list = []
		self.tempDir = None
		self.finalDir = None
		self.options = self.compose_option(settings.get_config(self.sectionName))

	def process_download(self, file):
		"""
		Add the requested url to the list of files to download
		:param file: The file containing all the information to manage
		:return:
		"""
		self.file_list.append(file)

	def stop_download(self, file):
		for download_file in self.file_list:
			if file == download_file:
				download_file['stop'] = true


	def start_download(self) -> None:
		"""
		Start the download of requested url
		:return:
		"""
		with youtube_dl.YoutubeDL(self.options) as ydl:
			for file in self.file_list:
				url = file['url']
				try:
					print("Downloading: " + url)
					result = ydl.extract_info("{}".format(url))
					title = ydl.prepare_filename(result)
					self.logging.info("Preparing download of: " + str(title))
					print("Preparing download of: " + str(title))
					ydl.download([url])
					if self.tempDir:
						try:
							shutil.move(os.path.join(self.tempDir, title), self.finalDir)
							self.logging.debug("Moved " + title + " from ["+self.finalDir+"] to ["+self.tempDir+"]")
							print("Moved " + title + " from ["+self.finalDir+"] to ["+self.tempDir+"]")
						except FileNotFoundError:
							self.logging.warning('Cannot find downloaded file: ' + title)
							print('Cannot find file: ' + title)

					self.logging.info("Successfully downloaded: " + str(title))
					print("Successfully downloaded: " + str(title))
				except youtube_dl.utils.DownloadError as e:
					print("Cannot download " + url + ": " + str(e))
					self.logging.warning("Cannot download " + url + ": " + str(e))
				except StopDownload:
					print("Download paused [" + url + "]")
					self.logging.info("Download paused [" + url + "]")

	def compose_option(self, settings):
		"""
		Creates the option to pass to youtube_dl
		:param settings: An object containing a list of settings
		:return: A parsed object ready to be passed to youtube-dl
		"""
		output_settings = {
			'progress_hooks': [self.my_hook],
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
		self.finalDir = os.path.dirname(settings['outtmpl'])
		if 'tempDir' in settings:
			self.tempDir = settings['tempDir']
			output_settings['outtmpl'] = os.path.join(self.tempDir, os.path.basename(settings['outtmpl']))
			self.logging.info(
				"Using temp dir: [" + output_settings['outtmpl'] + "] and finally move to final dir: [" + settings['outtmpl'] + "]")
		else:
			self.logging.warning(
				"Not using temp directory, downloading directly to [" + output_settings['outtmpl'] + "]")

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

	def check_download_to_stop(self):
		for download_file in self.file_list:
			if 'stop' in download_file and download_file['stop']:
				self.logging.info("Stopping download [" + download_file['url'] + "]")
				print("Stopping download  [" + download_file['url'] + "]")
				raise StopDownload("Stopping download  [" + download_file['url'] + "]")

	def my_hook(self, d):
		time = str("{:0>8}".format(str(timedelta(seconds=d['elapsed'])))) if 'elapsed' in d else ""
		size_in_bytes = d["total_bytes"] if 'total_bytes' in d else 0.00001
		size = sizeof_fmt(size_in_bytes)
		complete_filename = d['filename']
		filename = os.path.basename(complete_filename)
		self.check_download_to_stop()
		if d['status'] == 'finished':
			print(
				"Download complete [" + filename + "] - " + size + " in " + time)
			# self.logging(
			# 	"Download complete [" + os.path.basename(d['filename']) + "] - " + d["_total_bytes_str"] + " in "
			# 	+ d["_elapsed_str"])
		elif d['status'] == 'downloading':
			downloaded_bytes = float(d['downloaded_bytes'])
			percentage = round(downloaded_bytes/size_in_bytes * 100, 1)
			print(
				"Downloading " + str(percentage) + "% (" + str(downloaded_bytes) + "/" + str(size_in_bytes) + " bytes) [" + filename +
				"] - Elapsed: " + time + "s - ETA: " + str(d['eta']) + "s")
			self.download_manager.update_download_progress(filename, percentage)
		else:
			print("Unexpected error during download: " + str(d))
			# self.logging("Unexpected error during download: " + str(d))


class MissingRequiredParameter(Exception):
	pass


class StopDownload(Exception):
	pass
