from __future__ import annotations
import logging
import os
import threading
from urllib.parse import urlparse
import yaml
from QueueManager import QueueManager
from IUBBaseTools import IUBConfiguration

#Import all downloaders
from Downloaders.GenericDownloader import GenericDownloader
from Downloaders.AniplayDownloader import AniplayDownloader
from Downloaders.CrunchyrollDownloader import CrunchyrollDownloader


class DownloaderManager(threading.Thread):

	supportedHost = [
		'youtube.com',
		'youtu.be',
		'crunchyroll.com',
		'aniplay.it'
	]
	"""
	The list of supported host
	"""

	testedHost = [
		'youtube.com',
		'youtu.be',
		'aniplay.it'
	]
	"""
	The list of host that work correctly using the generic downloader
	"""

	all_settings_dir = "Settings"
	setting_file = "settings.yml"
	association_file = "association.yml"

	def __init__(self, settings: IUBConfiguration, logging_handler: logging):
		super().__init__()
		self.queueManager = QueueManager(settings, logging, self)
		self.downloaderAssociation = self.loadAssociationList()
		self.registeredDownload = []
		self.registrationLock = threading.Condition()
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
				downloader = self.get_downloader(file['url'])
				downloader.process_download(file)
				downloader.start()
				self.logging.info("Started download of: " + str(file))
				print("Started download of: " + file['name'] + "[" + file['url'] + "]")
			else:
				self.logging.info("Received invalid download file, ignoring it")

	def registerDownloader(self, url: str, downloader: GenericDownloader):
		"""
		Associate an url to the relative downloader
		:param url:
		:param downloader:
		:return:
		"""
		with self.registrationLock:
			self.registeredDownload.append({'url': url, 'downloader': downloader})

	def unregisterDownloader(self, url):
		"""
		Remove the association to a downloader of the url
		:param url:
		:return:
		"""
		with self.registrationLock:
			for registration in self.registeredDownload:
				if registration['url'] == url:
					self.registeredDownload.remove(registration)

	def complete_this_download(self, file: dict):
		return self.queueManager.change_queue(file["url"], 'inProgress', 'downloadCompleted')

	def request_pause_this_download(self, file: dict):
		"""
		Send a request to pause a download
		:param file:
		:return:
		"""
		for registration in self.registeredDownload:
			if registration['url'] == file['url']:
				self.logging.info("Sendind request for pausing this download: " + file['url'])
				registration['downloader'].stop_download()

	def pause_this_download(self, file: dict):
		"""
		Stop of an active download
		:param file: The file to stop download
		:return:
		"""
		return self.queueManager.change_queue(file["url"], 'inProgress', 'paused')

	def fail_this_download(self, file: dict):
		"""
		Handle all the activities related to the download failure
		:param file: The file that cannot be downloaded
		:return:
		"""
		self.logging.info("Download failed: [" + file["url"] + "]")
		self.unregisterDownloader(file["url"])
		return self.queueManager.change_queue(file["url"], 'inProgress', 'downloadFailed')

	def cancel_download(self, url: str) -> bool:
		"""
		Cancel a download
		:param url:
		:return:
		"""
		if url:
			file, queue = self.queueManager.retrieveFileFromUrl(url, QueueManager.ALL_QUEUES)
			if queue == QueueManager.DOWNLOAD_ACTIVE:
				self.logging.info("Pausing download: " + str(url))
				self.request_pause_this_download(file)
			else:
				self.logging.info("Deleting url: " + str(url))
				return self.queueManager.delete_from_queue(url)
		else:
			self.logging.warning("No url to delete received")
			return False

	def restart_download(self, url: str) -> bool:
		"""
		Try to restore the download of an url
		:param url: The failed url to restore
		:return: True if the restart was successful, false otherwise
		"""
		if url:
			self.logging.info("Restarting url: " + str(url))
			file, queue = self.queueManager.retrieveFileFromUrl(url, [QueueManager.DOWNLOAD_FAILED])
			self.queueManager.delete_file_from_queue(file, queue)
			return self.queueManager.addBatchFiles([file])
		else:
			self.logging.warning("No url to delete received")
			return False

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
		if 'dir_value' in el:
			self.queueManager.addBatchFiles(el['dir_value'])
		else:
			self.queueManager.addBatchFiles([el])

	def get_queue(self):
		return self.queueManager.get_queues()

	def get_downloader(self, url: str):
		"""
		Dynamically retrieve the downloader to use to manage this file
		:param url: The url to manage
		:return: The downloader instance
		"""
		host = urlparse(url).netloc
		info = self.extractSettingsAssociation(host)
		className = info["downloaderName"]
		constructor = globals()[className]
		instance = constructor(self.configuration, self.logging, self)
		self.logging.info("Dynamically created an instance of: " + className)
		return instance

	def update_download_progress(self, url: str, percentage: float):
		self.queueManager.update_download_progress(url, percentage)

	def loadAssociationList(self) -> dict:
		"""
		Retrieve the association list containing all the relevant information on Settings, Downloader and associated domains
		:return:
		"""
		#Create correct path to the association list
		path = os.path.join(DownloaderManager.all_settings_dir, DownloaderManager.association_file)
		if not os.path.isabs(path):
			currentDir = os.path.dirname(os.path.realpath(__file__))
			path = os.path.join(currentDir, path)

		#Load content of the association list
		with open(path, 'r') as stream:
			try:
				config = yaml.safe_load(stream)
				return config['Association']
			except yaml.YAMLError as exc:
				print("Cannot load file: [" + path + "] - Error: " + str(exc))
				self.logging.error("Cannot load file: [" + path + "] - Error: " + str(exc))
				exit(1)

	def extractSettingsAssociation(self, domain: str) -> dict:
		genericInfo = None
		# Remove www if present
		domain = domain.replace("www.", "")
		for downloader in self.downloaderAssociation['downloader']:
			#Check association
			key = list(downloader.keys())[0]
			if domain in downloader[key]['associatedDomains']:
				return downloader[key]
			# Extract generic info
			if key == 'generic':
				genericInfo = downloader[key]

		self.logging.warning("Untested domain - Getting generic section")
		if genericInfo:
			return genericInfo
		else:
			self.logging.error("Missing section generic in association file - EXIT")
			exit(1)

	def extractSettingsAssociationFromDownloaderName(self, className: str) -> dict:
		for downloader in self.downloaderAssociation['downloader']:
			# Check association
			key = list(downloader.keys())[0]
			if className in downloader[key]['downloaderName']:
				return downloader[key]
		self.logging.error("Missing information for this downloader [" + className + "] - EXIT")
		exit(1)

	def loadHistory(self):
		"""
		Load the history from a file populates the different queue
		:return:
		"""
		#Load history
		with open('history.yml', 'r') as f:
			rawList = yaml.safe_load(f)
		#Parse
		rawList[QueueManager.DOWNLOAD_QUEUE] = rawList[QueueManager.DOWNLOAD_ACTIVE] + rawList[QueueManager.DOWNLOAD_QUEUE]
		rawList[QueueManager.DOWNLOAD_ACTIVE] = []
		#Load
		for queue in rawList:
			self.queueManager.addBatchFiles(rawList[queue], queue)

	def saveHistory(self):
		finalList = {}
		#Load history
		queues = self.get_queue()
		#Store
		with open('history.yml', 'w') as f:
			yaml.safe_dump(queues, f)
