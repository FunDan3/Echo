#! /usr/bin/python3
# Main server file

from httpdecolib import WebServer
from configlib import DictLayer
import hashlib
import os
import time

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
	if not os.path.exists(f"./storage/users/{interface.json['login']}/"):
		interface.write("No such user")
		interface.header("Content-Type", "text/plain")
		interface.finish(401)
		return
	if not check_if_string_only_contains_allowed_characters(interface.json["login"]):
		interface.write("Login field can only contain letters, numbers and underscore")
		interface.header("Content-Type", "text/plain")
		interface.finish(401)
		return
	if interface.json["login"] not in user_data["tokens"]:
		user_data["tokens"][interface.json['login']] = DictLayer(f"./storage/users/{interface.json['login']}/data.json", autowrite = False)["token"]
	if interface.json["token"] == user_data["tokens"][interface.json["login"]]: #TODO: safe compation
		return True
	else:
		interface.write("Invalid token")
		interface.header("Content-Type", "text/plain")
		interface.finish(401)
		return

config = DictLayer("./storage/config.json", template = {"Host": "", "Port": 8080})
user_data = DictLayer("./storage/users/user_data.json", template = {"last_uid": 0, "tokens": {}}, autosave = True)
BannerContent = ReadFile("./banner.txt")


api = WebServer(config["Host"], config["Port"])


@api.post("/message")
def message(interface):
	interface.jsonize()
	if not interface.verify(["login", "token", "recipient"]):
		interface.write("Invalid request. Expected fields: 'login', 'token', 'recipient'")
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
	if not interface.verify(["login", "token"]):
		interface.write("Invalid request. Expected fields: 'login', 'token'")
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
	if os.path.exists(f"./storage/users/{interface.json['login']}/"):
		interface.write("User with that nickname already exists")
		interface.header("Content-Type", "text/plain")
		interface.finish(401)
		return
	token = hashlib.sha512()
	token.update(f"{interface.json['login']}{interface.json['password']}{user_data['last_uid']}{time.time()}".encode("utf-8"))
	token = token.hexdigest()
	user_config = DictLayer(f"./storage/users/{interface.json['login']}/data.json", template = {"LastLogin": time.time(), "IpList": [interface.client_address.ip], "token": token, "uid": user_data["last_uid"], "PublicMetadata": {}, "PrivateMetadata": {"DataSent": 0}})
	user_config.save()
	message_config = DictLayer(f"./storage/users/{interface.json['login']}/inbox/messages.json", template = {"LastMID": 0, "MessagesMetadata": {}})
	message_config.save()
	WriteFile(f"./storage/users/{interface.json['login']}/public.key", numbers_to_bytes(interface.json["public_key"]))
	WriteFile(f"./storage/users/{interface.json['login']}/public.sign", numbers_to_bytes(interface.json["public_key"]))
	user_data["tokens"][interface.json["login"]] = token
	user_data["last_uid"] = user_data["last_uid"] + 1
	interface.write(token)
	interface.finish(200)
api.start()
