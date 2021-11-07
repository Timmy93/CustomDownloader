from GenericDownloader import GenericDownloader


class CrunchyrollDownloader(GenericDownloader):

	sectionName = 'CrunchyrollSettings'

	def __init__(self, settings, logging_handler, dm):
		super().__init__(settings, logging_handler, dm)
		print(settings)
