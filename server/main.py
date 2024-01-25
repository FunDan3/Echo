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

config = DictLayer("./storage/config.json", template = {"Host": "", "Port": 8080})
user_data = DictLayer("./storage/users/user_data.json", template = {"last_uid": 0, "tokens": {}}, autosave = True)
BannerContent = ReadFile("./banner.txt")


api = WebServer(config["Host"], config["Port"])

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
	if not os.path.exists(f"./storage/users/{interface.data['username']}/"):
		interface.write("This user does not exist")
		interface.header("Content-Type", "text/plain")
		interface.finish(401)
		return
	if not check_if_string_only_contains_allowed_characters(interface.data["username"]):
		interface.write("Username contains invalid characters")
		interface.header("Content-Type", "text/plain")
		interface.finish(401)
		return
	interface.write(ReadFile(f"./storage/users/{interface.data['username']}/public.key", bytes = True))
	interface.finish(200)

@api.get(["/public_sign"])
def send_public_key(interface):
	if not interface.verify(["username"]):
		interface.write("Invalid request. Expected fields: 'username'")
		interface.header("Content-Type", "text/plain")
		interface.finish(400)
		return
	if not os.path.exists(f"./storage/users/{interface.data['username']}/"):
		interface.write("This user does not exist")
		interface.header("Content-Type", "text/plain")
		interface.finish(401)
		return
	if not check_if_string_only_contains_allowed_characters(interface.data["username"]):
		interface.write("Username contains invalid characters")
		interface.header("Content-Type", "text/plain")
		interface.finish(401)
		return
	interface.write(ReadFile(f"./storage/users/{interface.data['username']}/public.sign", bytes = True))
	interface.finish(200)


@api.post("/login")
def login_check(interface):
	interface.jsonize()
	if not interface.verify(["login", "token"]):
		interface.write("Invalid request. Expected fields: 'login', 'token'")
		interface.header("Content-Type", "text/plain")
		interface.finish(400)
		return
	if not os.path.exists(f"./storage/users/{interface.data['login']}/"):
		interface.write("No such user")
		interface.header("Content-Type", "text/plain")
		interface.finish(401)
		return
	if interface.data["login"] not in user_data["tokens"]:
		user_data["tokens"][interface.data['login']] = DictLayer(f"./storage/users/{interface.data['login']}/data.json", autowrite = False)["token"]
	if interface.data["token"] == user_data["tokens"][interface.data["login"]]: #TODO: safe compation
		interface.write("Success")
		interface.header("Content-Type", "text/plain")
		interface.finish(200)
		user_config = DictLayer(f"./storage/users/{interface.data['login']}/data.json", autowrite = False)
		if interface.client_address.ip not in user_config["IpList"]:
			user_config["IpList"] = user_config["IpList"] + [interface.client_address.ip] #yes, I had a bad time dealing with dicts some time ago
		user_config["LastLogin"] = time.time()
		user_config.save()
		return
	else:
		interface.write("Invalid token")
		interface.header("Content-Type", "text/plain")
		interface.finish(401)
		return
@api.post(["/register"])
def register(interface):
	interface.jsonize()
	if not interface.verify(["login", "password", "public_key", "public_sign"]):
		interface.write("Invalid request. Expected fields: 'login', 'password', 'public_key', 'public_sign'")
		interface.header("Content-Type", "text/plain")
		interface.finish(400)
		return
	if not check_if_string_only_contains_allowed_characters(interface.data["login"]):
		interface.write("You can only use letters, nubmbers and underscore for your nickname")
		interface.header("Content-Type", "text/plain")
		interface.finish(401)
		return
	if os.path.exists(f"./storage/users/{interface.data['login']}/"):
		interface.write("User with that nickname already exists")
		interface.header("Content-Type", "text/plain")
		interface.finish(401)
		return
	token = hashlib.sha512()
	token.update(f"{interface.data['login']}{interface.data['password']}{user_data['last_uid']}{time.time()}".encode("utf-8"))
	token = token.hexdigest()
	user_config = DictLayer(f"./storage/users/{interface.data['login']}/data.json", template = {"LastLogin": time.time(), "IpList": [interface.client_address.ip], "token": token, "uid": user_data["last_uid"], "PublicMetadata": {}})
	user_config.save()
	WriteFile(f"./storage/users/{interface.data['login']}/public.key", numbers_to_bytes(interface.data["public_key"]))
	WriteFile(f"./storage/users/{interface.data['login']}/public.sign", numbers_to_bytes(interface.data["public_key"]))
	user_data["tokens"][interface.data["login"]] = token
	user_data["last_uid"] = user_data["last_uid"] + 1
	interface.write(token)
	interface.finish(200)
api.start()
