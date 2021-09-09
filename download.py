#!/usr/bin/env python3
import getopt
import logging
import os
import sys
from Configuration import Configuration
from DownloaderManager import DownloaderManager
from flask import Flask, request, render_template
from markupsafe import escape

# Details on parameters here:
#   https://github.com/ytdl-org/youtube-dl/blob/3e4cedf9e8cd3157df2457df7274d0c842421945/youtube_dl/YoutubeDL.py#L137-L312

logName = "Downloader.log"
all_settings_dir = "Settings"
setting_file = "settings.yml"
app = Flask(__name__)
dm: DownloaderManager


def main():
	global logName, setting_file, all_settings_dir, dm
	logging.basicConfig(
		filename=create_absolute_path(logName),
		level=logging.ERROR,
		format='%(asctime)s %(levelname)-8s %(message)s')
	setting_path = Configuration.create_absolute_path(os.path.join(all_settings_dir, setting_file))
	config_class = Configuration(setting_path, logging)

	print("Starting...")
	dm = DownloaderManager(config_class, logging)

	if config_class.get_config('GlobalSettings', 'commandLineEnabled'):
		logging.debug("Retrieving files from command line")
		parameters = retrieve_command_line_parameters()
		for url in parameters['url']:
			dm.request_download(url)
	else:
		logging.debug("Command line disabled, settings value: " + str(config_class.get_config('GlobalSettings', 'commandLineEnabled')))

	dm.start()
	app.jinja_env.globals.update(get_urls=get_urls)
	app.run(port=5081, host='0.0.0.0', debug=True, use_reloader=False)
	dm.join()
	print("Download Manager has stopped working - Killing process")
	logging.error("Download Manager has stopped working - Killing process")
	exit(1)


def retrieve_command_line_parameters():
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


def create_absolute_path(path):
	# Check if the given path is an absolute path
	if not os.path.isabs(path):
		current_dir = os.path.dirname(os.path.realpath(__file__))
		path = os.path.join(current_dir, path)

	return path


def get_urls():
	return dm.get_queue()


@app.route("/add", methods=['POST'])
def test1():
	new_url = request.form.get('new_url')
	dm.request_download(new_url)
	print("Added new url [" + new_url + "]")
	return escape("Added new url [" + new_url + "]")


@app.route("/add", methods=['GET'])
def add_url_interface():
	return render_template('base.html')


if __name__ == "__main__":
	main()
