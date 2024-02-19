#! /usr/bin/python3
# Main server file

from httpdecolib import WebServer
from configlib import DictLayer
import hashlib
import os
import time
import json
import oqs

allowed_characters = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890_"

def delete_r(path):
	if os.path.isdir(path):
		path = path + ("/" if not path.endswith("/") else "")
		files = os.listdir(path)
		for file in files:
			delete_r(path + file)
		os.rmdir(path)
	else:
		os.remove(path)
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
	token_hash = hashlib.sha512()
	token_hash.update(f"{interface.json['login']}{interface.json['token']}".encode("utf-8"))
	token_hash = token_hash.hexdigest()
	if token_hash == user_data["token_hashes"][interface.json["login"]]: #it is probably safe...
		return True
	else:
		interface.write("Invalid token")
		interface.header("Content-Type", "text/plain")
		interface.finish(401)
		return

def get_min_time_key(message_dict):
	return_value = ("", 9999999999999999999999999999999999)
	for message_key in message_dict.keys():
		if message_dict[message_key]["time"] < return_value[1]:
			return_value = (message_key, message_dict[message_key]["time"])
	return return_value[0]

config = DictLayer("./storage/config.json", template = {"Host": "", "Port": 22389, "CertificatePath": "", "KeyPath": ""})
user_data = DictLayer("./storage/users/user_data.json", template = {"token_hashes": {}})
if os.path.exists("./banner.txt"):
	BannerContent = ReadFile("./banner.txt")
else:
	BannerContent = "Unconfigured server"

api = WebServer(config["Host"], config["Port"])

@api.post("/set_description")
def set_user_description(interface):
	interface.jsonize()
	if not interface.verify(["login", "token", "description"]):
		interface.write("Invalid request. Expected fields: 'login', 'token', 'description'")
		interface.header("Content-Type", "text/plain")
		interface.finish(400)
		return
	if not verify_login(interface):
		return
	if len(interface.json["description"])>256:
		interface.write("Description can be at max 256 characters")
		interface.header("Content-Type", "text/plain")
		interface.finish(401)
		return
	user_config = DictLayer(f"./storage/users/{interface.json['login']}/data.json", autowrite = False)
	user_config["Description"] = interface.json["description"]
	user_config.save()
	interface.finish(200)

@api.get("/read_description")
def read_user_description(interface):
	if not interface.verify(["username"]):
		interface.write("Invalid request. Expected fields: 'username'")
		interface.header("Content-Type", "text/plain")
		interface.finish(400)
		return
	user_config = DictLayer(f"./storage/users/{interface.json['username']}/data.json", autowrite = False)
	interface.write(user_config["Description"])
	interface.header("Content-Type", "text/plain")
	interface.finish(200)

@api.get("/echo-messager-server-info")
def send_server_info(interface):
	return_data = {"version": "0.0.2",
	"flavour": "vanilla"}
	interface.write(json.dumps(return_data))
	interface.header("Content-Type", "text/json")
	interface.finish(200)

@api.post("/fetch_message")
def fetch_message(interface):
	def sort_key(item):
		return item["time"]
	interface.jsonize()
	if not interface.verify(["login", "token"]):
		interface.write("Invalid request. Expected fields: 'login', 'token'")
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

@api.get(["/algorithms"])
def send_algorithms(interface):
	if not interface.verify(["username"]):
		interface.write("Invalid request. Expected fields: 'username'")
		interface.header("Content-Type", "text/plain")
		interface.finish(400)
		return
	if not check_if_string_only_contains_allowed_characters(interface.json["username"]):
		interface.write("Username contains invalid characters")
		interface.header("Content-Type", "text/plain")
		interface.finish(401)
		return
	if not os.path.exists(f"./storage/users/{interface.json['username']}/data.json"):
		interface.write("This user does not exist")
		interface.header("Content-Type", "text/plain")
		interface.finish(401)
		return
	user_config = DictLayer(f"./storage/users/{interface.json['username']}/data.json", autowrite = False)
	interface.write(json.dumps({"kem_algorithm": user_config["kem_algorithm"], "sig_algorithm": user_config["sig_algorithm"]}))
	interface.finish(200)

@api.get(["/public_key"])
def send_public_key(interface):
	if not interface.verify(["username"]):
		interface.write("Invalid request. Expected fields: 'username'")
		interface.header("Content-Type", "text/plain")
		interface.finish(400)
		return
	if not check_if_string_only_contains_allowed_characters(interface.json["username"]):
		interface.write("Username contains invalid characters")
		interface.header("Content-Type", "text/plain")
		interface.finish(401)
		return
	if not os.path.exists(f"./storage/users/{interface.json['username']}/public.key"):
		interface.write("This user does not exist")
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
	if not os.path.exists(f"./storage/users/{interface.json['username']}/public.sign"):
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

@api.post(["/delete"])
def delete_user(interface):
	interface.jsonize()
	if not interface.verify(["login", "token"]):
		interface.write("Invalid request. Expected fields: 'login', 'token'")
		interface.header("Content-Type", "text/plain")
		interface.finish(400)
		return
	if not verify_login(interface):
		return
	delete_r(f"./storage/users/{interface.json['login']}/")
	del user_data["token_hashes"][interface.json["login"]]
	user_data.save()
	interface.finish(200)

@api.post(["/register"])
def register(interface):
	interface.jsonize()
	if not interface.verify(["login", "token", "public_key", "public_sign", "kem_algorithm", "sig_algorithm"]):
		interface.write("Invalid request. Expected fields: 'login', 'token', 'public_key', 'public_sign', 'kem_algorithm', 'sig_algorithm'")
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
	if len(interface.json["token"])<8 or len(interface.json["token"])>32:
		interface.write("token is expected to be from 8 to 32 bytes long.")
		interface.header("Content-Type", "text/plain")
		interface.finish(401)
		return
	if interface.json["kem_algorithm"] not in oqs.get_enabled_kem_mechanisms():
		interface.write(f"Server does not know {interface.json['kem_algorithm']}. Make sure that this encryption algorithm exists. If it does then server is outdated")
		interface.header("Content-Type", "text/plain")
		interface.finish(401)
		return
	if interface.json["sig_algorithm"] not in oqs.get_enabled_sig_mechanisms():
		interface.write(f"Server does not know {interface.json['sig_algorithm']}. Make sure that this signing algorithm exists. If it does then server is outdated")
		interface.header("Content-Type", "text/plain")
		interface.finish(401)
		return
	with oqs.KeyEncapsulation(interface.json["kem_algorithm"]) as encryption:
		key_size = encryption.details["length_public_key"]
	with oqs.Signature(interface.json["sig_algorithm"]) as signing:
		sign_size = signing.details["length_public_key"]
	if len(interface.json["public_key"])!=key_size:
		interface.write(f"Public key is expected to {key_size} bytes long.")
		interface.header("Content-Type", "text/plain")
		interface.finish(401)
		return
	if len(interface.json["public_sign"])!=sign_size:
		interface.write(f"Public sign is expected to be {sig_size} bytes long.")
		interface.header("Content-Type", "text/plain")
		interface.finish(401)
		return
	if os.path.exists(f"./storage/users/{interface.json['login']}/"):
		interface.write("User with that nickname already exists")
		interface.header("Content-Type", "text/plain")
		interface.finish(401)
		return
	token_hash = hashlib.sha512()
	token_hash.update(f"{interface.json['login']}{interface.json['token']}".encode("utf-8"))
	token_hash = token_hash.hexdigest()
	user_config = DictLayer(f"./storage/users/{interface.json['login']}/data.json",
				template = {"LastLogin": time.time(),
					"IpList": [interface.client_address.ip],
					"kem_algorithm": interface.json["kem_algorithm"],
					"sig_algorithm": interface.json["sig_algorithm"],
					"DataSent": 0,
					"Description": ""})
	user_config.save()
	message_config = DictLayer(f"./storage/users/{interface.json['login']}/inbox/messages.json", template = {"LastMID": 0, "MessagesMetadata": {}})
	message_config.save()
	WriteFile(f"./storage/users/{interface.json['login']}/public.key", numbers_to_bytes(interface.json["public_key"]))
	WriteFile(f"./storage/users/{interface.json['login']}/public.sign", numbers_to_bytes(interface.json["public_sign"]))
	user_data["token_hashes"][interface.json["login"]] = token_hash
	user_data.save()
	interface.finish(200)
if config["CertificatePath"] and config["KeyPath"]:
	api.convert_to_ssl(config["CertificatePath"], config["KeyPath"])
api.start()
