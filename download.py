#!/usr/bin/env python3
#from __future__ import unicode_literals
import sys, getopt, os
import youtube_dl

def main():
	url = []
	outputDir = os.getcwd()
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
			outputDir = arg
		elif opt in ('-u', 'url'):
			print("Option: Adding url to list: "+arg)
			url.append(arg)
	for arg in args:
		print("parameter: Adding url to list: "+arg)
		url.append(arg)
	for u in url:
		download(u, outputDir)
	print("Downloaded ", len(url), " urls")


def download(url, outputDir):
	ydl_opts = {'outtmpl': outputDir+'/%(title)s.%(ext)s'}
	with youtube_dl.YoutubeDL(ydl_opts) as ydl:
		print("Downloading: "+url)
		ydl.download([url])
		print("Done!")

if __name__ == "__main__":
	main()
