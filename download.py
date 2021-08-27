#!/usr/bin/env python3
import getopt
import logging
import os
import sys
import youtube_dl
from Configuration import Configuration
from CruncyrollDownloader import CrunchyrollDownloader

# Details on parameters here:
#   https://github.com/ytdl-org/youtube-dl/blob/3e4cedf9e8cd3157df2457df7274d0c842421945/youtube_dl/YoutubeDL.py#L137-L312

logName = "Downloader.log"
all_settings_dir = "Settings"
setting_file = "settings.yml"
tested_host = [
	'youtube.com',
]


def main():
	global logName, setting_file, all_settings_dir
	logging.basicConfig(
		filename=create_absolute_path(logName),
		level=logging.ERROR,
		format='%(asctime)s %(levelname)-8s %(message)s')
	url = []
	# output_dir = os.getcwd()
	setting_path = os.path.join(all_settings_dir, setting_file)
	config_class = Configuration(setting_path, logging)

	if config_class.get_config('GlobalSettings', 'commandLineEnabled'):
		logging.debug("Retrieving files from command line")
		parameters = retrieve_command_line_parameters()
		url += parameters['url']
	else:
		logging.debug("Command line disabled, settings value: " + str(config_class.get_config('GlobalSettings', 'commandLineEnabled')))

	download(url, config_class)

	print("Downloaded ", len(url), " urls")


def retrieve_command_line_parameters():
	print("START")
	result = {
		'url': []
	}
	try:
		opts, args = getopt.getopt(sys.argv[1:], "hu:o:", ["url=", "output="])
	except getopt.GetoptError:
		print('download.py -u <urlToDownload> -o <outputfile>')
		sys.exit(2)
	for opt, arg in opts:
		if opt == '-h':
			print('download.py -u <urlToDownload> -o <outputfile>')
			sys.exit(2)
		elif opt in ('-o', 'output'):
			print("Option: Writing output in: " + arg)
			result['output_dir'] = arg
		elif opt in ('-u', 'url'):
			print("Option: Adding url to list: " + arg)
			result['url'].append(arg)
	for arg in args:
		print("parameter: Adding url to list: " + arg)
		result['url'].append(arg)
	return result


def generic_download(url, settings):
	ydl_opts = {'outtmpl': settings.get_config('GlobalSettings', 'outtmpl')}
	with youtube_dl.YoutubeDL(ydl_opts) as ydl:
		print("Downloading: " + url)
		ydl.download([url])
		print("Done!")


def download(urls, settings):
	cr = CrunchyrollDownloader(settings, logging)
	for url in urls:
		if 'crunchyroll.com' in url:
			cr.request_download(url)
		else:
			if not any([x in url for x in tested_host]):
				print("Attempting download - Unknown provider: [", url, "]")
			generic_download(url, settings)

	cr.start_download()


def get_settings(name=None):
	if name is None:
		return


def create_absolute_path(path):
	# Check if the given path is an absolute path
	if not os.path.isabs(path):
		current_dir = os.path.dirname(os.path.realpath(__file__))
		path = os.path.join(current_dir, path)

	return path


if __name__ == "__main__":
	main()
