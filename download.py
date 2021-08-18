#!/usr/bin/env python3
#from __future__ import unicode_literals
import sys, getopt, os
import youtube_dl

##Details on paramters here: https://github.com/ytdl-org/youtube-dl/blob/3e4cedf9e8cd3157df2457df7274d0c842421945/youtube_dl/YoutubeDL.py#L137-L312

def main():
	url = []
	output_dir = os.getcwd()
	print("START")
	try:
		opts, args = getopt.getopt(sys.argv[1:],"hu:o:",["url=","output="])
	except getopt.GetoptError:
		print ('download.py -u <urlToDownload> -o <outputfile>')
		sys.exit(2)
	for opt, arg in opts:
		if opt == '-h':
			print ('download.py -u <urlToDownload> -o <outputfile>')
			sys.exit(2)
		elif opt in ('-o', 'output'):
			print("Option: Writing output in: "+arg)
			output_dir = arg
		elif opt in ('-u', 'url'):
			print("Option: Adding url to list: "+arg)
			url.append(arg)
	for arg in args:
		print("parameter: Adding url to list: "+arg)
		url.append(arg)
	for u in url:
		download(u, output_dir)
	print("Downloaded ", len(url), " urls")

def youtubeDownload(url, output_dir):
	ydl_opts = {'outtmpl': output_dir + '/%(title)s.%(ext)s'}
	with youtube_dl.YoutubeDL(ydl_opts) as ydl:
		print("Downloading: " + url)
		ydl.download([url])
		print("Done!")

#TODO Subtitle are not hard impressed
def crDownload(url, output_dir):
	ydl_opts = {
	#	'simulate': True,
	#	'listsubtitles': True,
		'outtmpl': output_dir + '/%(title)s.%(ext)s',
		'subtitleslangs': ['itIT'],
		'subtitlesformat': 'ass',
		'writesubtitles': True
	}
	with youtube_dl.YoutubeDL(ydl_opts) as ydl:
		print("Downloading: " + url)
		ydl.download([url])
		print("Done!")

def download(url, output_dir):
	if 'youtube.com' in url:
		youtubeDownload(url, output_dir)
	elif 'crunchyroll.com' in url:
		crDownload(url, output_dir)
	else:
		print("Unsupported provider: [", url, "]")


if __name__ == "__main__":
	main()
