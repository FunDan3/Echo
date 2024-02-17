#! /usr/bin/python3
import update_executor
import requests
import platform
import json

with open("updater_config.json", "r") as f:
	settings = json.loads(f.read())
server = settings["server"]
program_version = settings["version"]

def GetFilename():
	bits = platform.architecture()[0]
	os = platform.system()
	if os == "Windows":
		os += platform.release()
	return f"EchoUpdate{os}{bits}-{program_version}.update"

def RequestUpdateData():
	try:
		url = f"https://{server}/EchoMessager/Updates/{GetFilename()}"
		print(f"Fetching update from {url}")
		response = requests.get(url)
		if response.status_code not in range(200, 300) and response.status_code!=404:
			raise Exception(f"Update failed with status code {response.status}")
		elif response.status_code == 404:
			raise Exception("No update found")
		return response.content
	except Exception as e:
		print(e)
		return None

def main():
	update = RequestUpdateData()
	if update:
		print("Updating...")
		update_executor.execute_update(update)
	else:
		print("Update failed")
if __name__ == "__main__":
	main()
