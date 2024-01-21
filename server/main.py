#! /usr/bin/python3
# Main server file

from httpdecolib import WebServer
from configlib import DictLayer
import hashlib

def ReadFile(filename, bytes = False):
	mode = "r" + ("b" if bytes else "")
	with open(filename, mode) as f:
		return f.read()

config = DictLayer("./storage/config.json", template = {"Host": "", "Port": 8080, "LastUID": 0})
BannerContent = ReadFile("./banner.txt")


api = WebServer(config["Host"], config["Port"])

@api.get(["/banner.txt"])
def banner(interface):
	interface.header("Content-Type", "text/plain")
	interface.write(BannerContent)
	interface.finish(200)

api.start()
