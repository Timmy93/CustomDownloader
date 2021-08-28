import threading
from threading import Event

from CruncyrollDownloader import CrunchyrollDownloader
from GenericDownloader import GenericDownloader


class DownloaderManager(threading.Thread):

	supportedHost = [
		'youtube',
		'crunchyroll'
	]
	"""
	The list of supported host
	"""

	testedHost = [
		'youtube.com',
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

	downloadQueue = []

	def __init__(self, settings, logging_handler):
		super().__init__()
		self.downloadFailed = []
		self.inProgress = []
		self.downloadCompleted = []
		self.logging = logging_handler
		self.configuration = settings
		self.urlAvailable = Event()
		print("Downloader Manager successfully started")
		self.logging.info("Downloader Manager successfully started")

	def run(self):
		self.start_processing()

	def request_download(self, url):
		if url in self.downloadQueue:
			self.logging.info("Already downloading: [" + url + "] - Skip")
			return
		self.logging.info("Adding new url to download list [" + url + "]")
		self._append_url(url)

	def _append_url(self, url):
		self.downloadQueue.append(url)
		self.urlAvailable.set()

	def _get_url(self):
		while len(self.downloadQueue) == 0:
			# Stop Download manager, start waiting for a new url
			self.logging.info("Stopping download manager - No url to download")
			print("Download Manager paused - Waiting for new url")
			self.urlAvailable.clear()
			self.urlAvailable.wait()
			self.logging.info("Resuming download manager - New url found")
		url = self.downloadQueue.pop(-1)
		self.inProgress.append(url)
		return url

	def get_queue(self):
		return {
			'wait': self.downloadQueue,
			'done': self.downloadCompleted,
			'errors': self.downloadFailed,  # TODO Still not supported
			'in_progress': self.inProgress
		}

	def start_processing(self):
		while True:
			url = self._get_url()
			downloader = self._get_downloader(url)
			downloader.request_download(url)
			downloader.start_download()
			self.downloadCompleted.append(self.inProgress.pop())

	def _get_downloader(self, url):
		if 'crunchyroll.com' in url:
			return CrunchyrollDownloader(self.configuration, self.logging)
		else:
			if not any([x in url for x in self.testedHost]):
				self.logging.warning("Attempting download - Unknown provider: [" + url + "]")
				print("Attempting download - Unknown provider: [" + url + "]")
			return GenericDownloader(self.configuration, self.logging)
