# This file provides layer for easy post quantum cipher and signs

import SymetricEncryptionLayer as aes
import oqs

default_kem_algorithm = "Kyber1024" # I have tried to reasearch what algorithms are good but I am too dumb to comperhend the papers so it is default one with biggest number at the end LOL
default_sig_algorithm = "Dilithium5" # Probably good. I dont think that signing is as important as encryption

class encryption:
	def generate_keypair(algorithm = None):
		algorithm = default_kem_algorithm if not algorithm else algorithm
		with oqs.KeyEncapsulation(algorithm) as encryptor:
			public_key, private_key = encryptor.generate_keypair(), encryptor.export_secret_key()
		return public_key, private_key
	def encrypt(public_key, plaintext, algorithm = None):
		algorithm = default_kem_algorithm if not algorithm else algorithm
		with oqs.KeyEncapsulation(algorithm) as encryptor:
			encrypted_key, plain_key = encryptor.encap_secret(public_key)
		ciphertext = aes.encrypt(plain_key, plaintext)
		return encrypted_key+ciphertext
	def decrypt(private_key, ciphertext, algorithm = None):
		algorithm = default_kem_algorithm if not algorithm else algorithm
		with oqs.KeyEncapsulation(algorithm, private_key) as encryptor:
			encrypted_key_size = encryptor.details["length_ciphertext"]
			encrypted_key = ciphertext[:encrypted_key_size]
			ciphertext = ciphertext[encrypted_key_size:]
			plain_key = encryptor.decap_secret(encrypted_key)
		return aes.decrypt(plain_key, ciphertext)

class signing:
	def generate_signs(algorithm = None):
		algorithm = default_sig_algorithm if not algorithm else algorithm
		with oqs.Signature(algorithm) as signer:
			public_sign, private_sign = signer.generate_keypair(), signer.export_secret_key()
		return public_sign, private_sign
	def sign(private_sign, message, algorithm = None):
		algorithm = default_sig_algorithm if not algorithm else algorithm
		with oqs.Signature(algorithm, private_sign) as signer:
			signature = signer.sign(message)
		return signature+message
	def verify(public_sign, message, algorithm = None):
		algorithm = default_sig_algorithm if not algorithm else algorithm
		with oqs.Signature(algorithm) as signer:
			signature_size = signer.details["length_signature"]
			signature = message[:signature_size]
			message = message[signature_size:]
			assert signer.verify(message, signature, public_sign)
		return message
