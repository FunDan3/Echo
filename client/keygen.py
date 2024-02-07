#! /usr/bin/python3

import EchoAPI
import multiprocessing as mp
import os
import pickle
import hashlib
import base64
import colorama
import time

colorama.init()
key_start = input("How do you want to start your verification hash: ")
time_started = time.time()
hashed = 0
cpu_count = mp.cpu_count()

def gencrypto(core):
	global hashed
	client = EchoAPI.client("")
	while not os.path.exists("./cryptodata.pickle"):
		public_key, private_key, public_sign, private_sign = client.generate_cryptodata()
		verification_hash = hashlib.new("md5")
		verification_hash.update(public_key)
		verification_hash.update(public_sign)
		hash = base64.b64encode(verification_hash.digest()).decode("utf-8").replace("=", "")
		hashed += 1
		if hashed % 5000 == 0 and core == 0:
			print(f"{round(hashed/(time.time()-time_started)*cpu_count/1000, 1)} kH/S")
		if hash.startswith(key_start):
			with open("./cryptodata.pickle", "wb") as f:
				f.write(pickle.dumps((public_key, private_key, public_sign, private_sign)))
			break

processes = []
for core in range(0, cpu_count):
	processes.append(mp.Process(target = gencrypto, args = [core]))
for process in processes:
	process.start()
for process in processes:
	process.join()
