#!/usr/bin/env python3
# from __future__ import unicode_literals
import getopt
import logging
import os
import sys
import youtube_dl

from CruncyrollDownloader import CrunchyrollDownloader

# Details on parameters here:
#   https://github.com/ytdl-org/youtube-dl/blob/3e4cedf9e8cd3157df2457df7274d0c842421945/youtube_dl/YoutubeDL.py#L137-L312

logName = "Downloader.log"


def main():
	global logName
	logging.basicConfig(filename=create_absolute_path(logName), level=logging.ERROR, format='%(asctime)s %(levelname)-8s '
																					'%(message)s')
	logging.getLogger().setLevel('INFO')
	url = []
	output_dir = os.getcwd()
	print("START")
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
			output_dir = arg
		elif opt in ('-u', 'url'):
			print("Option: Adding url to list: " + arg)
			url.append(arg)
	for arg in args:
		print("parameter: Adding url to list: " + arg)
		url.append(arg)
	for u in url:
		download(u, output_dir)
	print("Downloaded ", len(url), " urls")


def youtube_download(url, output_dir):
	ydl_opts = {'outtmpl': output_dir + '/%(title)s.%(ext)s'}
	with youtube_dl.YoutubeDL(ydl_opts) as ydl:
		print("Downloading: " + url)
		ydl.download([url])
		print("Done!")


def download(url, output_dir):
	if 'youtube.com' in url:
		youtube_download(url, output_dir)
	elif 'crunchyroll.com' in url:
		cr = CrunchyrollDownloader(output_dir, logging)
		cr.request_download(url)
		cr.start_download()
	else:
		print("Unsupported provider: [", url, "]")


def create_absolute_path(path):
	# Check if the given path is an absolute path
	if not os.path.isabs(path):
		current_dir = os.path.dirname(os.path.realpath(__file__))
		path = os.path.join(current_dir, path)

	return path


if __name__ == "__main__":
	main()
