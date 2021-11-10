import threading
from threading import Event

from youtube_dl import YoutubeDL

from CrunchyrollDownloader import CrunchyrollDownloader
from GenericDownloader import GenericDownloader


class Singleton(type):
	_instances = {}

	def __call__(cls, *args, **kwargs):
		if cls not in cls._instances:
			cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
		return cls._instances[cls]


class DownloaderManager(threading.Thread, metaclass=Singleton):

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
		if not isinstance(url, str):
			self.logging.info("Not a valid link passed")
			return
		if url in self.downloadQueue:
			self.logging.info("Already downloading: [" + url + "] - Skip")
			return
		self.logging.info("Adding new url to download list [" + url + "]")
		self._append_url(url)

	def _append_url(self, url):
		"""
		Analyze the given url and try to add it to the list
		:param url: The url to download
		:return: The complete object to manage
		"""
		el = self._analyze_url(url)
		self.downloadQueue.append(el)
		self.urlAvailable.set()

	def _get_url(self):
		while len(self.downloadQueue) == 0:
			# Stop Download manager, start waiting for a new url
			self.logging.info("Stopping download manager - No url to download")
			print("Download Manager paused - Waiting for new url")
			self.urlAvailable.clear()
			self.urlAvailable.wait()
			self.logging.info("Resuming download manager - New url found")
		el = self.downloadQueue.pop(-1)
		self.inProgress.append(el)
		return el

	def get_queue(self):
		return {
			'wait': self.downloadQueue,
			'done': self.downloadCompleted,
			'errors': self.downloadFailed,  # TODO Still not supported
			'in_progress': self.inProgress
		}

	def start_processing(self):
		while True:
			file = self._get_url()
			downloader = self._get_downloader(file)
			downloader.process_download(file)
			downloader.start_download()
			self.downloadCompleted.append(self.inProgress.pop())

	def _get_downloader(self, file):
		url = file["url"]
		if 'crunchyroll.com' in url:
			return CrunchyrollDownloader(self.configuration, self.logging, self)
		else:
			if not any([x in url for x in self.testedHost]):
				self.logging.warning("Attempting download - Unknown provider: [" + url + "]")
				print("Attempting download - Unknown provider: [" + url + "]")
			return GenericDownloader(self.configuration, self.logging, self)

	def _analyze_url(self, url):
		with YoutubeDL({}) as ydl:
			info_dict = ydl.extract_info(url, download=False)
			video_title = info_dict.get('title', None)
			self.logging.info("Added url: " + video_title)
			return {'url': url, 'name': video_title}

	def update_download_progress(self, filename, percentage):
		#todo - download queue empty
		for file in self.downloadQueue:
			if file["name"] == filename:
				file["status"] = percentage
				self.logging.info("Updated percentage for this file " + file["name"])
			else:
				self.logging.info("Different name: [" + filename + "] - [" + file["name"] + "] - SKIP")
		print("Updated")

