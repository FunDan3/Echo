#! /usr/bin/python3
# Main server file

from httpdecolib import WebServer
from configlib import DictLayer
import hashlib
import os
import time
import json

allowed_characters = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890_"

def check_if_string_only_contains_allowed_characters(string_to_check):
	total_count = 0
	for allowed_character in allowed_characters:
		total_count += string_to_check.count(allowed_character)
	return total_count == len(string_to_check)

def ReadFile(filename, bytes = False):
	mode = "r" + ("b" if bytes else "")
	with open(filename, mode) as f:
		return f.read()

def WriteFile(filename, data):
	mode = "w" + ("b" if type(data)==bytes else "")
	with open(filename, mode) as f:
		f.write(data)

def numbers_to_bytes(numbers):
	return bytes(bytearray(numbers))

def verify_login(interface):
	if not interface.json["login"]:
		interface.write("Login field can not be empty")
		interface.header("Content-Type", "text/plain")
		interface.finish(401)
		return
	if not check_if_string_only_contains_allowed_characters(interface.json["login"]):
		interface.write("Login field can only contain letters, numbers and underscore")
		interface.header("Content-Type", "text/plain")
		interface.finish(401)
		return
	if not os.path.exists(f"./storage/users/{interface.json['login']}/"):
		interface.write("No such user")
		interface.header("Content-Type", "text/plain")
		interface.finish(401)
		return
	password_hash = hashlib.sha512()
	password_hash.update(f"{interface.json['login']}{interface.json['password']}".encode("utf-8"))
	password_hash = password_hash.hexdigest()
	if password_hash == user_data["password_hashes"][interface.json["login"]]: #it is probably safe...
		return True
	else:
		interface.write("Invalid password")
		interface.header("Content-Type", "text/plain")
		interface.finish(401)
		return

def get_min_time_key(message_dict):
	return_value = ("", 9999999999999999999999999999999999)
	for message_key in message_dict.keys():
		if message_dict[message_key]["time"] < return_value[1]:
			return_value = (message_key, message_dict[message_key]["time"])
	return return_value[0]

config = DictLayer("./storage/config.json", template = {"Host": "", "Port": 8080})
user_data = DictLayer("./storage/users/user_data.json", template = {"last_uid": 0, "password_hashes": {}})
BannerContent = ReadFile("./banner.txt")


api = WebServer(config["Host"], config["Port"])

@api.post("/fetch_message")
def fetch_message(interface):
	def sort_key(item):
		return item["time"]
	interface.jsonize()
	if not interface.verify(["login", "password"]):
		interface.write("Invalid request. Expected fields: 'login', 'password'")
		interface.header("Content-Type", "text/plain")
		interface.finish(400)
		return
	if not verify_login(interface):
		return
	message_config = DictLayer(f"./storage/users/{interface.json['login']}/inbox/messages.json", autowrite = False)
	first_timed_mid = get_min_time_key(message_config["MessagesMetadata"])
	if not message_config["MessagesMetadata"]:
		interface.finish(200)
		return
	interface.write(json.dumps(message_config["MessagesMetadata"][first_timed_mid])+"\n")
	with open(f"./storage/users/{interface.json['login']}/inbox/{first_timed_mid}.content", "rb") as f:
		interface.write(f.read())
	interface.finish(200)
	del message_config["MessagesMetadata"][first_timed_mid]
	if not message_config["MessagesMetadata"]: #if it is empty
		message_config["LastMID"] = 0
	message_config.save()
	os.remove(f"./storage/users/{interface.json['login']}/inbox/{first_timed_mid}.content")

@api.post("/message")
def message(interface):
	interface.jsonize()
	if not interface.verify(["login", "password", "recipient"]):
		interface.write("Invalid request. Expected fields: 'login', 'password', 'recipient'")
		interface.header("Content-Type", "text/plain")
		interface.finish(400)
		return
	if not verify_login(interface):
		return
	if not check_if_string_only_contains_allowed_characters(interface.json["recipient"]):
		interface.write("recipient may only contain letters, numbers and underscore")
		interface.header("Content-Type", "text/plain")
		interface.finish(401)
		return
	if not os.path.exists(f"./storage/users/{interface.json['recipient']}/"):
		interface.write("Invalid request. Expected fields: 'username'")
		interface.header("Content-Type", "text/plain")
		interface.finish(401)
		return
	message_config = DictLayer(f"./storage/users/{interface.json['recipient']}/inbox/messages.json", autowrite = False)
	WriteFile(f"./storage/users/{interface.json['recipient']}/inbox/{message_config['LastMID']}.content", interface.data)
	message_config["MessagesMetadata"][message_config["LastMID"]] = {"Sender": interface.json["login"], "time": time.time()}
	message_config["LastMID"] = message_config["LastMID"] + 1
	message_config.save()
	interface.finish(200)

@api.get(["/banner.txt"])
def banner(interface):
	interface.header("Content-Type", "text/plain")
	interface.write(BannerContent)
	interface.finish(200)

@api.get(["/public_key"])
def send_public_key(interface):
	if not interface.verify(["username"]):
		interface.write("Invalid request. Expected fields: 'username'")
		interface.header("Content-Type", "text/plain")
		interface.finish(400)
		return
	if not os.path.exists(f"./storage/users/{interface.json['username']}/"):
		interface.write("This user does not exist")
		interface.header("Content-Type", "text/plain")
		interface.finish(401)
		return
	if not check_if_string_only_contains_allowed_characters(interface.json["username"]):
		interface.write("Username contains invalid characters")
		interface.header("Content-Type", "text/plain")
		interface.finish(401)
		return
	interface.write(ReadFile(f"./storage/users/{interface.json['username']}/public.key", bytes = True))
	interface.finish(200)

@api.get(["/public_sign"])
def send_public_key(interface):
	if not interface.verify(["username"]):
		interface.write("Invalid request. Expected fields: 'username'")
		interface.header("Content-Type", "text/plain")
		interface.finish(400)
		return
	if not os.path.exists(f"./storage/users/{interface.json['username']}/"):
		interface.write("This user does not exist")
		interface.header("Content-Type", "text/plain")
		interface.finish(401)
		return
	if not check_if_string_only_contains_allowed_characters(interface.json["username"]):
		interface.write("Username contains invalid characters")
		interface.header("Content-Type", "text/plain")
		interface.finish(401)
		return
	interface.write(ReadFile(f"./storage/users/{interface.json['username']}/public.sign", bytes = True))
	interface.finish(200)


@api.post("/login")
def login_check(interface):
	interface.jsonize()
	if not interface.verify(["login", "password"]):
		interface.write("Invalid request. Expected fields: 'login', 'password'")
		interface.header("Content-Type", "text/plain")
		interface.finish(400)
		return
	if verify_login(interface):
		interface.write("Success")
		interface.header("Content-Type", "text/plain")
		interface.finish(200)
		user_config = DictLayer(f"./storage/users/{interface.json['login']}/data.json", autowrite = False)
		if interface.client_address.ip not in user_config["IpList"]:
			user_config["IpList"] = user_config["IpList"] + [interface.client_address.ip] #yes, I had a bad time dealing with dicts some time ago
		user_config["LastLogin"] = time.time()
		user_config.save()
		return
	else:
		return

@api.post(["/register"])
def register(interface):
	interface.jsonize()
	if not interface.verify(["login", "password", "public_key", "public_sign"]):
		interface.write("Invalid request. Expected fields: 'login', 'password', 'public_key', 'public_sign'")
		interface.header("Content-Type", "text/plain")
		interface.finish(400)
		return
	if not check_if_string_only_contains_allowed_characters(interface.json["login"]):
		interface.write("You can only use letters, nubmbers and underscore for your nickname")
		interface.header("Content-Type", "text/plain")
		interface.finish(401)
		return
	if len(interface.json["login"])<4 or len(interface.json["login"])>16:
		interface.write("Login is expected to be from 4 to 16 bytes long")
		interface.header("Content-Type", "text/plain")
		interface.finish(401)
		return
	if len(interface.json["password"])<8 or len(interface.json["password"])>32:
		interface.write("Password is expected to be from 8 to 32 bytes long.")
		interface.header("Content-Type", "text/plain")
		interface.finish(401)
		return
	if len(interface.json["public_key"])!=800:
		interface.write("Public key is expected to 800 bytes long.")
		interface.header("Content-Type", "text/plain")
		interface.finish(401)
		return
	if len(interface.json["public_sign"])!=2592:
		interface.write("Public sign is expected to be 2592 bytes long.")
		interface.header("Content-Type", "text/plain")
		interface.finish(401)
		return
	if os.path.exists(f"./storage/users/{interface.json['login']}/"):
		interface.write("User with that nickname already exists")
		interface.header("Content-Type", "text/plain")
		interface.finish(401)
		return
	password_hash = hashlib.sha512()
	password_hash.update(f"{interface.json['login']}{interface.json['password']}".encode("utf-8"))
	password_hash = password_hash.hexdigest()
	user_config = DictLayer(f"./storage/users/{interface.json['login']}/data.json", template = {"LastLogin": time.time(), "IpList": [interface.client_address.ip], "uid": user_data["last_uid"], "PublicMetadata": {}, "PrivateMetadata": {}, "DataSent": 0})
	user_config.save()
	message_config = DictLayer(f"./storage/users/{interface.json['login']}/inbox/messages.json", template = {"LastMID": 0, "MessagesMetadata": {}})
	message_config.save()
	WriteFile(f"./storage/users/{interface.json['login']}/public.key", numbers_to_bytes(interface.json["public_key"]))
	WriteFile(f"./storage/users/{interface.json['login']}/public.sign", numbers_to_bytes(interface.json["public_sign"]))
	user_data["password_hashes"][interface.json["login"]] = password_hash
	user_data["last_uid"] = user_data["last_uid"] + 1
	user_data.save()
	interface.finish(200)
api.start()
