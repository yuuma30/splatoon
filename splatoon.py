#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function
from __future__ import division
from builtins import input
from builtins import zip
from builtins import str
from builtins import range
from past.utils import old_div
import os.path, argparse, sys
import requests, json, time, datetime, random, re
import msgpack, uuid
import iksm
from io import BytesIO
from operator import itemgetter
from distutils.version import StrictVersion
from subprocess import call

A_VERSION = "1.0.3"

try:
	config_file = open("config.txt", "r")
	config_data = json.load(config_file)
	config_file.close()
except (IOError, ValueError):
	print("Generating new config file.")
	config_data = {"api_key": "", "cookie": "", "user_lang": "", "session_token": ""}
	config_file = open("config.txt", "w")
	config_file.seek(0)
	config_file.write(json.dumps(config_data, indent=4, sort_keys=True, separators=(',', ': ')))
	config_file.close()
	config_file = open("config.txt", "r")
	config_data = json.load(config_file)
	config_file.close()

#########################
## API KEYS AND TOKENS ##
API_KEY       = config_data["api_key"] # for stat.ink
YOUR_COOKIE   = config_data["cookie"] # iksm_session
try: # support for pre-1.0.0 config.txts
	SESSION_TOKEN = config_data["session_token"] # to generate new cookies in the future
except:
	SESSION_TOKEN = ""
USER_LANG     = config_data["user_lang"] # only works with your game region's supported languages
#########################

debug = False # print out payload and exit. can use with geargrabber2.py & saving battle jsons

app_head = {
	'Host': 'app.splatoon2.nintendo.net',
	'x-unique-id': '32449507786579989234', # random 19-20 digit token. used for splatnet store
	'x-requested-with': 'XMLHttpRequest',
	'x-timezone-offset': '0',
	'User-Agent': 'Mozilla/5.0 (Linux; Android 7.1.2; Pixel Build/NJH47D; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/59.0.3071.125 Mobile Safari/537.36',
	'Accept': '*/*',
	'Referer': 'https://app.splatoon2.nintendo.net/home',
	'Accept-Encoding': 'gzip, deflate',
	'Accept-Language': USER_LANG
}

def write_config(tokens):
	'''Writes config file and updates the global variables.'''

	config_file = open("config.txt", "w")
	config_file.seek(0)
	config_file.write(json.dumps(tokens, indent=4, sort_keys=True, separators=(',', ': ')))
	config_file.close()

	config_file = open("config.txt", "r")
	config_data = json.load(config_file)

	global API_KEY
	API_KEY = config_data["api_key"]
	global SESSION_TOKEN
	SESSION_TOKEN = config_data["session_token"]
	global YOUR_COOKIE
	YOUR_COOKIE = config_data["cookie"]
	global USER_LANG
	USER_LANG = config_data["user_lang"]

	config_file.close()

def gen_new_cookie(reason):
	'''Attempts to generate new cookie in case provided one is invalid.'''

	manual = False

	if reason == "blank":
		print("Blank cookie.")
	elif reason == "auth":
		#authentication error
		print("The stored cookie has expired.")
	else:
		#server error or player hasn't battled before
		print("Cannnot access SplatNet 2 without having played at least one")
		exit(1)
	if SESSION_TOKEN == "":
		print("session_token is blank.Please log in to your Nintendo Account")
		new_token = iksm.log_in(A_VERSION)
		if new_token == None:
			print("There was a problem logging you in. Please try again later")
		else:
			if new_token == "skip":
				#user has opted to manually enter cookie
				manual = True
				print("\nYou have opted against automatic cookie generation\n")
			else:
				print("\nWrote session_token to config.txt.")
			config_data["session_token"] = new_token
			write_config(config_data)
	elif SESSION_TOKEN == "skip":
		manual = True
		print("\nYOu have opted against automatic")

	if manual:
		new_cookie = iksm.enter_cookie()
	else:
		new_cookie = iksm.get_cookie(SESSION_TOKEN, USER_LANG, A_VERSION)
	config_data["cookie"] = new_cookie
	write_config(config_data)
	print("Wrote iksm_session cookie to config.txt.")



def load_json(bool):
	'''Returns results JSON from online. '''

	if bool:
		print("Pulling data from online...") #grab dfata from SplatNet 2
	url = "https://app.splatoon2.nintendo.net/api/results"
	results_list = requests.get(url, headers=app_head, cookies=dict(iksm_session=YOUR_COOKIE))
	return json.loads(results_list.text)

def set_gender():
	'''Sets the global gender variable.'''
	try:
		url = "https://app.splatoon2.nintendo.net/api/records"
		records = requests.get(url, headers=app_head, cookies=dict(iksm_session=YOUR_COOKIE))
		global gender
		gender = json.loads(records.text)["records"]["player"]["player_type"]["key"]
	except:
		pass

def get_num_battles():
	'''Returns number of battles to upload along with results json.'''

	while True:
		data = load_json(True)

		try:
			results = data["results"]
			# print(results)
		except KeyError: # either auth error json (online) or battle json (local file)
			if YOUR_COOKIE == "":
				reason = "blank"
			elif data["code"] == "AUTHENTICATION_ERROR":
				reason = "auth"
			else:
				reason = "other"
			gen_new_cookie(reason)
			continue
		set_gender()
		return results

if __name__ == "__main__":
	results = get_num_battles()
	# for i in reversed(range(50))
		# post_battle(i, True if i == 0 else False)
	fw = open('hoge.json', 'w')
	json.dump(results,fw,indent=4)