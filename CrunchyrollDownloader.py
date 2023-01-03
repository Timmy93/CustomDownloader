import os

import yt_dlp
import urllib.request

from GenericDownloader import GenericDownloader


class CrunchyrollDownloader(GenericDownloader):

	def __init__(self, settings, logging_handler, dm):
		super().__init__(settings, logging_handler, dm)
		print(settings)

	def _start_download(self) -> None:
		url = self.managing_file['url']
		options = {
			'writesubtitles': True,
			'skip_download': True,
		}
		if 'outtmpl' in self.options:
			options['outtmpl'] = self.options['outtmpl']
		if 'subtitleslangs' in self.options:
			options['subtitleslangs'] = self.options['subtitleslangs']
		lang = options['subtitleslangs'][0]

		with yt_dlp.YoutubeDL(options) as ydl:
			#Preparing subtitle file
			info_dict = ydl.extract_info(url, download=False)
			videoName = ydl.prepare_filename(info_dict)
			lang_parsed = lang[:2] + "-" + lang[2:]
			sub_ext_info = info_dict.get('subtitles', {}).get(lang_parsed, [{}])[0]
			sub_ext = sub_ext_info.get('ext', None)
			directDownloadLink = sub_ext_info.get('url', None)
			if sub_ext and directDownloadLink:
				subtitleName = os.path.splitext(videoName)[0] + "." + lang + "." + sub_ext
				self.logging.info("Downloading subtitle file: " + subtitleName)
				urllib.request.urlretrieve(directDownloadLink, subtitleName)
			else:
				subtitleName = None
				self.logging.warning("Cannot extract subtitle language - Skipping selection")

		with yt_dlp.YoutubeDL(self.options) as ydl:
			print("Downloading video file: " + videoName)
			info_dict = ydl.extract_info(url, download=True)
			videoName = ydl.prepare_filename(info_dict)
			outputName = os.path.splitext(videoName)[0] + ".mkv"

		if subtitleName:
			#Impress subtitle only if found
			self.joinVideo(videoName, subtitleName, lang, outputName)
		self.logging.info("Downloaded file: " + outputName)
		if os.path.isfile(outputName):
			os.remove(subtitleName)
			os.remove(videoName)
			self.logging.info("Deleted temporary files")
		else:
			self.logging.warning("Cannot delete temporary files ["+subtitleName+"]["+videoName+"] - SKIP")
		return os.path.basename(outputName)
