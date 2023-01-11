import ast
import os
import string
import time
import urllib.request
from pathlib import Path
from urllib.parse import unquote, urlparse
from urllib.error import HTTPError
import ffmpeg
import requests
from unidecode import unidecode

from Downloaders.GenericDownloader import GenericDownloader


class AniplayDownloader(GenericDownloader):

	headers = {
		"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:108.0) Gecko/20100101 Firefox/108.0",
		"Accept": "application/json, text/plain, */*",
		"Accept-Language": "it-IT,it;q=0.8,en-US;q=0.5,en;q=0.3",
		"Accept-Encoding": "gzip, deflate",
		"DNT": "1",
		"Sec-Fetch-Dest": "empty",
		"Sec-Fetch-Mode": "cors",
		"Sec-Fetch-Site": "same-origin",
		"Connection": "keep-alive",
		"TE": "trailers"
	}

	def __init__(self, configuration, logging, dm):
		super().__init__(configuration, logging, dm)
		self.logging.info("Aniplay Downloader - Created")
		# The download status
		self.percentage = 0

	def get_info(self, url: str) -> dict:
		"""
		Extract further information on this url
		:param url: The url to analyze
		:return: The object containing further information
		"""
		res = {'dir_value': []}
		if self.isARelease(url):
			self.logging.info("Managing this release: [" + url + "]")
			releaseLink = self.parseRelease(url)
			self._retrieveReleaseInfo(releaseLink)
			#Extract season episodes
			if "seasons" in self.release and self.release["seasons"]:
				for seasonInfo in self.release["seasons"]:
					self.release["episodes"] += self._retrieveSeasonEpisodes(seasonInfo)
			#Analyze all episodes
			for episodeInfo in self.release["episodes"]:
				name = self._createEpisodeName(episodeInfo)
				episodeId = str(episodeInfo["id"])
				epLink = "https://aniplay.it/api/download/episode/" + episodeId
				domain = urlparse(epLink).netloc
				res['dir_value'].append({'url': epLink, 'name': name, 'host': domain})
				self.logging.info("Adding episode: " + name + " [" + epLink + "]")
		elif self.isAnEpisode(url):
			epLink = self.parseEpisode(url)
			episodeInfo = self._getDownloadEpisodeInfo(epLink)
			if episodeInfo:
				epName = self._createEpisodeName(episodeInfo)
				domain = urlparse(epLink).netloc
				res['dir_value'].append({'url': epLink, 'name': epName, 'host': domain})
				self.logging.info("Adding episode: " + epName + " [" + epLink + "]")
			else:
				self.logging.warning("Cannot extract info on this episode: [" + epLink + "]")
		else:
			self.logging.info("The passed url is not a supported Aniplay link: [" + url + "]")
			print("Nothing to download")
		return res

	def _start_download(self) -> str:
		self.logging.info("Starting download of this file: ", self.managing_file)
		url = self.managing_file['url']
		start = time.time()
		try:
			downloadFileLocation = self._downloadFile(url)
		except HTTPError:
			self.logging.warning("Direct download file not available [" + url + "] - Attempt download from streaming file")
			downloadFileLocation = self._downloadStreamingFile(url)
		downloadFileName = os.path.basename(downloadFileLocation)
		end = time.time()
		elapsed = end - start
		size = os.path.getsize(downloadFileLocation)
		speed = size / elapsed / 1024 / 1024
		print("Download completed [" + downloadFileName + "]")
		self.logging.info("Download completed [" + downloadFileName + "]")
		print("Downloaded at " + str("%.2f" % speed) + " MB/s [" + str("%.2f" % (size / 1024 / 1024)) + "MB in " + str(
			"%.2f" % elapsed) + "s]")
		self.logging.info("Downloaded at " + str("%.2f" % speed) + " MB/s [" + str("%.2f" % (size / 1024 / 1024)) + "MB in " + str(
			"%.2f" % elapsed) + "s]")
		return downloadFileName

	def _retrieveReleaseInfo(self, url: str) -> bool:
		"""
		Extract the information related to the release.
		:param url: The url of a release
		:return: True if it is possible to extract
		"""
		headers = self.headers
		headers["Referer"] = url
		response = requests.get(url, headers=headers)
		if response.status_code < 400:
			try:
				self.release = response.json()
				return True
			except requests.exceptions.JSONDecodeError as e:
				print("WARNING - Cannot decode this release [" + str(e) + "]")
				self.logging.warning("Cannot decode this release [" + str(e) + "]")
				self.logging.warning(response.content)
				try:
					self.release = ast.literal_eval(str(response.content))
					return True
				except:
					self.logging.warning("Cannot execute literal evaluation as dict")
					print("WARNING - Cannot evalue as dict")
					return False
		else:
			self.logging.error("Page not available [" + str(response.status_code) + "]")
			print("ERROR - Page not available [" + str(response.status_code) + "]")
			return False

	def getDirectDownloadUrl(self, episodeId: str) -> str:
		"""
		Extract the direct link of a certain episode
		:param episodeId: The episode id
		:return: The direct link to the episode
		"""
		self.headers["Referer"] = "https://www.aniplay.it/download/" + episodeId
		url = "https://aniplay.it/api/download/episode/" + episodeId + "/link"
		response = requests.get(url, headers=self.headers)
		return response.json()["downloadUrl"]

	def _downloadFile(self, url: str) -> str:
		"""
		Download the given file
		:param url: The url of the episode to download
		:return: The name of the downloaded file
		"""
		#Get episode info
		episodeInfo = self._getDownloadEpisodeInfo(url)
		if not episodeInfo:
			self.logging.warning("Cannot extract information on this episode [", url, "] - Cannot proceed with download")
			raise ImpossibleDownload("Cannot extract information on this episode")
		#Get direct download link
		directDownloadLink = self.getDirectDownloadUrl(str(episodeInfo["id"]))
		#Generate file name
		name = self.generateFileName(episodeInfo, directDownloadLink)
		#Define temporary file location
		temp_location = os.path.join(self.getTempDir(), name)
		self.logging.info("Starting direct download")
		#Execute download
		opener = urllib.request.build_opener()
		opener.addheaders = [
			('Referer', 'https://aniplay.it/'),
			('User-Agent', self.headers['User-Agent']),
			('Sec-Fetch-Site', 'cross-site'),
			('Sec-Fetch-Mode', 'navigate'),
			('Sec-Fetch-Dest', 'document')
		]
		urllib.request.install_opener(opener)
		urllib.request.urlretrieve(directDownloadLink, temp_location, reporthook=self.download_hook)
		return temp_location

	def _downloadStreamingFile(self, url: str) -> str:
		"""
		Start the download from Streaming Link
		:param url: The url of the episode
		:return: The name of the downloaded file
		"""
		# Get episode info
		episodeInfo = self._getStreamingEpisodeInfo(url)
		if not episodeInfo:
			self.logging.warning("Cannot extract information on this episode [", url, "] - Cannot proceed with download")
			raise ImpossibleDownload("Cannot extract information on this episode")
		# Get direct download link
		if 'videoUrl' not in episodeInfo or not episodeInfo['videoUrl']:
			self.logging.warning("Missing streaming link  [" + str(url) + "] - Cannot proceed with download")
			raise ImpossibleDownload("Missing streaming link")
		directDownloadLink = episodeInfo['videoUrl']
		# Generate file name
		name = self._createEpisodeName(episodeInfo) + ".mp4"
		# Define temporary file location
		temp_location = os.path.join(self.getTempDir(), name)
		# Execute download
		self.logging.info("Starting streaming download")
		print("Starting streaming download")
		self._downloadFileFromStreaming(directDownloadLink, temp_location, reporthook=self.download_hook)
		return temp_location

	def generateFileName(self, episodeInfo, episodeUrl):
		"""
		Extract the extension from the direct download url and generates url
		:param episodeInfo:
		:param episodeUrl:
		:return:
		"""
		name = self._createEpisodeName(episodeInfo)
		remote_name = unquote(Path(urlparse(episodeUrl).path).name)
		extension = Path(remote_name).suffix
		name = name + extension
		return name

	def download_hook(self, blockTrasferred: int, blockSize: int, totalSize: int):
		self.check_download_to_stop()
		downloadSize = blockTrasferred*blockSize
		percentage = round(downloadSize * 100 / totalSize, 1)
		if percentage != self.percentage:
			self.percentage = percentage
			print(str("%.2f" % self.percentage) + "% - Downloaded " + str("%.2f" % (downloadSize / 1024 / 1024)) + "MB of " + str("%.2f" % (totalSize / 1024 / 1024)) + "MB")
		self.download_manager.update_download_progress(self.managing_file['url'], self.percentage)

	def _createEpisodeName(self, episodeInfo) -> str:
		"""
		Generate the episode name without extension from the collected information
		:param episodeInfo: The dict of information related to the episode
		:return: The name without extension
		"""
		if not hasattr(self, 'release'):
			# Extract info on the release if missing
			self.logging.info("Extracting info on this release [" + str(episodeInfo["animeId"]) + "]")
			self._retrieveReleaseInfo(self.parseRelease(releaseId=episodeInfo["animeId"]))
		if "episodeNumber" not in self.release or not self.release["episodeNumber"]:
			self.release["episodeNumber"] = 0
		episodeNumber = str(episodeInfo["episodeNumber"]).zfill(max(2, len(str(self.release["episodeNumber"]))))
		seasonNumber = "01"
		name = self.release["title"] + " - S" + seasonNumber + "E" + episodeNumber
		if 'title' in episodeInfo and episodeInfo["title"]:
			episodeTitle = episodeInfo["title"]
			name = name + " - " + episodeTitle
		name = name + "[Aniplay]"
		return self.makeSafeFilename(name)

	@staticmethod
	def parseRelease(url: str = "", releaseId: int = None) -> str:
		"""
		Parse the link to a release
		:param url: The original link that refers to a release
		:param releaseId: The reference to the release id
		:return: The link to the api release link
		"""
		if releaseId:
			return "https://aniplay.it/api/anime/" + str(releaseId)
		elif url:
			url = url.strip()
			parse = urlparse(url)
			parts = parse.path.split("/")
			if len(parts) <= 1:
				print("Invalid url")
				raise ValueError("Invalid url")
			elif parts[1] == "anime" and str(parts[2]).isnumeric():
				url = parse.scheme + "://" + parse.netloc + "/api/anime/" + str(parts[2])
			elif parts[1] == "api" and parts[2] == "anime" and str(parts[3]).isnumeric():
				pass
			else:
				print("Not a release [" + url + "]")
				print(parse)
				raise ValueError("Not a release")
			return url
		else:
			print("No valid id or url was passed")
			raise ValueError("Not a release")

	@staticmethod
	def parseEpisode(url: str) -> str:
		"""
		Parse the link to an episode
		:param url: The original link that refers to an episode
		:return: The parsed link to the episode
		"""
		url = url.strip()
		parse = urlparse(url)
		parts = parse.path.split("/")
		if len(parts) <= 1:
			print("Invalid url")
			raise ValueError("Invalid url")
		elif parts[1] in ["play", "download"] and str(parts[2]).isnumeric():
			url = parse.scheme + "://" + parse.netloc + "/api/download/episode/" + str(parts[2])
		elif parts[1] == "api" and parts[2] == "download" and parts[3] == "episode" and str(parts[4]).isnumeric():
			pass
		elif parts[1] == "api" and parts[2] == "episode" and str(parts[3]).isnumeric():
			url = parse.scheme + "://" + parse.netloc + "/api/download/episode/" + str(parts[3])
		else:
			print("Not an episode [" + url + "]")
			print(parse)
			raise ValueError("Not a release")
		return url

	@staticmethod
	def _extractEpisodeCode(url: str) -> str:
		"""
		Extract the episode code from the episode link
		:param url: The url to the episode
		:return: The code of the episode
		"""
		url = url.strip()
		parse = urlparse(url)
		parts = parse.path.split("/")
		result = None
		for part in parts:
			if str(part).isnumeric():
				result = part
		return str(result)

	def _getDownloadEpisodeInfo(self, apiUrl: str) -> dict:
		"""
		Extract the information related to the download of a specific episode
		:param apiUrl : The url to the specific episode
		:return: The information related to the episode
		"""
		episodeId = self._extractEpisodeCode(apiUrl)
		self.headers["Referer"] = "https://www.aniplay.it/download/" + episodeId
		response = requests.get(apiUrl, headers=self.headers)
		if response.status_code >= 400:
			self.logging.warning("Episode download not available: [" + str(response.status_code) + "]")
			self.logging.warning("URL: [" + apiUrl + "] - Headers: [" + str(self.headers) + "]")
			return {}
		return response.json()

	def _getStreamingEpisodeInfo(self, url: str) -> dict:
		"""
		Extract the information related to the streaming of a specific episode
		:param url : The url to the specific episode
		:return: The information related to the episode
		"""
		episodeId = self._extractEpisodeCode(url)
		apiUrl = "https://aniplay.it/api/episode/" + episodeId
		self.headers["Referer"] = "https://www.aniplay.it/play/" + episodeId
		response = requests.get(apiUrl, headers=self.headers)
		if response.status_code >= 400:
			self.logging.warning("Episode streaming not available: [" + str(response.status_code) + "]")
			self.logging.warning("URL: [" + apiUrl + "] - Headers: [" + str(self.headers) + "]")
			return {}
		return response.json()

	@staticmethod
	def isARelease(url: str) -> bool:
		url = url.strip()
		parse = urlparse(url)
		parts = parse.path.split("/")
		if len(parts) <= 1:
			print("Invalid url")
			return False
		elif parts[1] == "anime" and str(parts[2]).isnumeric():
			return True
		elif parts[1] == "api" and parts[2] == "anime" and str(parts[3]).isnumeric():
			return True
		else:
			return False

	@staticmethod
	def isAnEpisode(url: str) -> bool:
		url = url.strip()
		parse = urlparse(url)
		parts = parse.path.split("/")
		if len(parts) <= 1:
			return False
		elif parts[1] in ["play", "download"] and str(parts[2]).isnumeric():
			return True
		elif parts[1] == "api" and parts[2] == "download" and parts[3] == "episode" and str(parts[4]).isnumeric():
			return True
		else:
			print("Not an episode [" + url + "]")
			print(parse)
			return False

	def moveToFinalLocation(self, temp_location: str, name: str):
		"""
		Moves the downloaded file to the final location
		:param temp_location: The current file position
		:param name: The name of the file to move
		:return:
		"""
		finalDir = self.options['outtmpl']
		if '%' in os.path.basename(finalDir):
			#Ignoring the output format provided
			finalDir = os.path.dirname(finalDir)
		finalLocation = os.path.join(finalDir, name)
		os.replace(temp_location, finalLocation)
		self.logging.info("File [" + name + "] moved to dir [" + finalDir + "]")

	@staticmethod
	def makeSafeFilename(inputFilename):
		unidecodedName = unidecode(inputFilename)
		#Set here the valid chars
		safechars = string.ascii_letters + string.digits + "~ -_.[]()"
		finalName = ""
		for char in unidecodedName:
			if char in safechars:
				finalName = finalName + char
		return finalName

	def getTempDir(self):
		finalDir = self.options['tempDir']
		if '%' in os.path.basename(finalDir):
			#Ignoring the output format provided
			finalDir = os.path.dirname(finalDir)
		self.logging.info("Temporary directory for download: " + finalDir)
		return finalDir

	def _downloadFileFromStreaming(self, directStreamingLink: str, temp_location: str, reporthook: callable):
		"""
		Attempt download from the HLS link (m3u8) using ffmpeg
		:param directStreamingLink: The direct link to m3u8
		:param temp_location: Where the file will be called
		:param reporthook: A callback function to monitor the download progress
		:return:
		"""
		stream = ffmpeg.input(directStreamingLink, headers='referer: https://aniplay.it/')
		output_ffmpeg = ffmpeg.output(stream, temp_location, vcodec='copy', acodec='copy')
		output_ffmpeg = ffmpeg.overwrite_output(output_ffmpeg)
		self.logging.info("Start downloading streaming file")
		ffmpeg.run(output_ffmpeg, quiet=True)

	def _retrieveSeasonEpisodes(self, seasonInfo: dict) -> list:
		"""
		Extract the episode list from the season information
		:param seasonInfo: The season information
		:return: The list of episodes information
		"""
		animeId = str(seasonInfo['animeId'])
		seasonId = str(seasonInfo['id'])
		self.logging.info("Extracting episodes from season: " + seasonInfo['name'] + " [" + seasonId + "]")
		url = "https://aniplay.it/api/anime/" + animeId + "/season/" + seasonId
		refererUrl = "https://aniplay.it/anime/" + animeId
		headers = self.headers
		headers["Referer"] = refererUrl
		response = requests.get(url, headers=headers)
		return response.json()


class ImpossibleDownload(Exception):
	pass
