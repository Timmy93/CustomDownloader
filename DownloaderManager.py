import logging
import threading

from QueueManager import QueueManager
from IUBBaseTools import IUBConfiguration
from CrunchyrollDownloader import CrunchyrollDownloader
from GenericDownloader import GenericDownloader


class DownloaderManager(threading.Thread):

	supportedHost = [
		'youtube.com',
		'youtu.be',
		'crunchyroll.com'
	]
	"""
	The list of supported host
	"""

	testedHost = [
		'youtube.com',
		'youtu.be'
	]
	"""
	The list of host that work correctly using the generic downloader
	"""

	sectionName = {
		'crunchyroll': 'CrunchyrollSettings'
	}
	"""
	The dedicated section for each host. If no section is specified, the generic one will be used
	"""

	downloaderName = {
		'crunchyroll': 'CrunchyrollDownloader'
	}
	"""
	The list of specific downloader to use for each host. If no downloader is specified, the generic one will be used
	"""

	def __init__(self, settings: IUBConfiguration, logging_handler: logging):
		super().__init__()
		self.queueManager = QueueManager(settings, logging, self)
		self.downloadFailed = []
		self.inProgress = []
		self.paused = []
		self.downloadCompleted = []
		self.logging = logging_handler
		self.configuration = settings
		print("Downloader Manager successfully started")
		self.logging.info("Downloader Manager successfully started")

	def run(self):
		"""
		Start thread that manages url
		:return:
		"""
		while True:
			# Retrieve the next file to process
			file = self.queueManager.get_next_file()
			if file is not None:
				# Retrieve the downloader to process that link
				url = file['url']
				downloader = self.get_downloader(url)
				downloader.process_download(url)
				downloader.start_download()
			else:
				self.logging.info("Received invalid download file, ignoring it")

	def complete_this_download(self, url: str):
		return self.queueManager.change_queue(url, 'inProgress', 'downloadCompleted')

	def pause_this_download(self, url: str):
		return self.queueManager.change_queue(url, 'inProgress', 'paused')

	def fail_this_download(self, url: str):
		return self.queueManager.change_queue(url, 'inProgress', 'downloadFailed')

	def request_download(self, url: str):
		"""
		Add a new url to the list of link to manage
		:param url: The url to manage
		:return:
		"""
		if not isinstance(url, str):
			self.logging.info("Not a valid link passed")
			return
		if self.queueManager.already_managing(url):
			self.logging.info("Already downloading: [" + url + "] - Skip")
			return
		self.logging.info("Adding new url to download list [" + url + "]")
		downloader = self.get_downloader(url)
		el = downloader.get_info(url)
		self.queueManager.add_file(el)

	def get_queue(self):
		return self.queueManager.get_queues()

	def get_downloader(self, url: str):
		"""
		Retrieve the downloader to use to manage this file
		:param url: The url to manage
		:return: The downloader instance
		"""
		if 'crunchyroll.com' in url:
			return CrunchyrollDownloader(self.configuration, self.logging, self)
		else:
			if not any([x in url for x in self.testedHost]):
				self.logging.warning("Attempting download - Unknown provider: [" + url + "]")
				print("Attempting download - Unknown provider: [" + url + "]")
			return GenericDownloader(self.configuration, self.logging, self)

	def update_download_progress(self, filename: str, percentage: float):
		self.queueManager.update_download_progress(filename, percentage)
