#! /usr/bin/python3
# Script used for creating updates for Echo messager. Uses unsafe pickle however if malicious actor gets access to the update server you are going to get hacked anyways

import pickle
import hashlib
import os
import platform

def hash_path(path, local_path = None):
	if not local_path:
		local_path = "./"
	def hash(data):
		data_hash = hashlib.new("sha256")
		data_hash.update(data)
		return data_hash.digest()
	if os.path.isdir(path):
		hashed_data = {}
		path = path + ("/" if not path.endswith("/") else "")
		local_path = local_path + ("/" if not local_path.endswith("/") else "")
		for file in os.listdir(path):
			if file == "update":
				continue
			file_local_path = local_path+file
			file_path = path+file
			hashed_data[file_local_path] = hash_path(file_path, local_path = local_path + file)
		return hashed_data
	else:
		with open(path, "rb") as f:
			return hash(f.read())

def find_deleted_files(old_path_hash, new_path_hash):
	to_remove = []
	for path, data in old_path_hash.items():
		if type(data) == bytes:
			if path not in new_path_hash:
				to_remove.append(path)
		else:
			if path in new_path_hash:
				to_remove += find_deleted_files(old_path_hash[path], new_path_hash[path])
			else:
				to_remove.append(path)
	return to_remove

def find_changed_files(old_path_hash, new_path_hash):
	changed_files = []
	for path, data in old_path_hash.items():
		if type(data) == bytes:
			if path in new_path_hash:
				if data != new_path_hash[path]:
					changed_files.append(path)
		else:
			if path in new_path_hash:
				changed_files += find_changed_files(old_path_hash[path], new_path_hash[path])
	return changed_files

def find_new_files(old_path_hash, new_path_hash):
	new_files = []
	for path, data in new_path_hash.items():
		if type(data) == bytes:
			if path not in old_path_hash:
				new_files.append(path)
		else:
			if path in old_path_hash:
				new_files += find_new_files(old_path_hash[path], new_path_hash[path])
			else:
				new_files += find_new_files({}, new_path_hash[path])
	return new_files

def read_files(files):
	data = {}
	for file in files:
		with open(file, "rb") as f:
			data[file.replace("./new_release/", "./")] = f.read()
	return data

def create_update_package(scripts, update_files, to_remove, to_write):
	update_dict = {"scripts": scripts, "update_files": update_files, "to_remove": to_remove, "to_write": to_write}
	return pickle.dumps(update_dict)

def read_scripts():
	scripts = {}
	scripts_names = os.listdir("./scripts/")
	for script_name in scripts_names:
		script_path = f"./scripts/{script_name}"
		script_name = os.path.splitext(script_name)[0]
		with open(script_path, "r") as f:
			scripts[script_name] = f.read()
	return scripts

def GetFilename(program_version):
        bits = platform.architecture()[0]
        os = platform.system()
        if os == "Windows":
                os += platform.release()
        return f"EchoUpdate{os}{bits}-{program_version}.update"

def main(old_build_path, new_build_path):
	old_build_path = old_build_path + ("/" if not old_build_path.endswith("/") else "")
	new_build_path = new_build_path + ("/" if not new_build_path.endswith("/") else "")

	old_file_hashes = hash_path(old_build_path)
	new_file_hashes = hash_path(new_build_path)

	to_remove = find_deleted_files(old_file_hashes, new_file_hashes)
	to_write = find_changed_files(old_file_hashes, new_file_hashes) + find_new_files(old_file_hashes, new_file_hashes)
	global_to_write = [file_path.replace("./", "./new_release/") for file_path in to_write]

	[print(f"removed {file}") for file in to_remove]
	[print(f"written {file}") for file in to_write]

	update_files = read_files(global_to_write)
	scripts = read_scripts()
	previous_version = input("Previous version: ")
	update_package = create_update_package(scripts, update_files, to_remove, to_write)
	print(f"update size: {len(update_package)/1000} kilobytes")
	with open(f"{GetFilename(previous_version)}", "wb") as f:
		f.write(update_package)

main("./old_release/", "./new_release/")

