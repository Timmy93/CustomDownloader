import os

import yt_dlp

from GenericDownloader import GenericDownloader


class CrunchyrollDownloader(GenericDownloader):

	sectionName = 'CrunchyrollSettings'

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
			info_dict = ydl.extract_info(url, download=False)
			videoName = ydl.prepare_filename(info_dict)
			sub_ext = info_dict.get('requested_subtitles', {}).get(lang, {}).get('ext', None)
			subtitleName = os.path.splitext(videoName)[0] + "." + lang + "." + sub_ext
			self.logging.info("Downloading subtitle file: " + subtitleName)
			ydl.download(url)

		with yt_dlp.YoutubeDL(self.options) as ydl:
			info_dict = ydl.extract_info(url, download=False)
			videoName = ydl.prepare_filename(info_dict)
			outputName = os.path.splitext(videoName)[0] + ".mkv"
			print("Downloading video file: " + videoName)

		self.joinVideo(videoName, subtitleName, lang, outputName)
		self.logging.info("Downloaded file: " + outputName)
		return outputName
