# -*- coding: utf8 -*-
from Crypto.Cipher import AES
from Crypto.Hash import SHA256
from os import urandom
import base64

#****************************************************************************************
# Class providing AES-128 CBC with PKCS7 padding cryptographic operations
#****************************************************************************************
class Crypto(object):

	#-----------------------------------------------------------
 	@classmethod
	def createKey(cls, outputFormat = "raw"):
		if outputFormat == "raw":
			return urandom(16) # 128bits AES is an agreed trade off between security and performances
		else:
			return base64.b64encode(urandom(16))

	#-----------------------------------------------------------
	@classmethod
	def encryptData(cls, clearText, key):
		"""Encrypts data with the provided key.
		The returned byte array is as follow:
		:==============:==================================================:
		: IV (16bytes) :    Encrypted (data + PKCS7 padding information)  :
		:==============:==================================================:
		"""

		# Generate a crypto secure random Initialization Vector
		iv = urandom(AES.block_size)

		# Perform PKCS7 padding so that clearText is a multiple of the block size
		clearText = cls.pad(clearText)

		cipher = AES.new(key, AES.MODE_CBC, iv)
		return iv + cipher.encrypt(clearText)

    #-----------------------------------------------------------
	@classmethod
	def decryptData(cls, cipherText, key):
		"""Decrypt data with the provided key"""

		# Initialization Vector is in the first 16 bytes
		iv = cipherText[:AES.block_size]

		cipher = AES.new(key, AES.MODE_CBC, iv)
		return cls.unpad(cipher.decrypt(cipherText[AES.block_size:]))

	#------------------------------------------------------------------------
	@classmethod
	def xor(cls, data, key):
		l = len(key)
		keyAsInt = map(ord, key)
		return bytes(bytearray((
		    (data[i] ^ keyAsInt[i % l]) for i in range(0,len(data))
		)))
    
	#------------------------------------------------------------------------
	@classmethod
	def convertKey(cls, key, outputFormat = "raw"):
		if outputFormat == "raw":
			return base64.b64decode(key)
		elif outputFormat == "sha256":
			return SHA256.new(key).hexdigest()
		else:
			return base64.b64encode(key)
			

	#------------------------------------------------------------------------
	@classmethod
	def pad(cls, s):
		"""PKCS7 padding"""
		return s + (AES.block_size - len(s) % AES.block_size) * chr(AES.block_size - len(s) % AES.block_size)

	#------------------------------------------------------------------------
	@classmethod
	def unpad(cls, s):
		"""PKCS7 padding removal"""
		return s[:-ord(s[len(s)-1:])]
