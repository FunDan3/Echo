#! /usr/bin/python3

import EchoAPI
import multiprocessing as mp
import os
import pickle
import hashlib
import base64
import colorama

colorama.init()
key_start = input("How do you want to start your verification hash: ")

def gencrypto():
	client = EchoAPI.client("")
	while not os.path.exists("./cryptodata.pickle"):
		public_key, private_key, public_sign, private_sign = client.generate_cryptodata()
		verification_hash = hashlib.new("sha1")
		verification_hash.update(public_key)
		verification_hash.update(public_sign)
		hash = base64.b64encode(verification_hash.digest()).decode("utf-8")
		toprint = colorama.Fore.LIGHTGREEN_EX
		for i in range(len(key_start)):
			if hash[i] != key_start[i]:
				toprint += colorama.Fore.LIGHTRED_EX
				toprint += hash[i:]
				break
			toprint += hash[i]
		print(toprint+colorama.Style.RESET_ALL)
		if hash.startswith(key_start):
			with open("./cryptodata.pickle", "wb") as f:
				f.write(pickle.dumps((public_key, private_key, public_sign, private_sign)))
			break

processes = []
for core in range(0, mp.cpu_count()):
	processes.append(mp.Process(target = gencrypto))
for process in processes:
	process.start()
for process in processes:
	process.join()
