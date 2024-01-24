# Because keys are bytes I need to transform them somehow to jsonifyable data type
# that is the purpose of that file

from pqcrypto.kem import mceliece8192128 as enc
from pqcrypto.sign import dilithium4 as sig
import SymetricEncryptionLayer as aes

def bytes_to_numbers(key):
	return [int(byte) for byte in key]

def numbers_to_bytes(numbers):
	return bytes(bytearray(numbers))


class encryption:
	def generate_keypair():
		public_key, private_key = enc.generate_keypair()
		return bytes_to_numbers(public_key), bytes_to_numbers(private_key)
	def encrypt(public_key, plaintext): #takes public key (in form of numbers), plaintext (bytes); returns symetric key(numbers), ciphertext(bytes)
		encrypted_key, plain_key = enc.encrypt(numbers_to_bytes(public_key))
		ciphertext = aes.encrypt(plain_key, plaintext)
		return encrypted_key+ciphertext
	def decrypt(private_key, ciphertext): #takes private key(numbers), ciphertext(bytes); returns plaintext(bytes)
		encrypted_key = ciphertext[:240]
		ciphertext = ciphertext[240:]
		plain_key = enc.decrypt(numbers_to_bytes(private_key), encrypted_key)
		return aes.decrypt(plain_key, ciphertext)
