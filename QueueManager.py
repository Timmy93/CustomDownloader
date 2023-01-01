from __future__ import annotations
import logging
from threading import Condition
import copy
from typing import Union


class NoElementAvailable(Exception):
	pass


class QueueManager:

	def __init__(self, settings: 'IUBConfiguration', logging_handler: 'logging', dm: 'DownloaderManager'):
		self.dm = dm
		self.logging = logging_handler
		self.configuration = settings
		self.queues = {
			'downloadQueue': [],
			'downloadFailed': [],
			'inProgress': [],
			'paused': [],
			'downloadCompleted': []
		}
		self.queueLock = Condition()

	def get_queues(self):
		return copy.deepcopy(self.queues)

	def change_queue(self, url: str, source_queue: str, destination_queue: str) -> bool:
		"""
		Move an element from a queue to another
		:param url: The url that is used to identify the element to move
		:param source_queue: The queue where the url will be searched
		:param destination_queue: The queue where the url will be placed
		:return: True if the change queue was successful. False if there was an error.
		"""
		# Initial check
		if not all(x in self.queues for x in [source_queue, destination_queue]):
			self.logging.error("Invalid queues: " + source_queue + " -> " + destination_queue)
			return False
		# File movement
		with self.queueLock:
			for idx, el in enumerate(copy.deepcopy(self.queues[source_queue])):
				if el["url"] == url:
					self.logging.info("Moving url ["+url+"] from "+source_queue+" to " + destination_queue)
					self.queues[destination_queue].append(self.queues[source_queue].pop(idx))
					# A download is completed, check if another file can be downloaded
					if source_queue == "inProgress":
						self.queueLock.notifyAll()
					return True
			self.logging.warning("Cannot find the requested url from the list " + source_queue)
			return False

	def add_file(self, file: dict, destination_queue: str = "downloadQueue") -> bool:
		"""
		Add a new file to a specific queue
		:param file: The file to add to the queue
		:param destination_queue: The queue where the file will be placed
		:return: The append operation outcome
		"""
		# Initial check
		if destination_queue not in self.queues:
			self.logging.error("Invalid destination queue: " + destination_queue)
			return False
		# File movement
		with self.queueLock:
			self.queues[destination_queue].append(file)
			# Added a new link, check if it can be downloaded
			self.queueLock.notifyAll()
			return True

	def addBatchFiles(self, batchList: list, destination_queue: str = "downloadQueue") -> bool:
		# Initial check
		if destination_queue not in self.queues:
			self.logging.error("Invalid destination queue: " + destination_queue)
			return False
		# File movement
		with self.queueLock:
			for file in batchList:
				self.queues[destination_queue].append(file)
			# Added a new link, check if it can be downloaded
			self.queueLock.notifyAll()
			return True

	def get_next_file(self) -> dict:
		"""
		An infinite loop that continuously tries to retrieve an available url to download
		:return: The element to download
		"""
		with self.queueLock:
			self.queueLock.wait_for(self._available_url)
			return self._get_next_element()

	def already_managing(self, url: str) -> bool:
		significant_queues = ['downloadQueue', 'inProgress', 'paused']
		with self.queueLock:
			for queue in significant_queues:
				for el in self.queues[queue]:
					if el['url'] == url:
						return True
			return False

	def update_download_progress(self, filename: str, percentage: float):
		pass
		# TODO Currently not working save reference to correct downloader
		# with self.queueLock:
		# 	for file in self.queues['downloadQueue']:
		# 		if file["name"] == filename:
		# 			file["status"] = percentage
		# 			self.logging.info("Updated percentage for this file " + file["name"])
		# 			return
		# 		else:
		# 			self.logging.info("Different name: [" + filename + "] - [" + file["name"] + "] - SKIP")
		# 	print("File [" + filename + "] updated, status:" + str(percentage))

	def _get_queue_overview(self, queue: str = 'inProgress'):
		"""
		Retrieve an overview of the host in the current queue
		:return: A dictionary containing the count of the elements in the queue
		"""
		overview = {}
		for el in self.queues[queue]:
			if el['host'] in overview:
				overview[el['host']] += 1
			else:
				overview[el['host']] = 1
		return overview

	def _get_next_element(self) -> Union[dict, None]:
		"""
		Retrieves the first available element from the download queue
		:return: The element to download. None in case of errors
		"""
		try:
			index = self._get_index_first_element_available()
			el = self.queues['downloadQueue'].pop(index)
			self.queues['inProgress'].append(el)
			self.logging.info("Downloading: " + str(el))
			return el
		except NoElementAvailable:
			self.logging.warning("No available url in the queue - Probable concurrency error")
			return None

	def _available_url(self) -> bool:
		"""
		Check if there is any available link in the queue
		:return: True if there is at least one link that can be processed. False otherwise.
		"""
		# Check if there are any further link to download
		if len(self.queues['downloadQueue']) == 0:
			return False
		# Check if limits of simultaneous download has been reached
		if len(self.queues['inProgress']) >= self.configuration.get_config('GlobalSettings', 'maxTotalDownload'):
			return False
		# Check max count per host
		try:
			self._get_index_first_element_available()
			return True
		except NoElementAvailable:
			return False

	def _get_index_first_element_available(self) -> int:
		"""
		Check if there is at least one host that can be processed in the download queue
		:return: The index containing the first available element. Raise NoElementAvailable if no element is found
		"""
		queue_overview = self._get_queue_overview()
		for idx, el in enumerate(copy.deepcopy(self.queues['downloadQueue'])):
			if 'host' not in el:
				self.logging.warning("Missing information on host in this object [" + str(el) + "] - Skipping host limitation")
				return idx
			# This host is not in the download list, proceed
			if el['host'] not in queue_overview:
				self.logging.info("File not in logging overview")
				return idx
			# This host has not reached the global limit per host
			sectionName = self.dm.get_downloader(el['host']).sectionName
			if queue_overview.get(el['host']) < self.configuration.get_config(sectionName, 'maxDownloadPerHost'):
				return idx
		raise NoElementAvailable()
