# This file provides layer for easy post quantum cipher and signs

from pqcrypto.kem import mceliece8192128 as enc
from pqcrypto.sign import dilithium4 as sig
import SymetricEncryptionLayer as aes

class encryption:
	def generate_keypair():
		return enc.generate_keypair()
	def encrypt(public_key, plaintext):
		encrypted_key, plain_key = enc.encrypt(public_key)
		ciphertext = aes.encrypt(plain_key, plaintext)
		return encrypted_key+ciphertext
	def decrypt(private_key, ciphertext):
		encrypted_key = ciphertext[:240]
		ciphertext = ciphertext[240:]
		plain_key = enc.decrypt(private_key, encrypted_key)
		return aes.decrypt(plain_key, ciphertext)

class signing:
	def generate_signs():
		return sig.generate_keypair()
	def sign(private_sign, message):
		signature = sig.sign(private_sign, message)
		return signature+message
	def verify(public_sign, message):
		signature = message[:3366]
		message = message[3366:]
		assert sig.verify(public_sign, message, signature)
		return message

""" This code will be later used in main api. Currently it is unused.
def bytes_to_numbers(key):
	return [int(byte) for byte in key]

def numbers_to_bytes(numbers):
	return bytes(bytearray(numbers))
"""
