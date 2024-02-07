# This file provides layer for easy post quantum cipher and signs

import SymetricEncryptionLayer as aes
import oqs

kem_algorithm = "Kyber512" # I have tried to reasearch what algoritms are good but I am too dumb to comperhend the papers so it is default one
sig_algorithm = "Dilithium5" # Probably good. I dont think that signing is as important as encryption

class encryption:
	def generate_keypair():
		with oqs.KeyEncapsulation(kem_algorithm) as encryptor:
			public_key, private_key = encryptor.generate_keypair(), encryptor.export_secret_key()
		return public_key, private_key
	def encrypt(public_key, plaintext):
		with oqs.KeyEncapsulation(kem_algorithm) as encryptor:
			encrypted_key, plain_key = encryptor.encap_secret(public_key)
		ciphertext = aes.encrypt(plain_key, plaintext)
		return encrypted_key+ciphertext
	def decrypt(private_key, ciphertext):
		encrypted_key = ciphertext[:768]
		ciphertext = ciphertext[768:]
		with oqs.KeyEncapsulation(kem_algorithm, private_key) as encryptor:
			plain_key = encryptor.decap_secret(encrypted_key)
		return aes.decrypt(plain_key, ciphertext)

class signing:
	def generate_signs():
		with oqs.Signature(sig_algorithm) as signer:
			public_sign, private_sign = signer.generate_keypair(), signer.export_secret_key()
		return public_sign, private_sign
	def sign(private_sign, message):
		with oqs.Signature(sig_algorithm, private_sign) as signer:
			signature = signer.sign(message)
		print(len(signature))
		return signature+message
	def verify(public_sign, message):
		signature = message[:4595]
		message = message[4595:]
		with oqs.Signature(sig_algorithm) as signer:
			assert signer.verify(message, signature, public_sign)
		return message
