import yt_dlp

from GenericDownloader import GenericDownloader


class CrunchyrollDownloader(GenericDownloader):

	sectionName = 'CrunchyrollSettings'

	def __init__(self, settings, logging_handler, dm):
		super().__init__(settings, logging_handler, dm)
		print(settings)

	def _start_download(self) -> None:
		lang = "itIT"
		url = self.managing_file['url']

		options = {
			'writesubtitles': True,
			'subtitleslangs': [lang],
			'skip_download': True,
		}
		with yt_dlp.YoutubeDL(options) as ydl:
			info_dict = ydl.extract_info(url, download=False)
			sub_ext = info_dict.get('requested_subtitles', {}).get(lang, {}).get('ext', None)
			subtitleName = info_dict.get('title', None) + "." + lang + "." + sub_ext
			self.logging.info("Downloading subtitle file: " + subtitleName)
			ydl.download(url)

		with yt_dlp.YoutubeDL({}) as ydl:
			info_dict = ydl.extract_info(url, download=True)
			title = info_dict.get('title', None)
			ext = info_dict.get('ext', None)
			videoName = title + "." + ext
			outputName = title + ".mkv"
			print("Downloading video file: " + videoName)

		self.joinVideo(videoName, subtitleName, lang, outputName)
		self.logging.info("Downloaded file: " + outputName)
		return outputName
