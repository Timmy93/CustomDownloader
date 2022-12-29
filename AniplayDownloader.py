import ast
import os
import time
import urllib.request
from pathlib import Path
from urllib.parse import unquote, urlparse
import requests
from GenericDownloader import GenericDownloader


class AniplayDownloader(GenericDownloader):

	sectionName = 'AniplaySettings'

	alreadyDownloadedList = []

	alreadyDownloadedListFile = "downloaded_episodes.txt"

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
		#self.logging = logging

	def get_info(self, url: str) -> dict:
		"""
		Extract further information on this url
		:param url: The url to analyze
		:return: The object containing further information
		"""
		res = {'dir_value': []}
		try:
			# Checking if passed an url to a release
			releaseLink = self.parseRelease(url)
			self._retrieveReleaseInfo(releaseLink)
			for episodeInfo in self.release["episodes"]:
				name = self._createEpisodeName(episodeInfo)
				epLink = "https://aniplay.it/api/download/episode/" + str(episodeInfo["id"])
				domain = urlparse(epLink).netloc
				res['dir_value'].append({'url': epLink, 'name': name, 'domain': domain})
		except ValueError:
			#Checking if passed an url to an episode
			try:
				print("URL: " + url)
				epLink = self.parseEpisode(url)
				print("URL 2: " + epLink)
				episodeInfo = self._getEpisodeInfo(url)
				print("INFO: ", episodeInfo)
				epName = self._createEpisodeName(episodeInfo)
				domain = urlparse(epLink).netloc
				res['dir_value'].append({'url': epLink, 'name': epName, 'domain': domain})
			except ValueError:
				print("Nothing to download")
		return res

	def _start_download(self) -> str:
		url = self.managing_file['url']
		print("Downloading: " + url)
		return self._downloadFile(url)

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
				print("WARNING - Cannot decode this release [" + e.msg + "]")
				print(response.content)
				try:
					self.release = ast.literal_eval(str(response.content))
					return True
				except:
					print("WARNING - Cannot evalue as dict")
					return False
		else:
			print("ERROR - Page not available ["+str(response.status_code)+"]")
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
		episodeInfo = self._getEpisodeInfo(url)
		name = self._createEpisodeName(episodeInfo)
		episodeId = str(episodeInfo["id"])
		episodeUrl = self.getDirectDownloadUrl(episodeId)
		print(episodeUrl)
		remote_name = unquote(Path(urlparse(episodeUrl).path).name)
		extension = Path(remote_name).suffix
		name = name + extension
		start = time.time()
		print("Downloading: " + name)
		urllib.request.urlretrieve(episodeUrl, name)
		end = time.time()
		elapsed = end - start
		size = os.path.getsize(name)
		speed = size / elapsed / 1024 / 1024
		print("Download completed [" + name + "]")
		print("Downloaded at " + str("%.2f" % speed) + " MB/s [" + str("%.2f" % (size / 1024 / 1024)) + "MB in " + str(
				"%.2f" % elapsed) + "s]")
		return name

	def _createEpisodeName(self, episodeInfo) -> str:
		"""
		Generate the episode name without extension from the collected information
		:param episodeInfo: The dict of information related to the episode
		:return: The name without extension
		"""
		episodeNumber = str(episodeInfo["episodeNumber"]).zfill(len(str(self.release["episodeNumber"])))
		seasonNumber = str(1).zfill(len(str(self.release["episodeNumber"])))
		name = self.release["title"] + " - S" + seasonNumber + "E" + episodeNumber
		if 'title' in episodeInfo and episodeInfo["title"]:
			episodeTitle = episodeInfo["title"]
			name = name + " - " + episodeTitle
		return name

	@staticmethod
	def parseRelease(url: str) -> str:
		"""
		Parse the link to a release
		:param url: The original link that refers to a release
		:return: The parsed link to release
		"""
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
			print("Not a release ["+url+"]")
			print(parse)
			raise ValueError("Not a release")
		return url

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
			# "https://aniplay.it/play/101663", "https://aniplay.it/download/101663"
		elif parts[1] == "api" and parts[2] == "download" and parts[3] == "episode" and str(parts[4]).isnumeric():
			pass
		else:
			print("Not an episode ["+url+"]")
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

	def _getEpisodeInfo(self, url: str) -> dict:
		"""
		Extract the information related to a specific episode
		:param url : The url to the specific episode
		:return: The information related to the episode
		"""
		episodeId = self._extractEpisodeCode(url)
		self.headers["Referer"] = "https://www.aniplay.it/download/" + episodeId
		response = requests.get(url, headers=self.headers)
		return response.json()
