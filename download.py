#!/usr/bin/env python3
from __future__ import annotations
import getopt
import logging
import os
import sys

# TODO Remove Locker or check if OS is Unix before requiring it
from IUBBaseTools import IUBConfiguration

from DownloaderManager import DownloaderManager
from flask import Flask, request, render_template, jsonify
from QueueManager import QueueManager

# Details on parameters here:
#   https://github.com/ytdl-org/youtube-dl/blob/3e4cedf9e8cd3157df2457df7274d0c842421945/youtube_dl/YoutubeDL.py#L137-L312

logName = "Downloader.log"
app = Flask(__name__)
dm: DownloaderManager


def create_absolute_path(path):
	"""
	Check if the given path is an absolute path
	:param path: The path to control
	:return: The absolute path
	"""
	if not os.path.isabs(path):
		currentDir = os.path.dirname(os.path.realpath(__file__))
		path = os.path.join(currentDir, path)
	return path


def main():
	global logName, dm
	logging.basicConfig(
		filename=create_absolute_path(logName),
		level=logging.ERROR,
		format='%(asctime)s %(levelname)-8s %(message)s')
	setting_path = create_absolute_path(os.path.join(DownloaderManager.all_settings_dir, DownloaderManager.setting_file))
	config_class = IUBConfiguration(setting_path, logging)

	print("Starting...")
	dm = DownloaderManager(config_class, logging)
	dm.loadHistory()

	if config_class.get_config('GlobalSettings', 'commandLineEnabled'):
		logging.debug("Retrieving files from command line")
		parameters = retrieve_command_line_parameters()
		for url in parameters['url']:
			dm.request_download(url)
	else:
		logging.debug("Command line disabled, settings value: " + str(config_class.get_config('GlobalSettings', 'commandLineEnabled')))

	logging.debug("Starting downloader routine")
	dm.start()
	port = config_class.get_config('GlobalSettings', 'port')
	try:
		logging.debug("Starting service on port: " + str(port))
		app.jinja_env.globals.update(get_urls=get_urls)
		app.run(port=port, host='0.0.0.0', debug=True, use_reloader=False)
		dm.join()
		dm.saveHistory()
		print("Download Manager has stopped working - Killing process")
		logging.error("Download Manager has stopped working - Killing process")
	except OSError as err:
		logging.error("Cannot start service on port " + str(port) + " - EXIT")
		print("Cannot start service on port " + str(port) + " - EXIT")
		raise err
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


def get_urls():
	return dm.get_queue()


@app.route("/add", methods=['POST'])
def test1():
	new_url = request.form.get('new_url')
	dm.request_download(new_url)
	print("Added new url [" + new_url + "]")
	return render_template('base.html')
	#return escape("Added new url [" + new_url + "]")


@app.route("/add", methods=['GET'])
def add_url_interface():
	return render_template('base.html')


@app.route("/")
def test_home():
	return add_url_interface()


@app.route("/status", methods=['GET'])
def show_progress():
	urls = get_urls()
	logging.info("Getting download status")
	return jsonify(**urls)


@app.route("/supported_sites", methods=['GET'])
def show_supported_sites():
	urls = DownloaderManager.supportedHost
	return jsonify(urls)


@app.route("/stop", methods=['GET'])
def stop_download():
	#todo
	urls = DownloaderManager.supportedHost
	return jsonify(urls)


@app.route("/delete", methods=['POST'])
def delete_download():
	delete_url = request.json
	if dm.cancel_download(delete_url):
		return jsonify({"success": True, "url_deleted": delete_url})
	else:
		return jsonify({"success": False})


@app.route("/store", methods=['GET'])
def store_download():
	dm.saveHistory()
	return jsonify({"success": True})


@app.route("/restore", methods=['POST'])
def restore_download():
	restore_url = request.json
	if dm.restart_download(restore_url):
		return jsonify({"success": True, "url_restored": restore_url, "old_queue": QueueManager.DOWNLOAD_FAILED, "new_queue": QueueManager.DOWNLOAD_QUEUE})
	else:
		return jsonify({"success": False})


if __name__ == "__main__":
	main()
