#! /usr/bin/python3
# Script used for creating updates for Echo messager. Uses unsafe pickle however if malicious actor gets access to the update server you are going to get hacked anyways

import pickle
import hashlib
import os

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
				new_files.append(path)
	return new_files

def generate_script(to_remove, to_write):
	script=f"""import os
def remove(path):
	if os.path.isdir(path):
		path = path + ("/" if not path.endswith("/")) else ""
		for file in os.listdir(path):
			file_path = path+file
			remove(file_path)
		os.rmdir(path)
	else:
		os.remove(path)
	print("removed " + path)

def write(path, data):
	with open(path, "wb") as f:
		f.write(data)
	print("written " + data)

[remove(path) for path in {to_remove}]
[write(path, update_files[path]) for path in {to_write}]"""
	return script

def main(old_build_path, new_build_path):
	old_build_path = old_build_path + ("/" if not old_build_path.endswith("/") else "")
	new_build_path = new_build_path + ("/" if not new_build_path.endswith("/") else "")

	old_file_hashes = hash_path(old_build_path)
	new_file_hashes = hash_path(new_build_path)

	to_remove = find_deleted_files(old_file_hashes, new_file_hashes)
	to_write = find_changed_files(old_file_hashes, new_file_hashes) + find_new_files(old_file_hashes, new_file_hashes)

	script = generate_script(to_remove, to_write)

main("./old_release/", "./new_release/")
