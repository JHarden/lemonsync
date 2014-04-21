import sys 
import time
import os 
import ConfigParser
import boto.s3 
import boto.s3.connection 

from boto.s3.key import Key
from watchdog.events import FileSystemEventHandler
from boto.s3.key import Key
from Config import config
from Connector import Connector

class Listener(FileSystemEventHandler):
	
	def __init__(self):
		# Get the s3 credentials for a federated user from the LemonStand2 API
		credentials = Connector()
		identity = credentials.getIdentity(config.api_host, config.store_host, config.api_access)

		self.conn = boto.s3.connection.S3Connection(aws_access_key_id=identity['key'], aws_secret_access_key=identity['secret'], security_token=identity['token']) 
		self.bucket = self.conn.get_bucket(identity['bucket'], validate = False)
		self.store = identity['store']
		self.theme = identity['theme']
		self.watch = config.watch_dir

		print '\033[92m' + 'LemonSync is listening to changes on ' + config.watch_dir

	def __getKey(self, event_path):
		# strip out the watch dir, from the modified path to get the relative folder in S3
		path = event_path.replace(self.watch, '')
		# this will create the full s3 key
		key = os.path.join(self.store, "themes", self.theme, path)

		return key

	def remove(self, event_path):
		key = self.__getKey(event_path)

		try:
			self.bucket.delete_key(key)
			print '\033[92m' + '[' + time.strftime("%c") + '] Successfully removed ' + key + ''
		except:
			print '\033[91m' + '[' + time.strftime("%c") + '] Failed to remove ' + key + ''

	def upsert(self, event_path):
		key = self.__getKey(event_path)

		try:
			k = self.bucket.new_key(key)
			k.set_contents_from_filename(event_path)
			print '\033[92m' + '[' + time.strftime("%c") + '] Successfully uploaded ' + key + ''
		except:
			print '\033[91m' + '[' + time.strftime("%c") + '] Failed to upload ' + key + ''


	def on_modified(self, event):
		filename, ext = os.path.splitext(event.src_path)

		# Some editors will create tmp files before writing to the actual file
		if (ext == '.tmp'): 
			return

		if not event.is_directory:
			self.upsert(event.src_path)

	def on_created(self, event):
		filename, ext = os.path.splitext(event.src_path)

		# Some editors will create tmp files before writing to the actual file
		if (ext == '.tmp'): 
			return

		if not event.is_directory:
			self.upsert(event.src_path)

	def on_moved(self, event):
		filename, ext = os.path.splitext(event.dest_path)

		# Some editors will create tmp files before writing to the actual file
		if (ext == '.tmp'): 
			return

		if not event.is_directory:
			self.upsert(event.dest_path)

	def on_deleted(self, event):
		filename, ext = os.path.splitext(event.src_path)

		# Some editors will create tmp files before writing to the actual file
		if (ext == '.tmp'): 
			return

		if not event.is_directory:
			self.remove(event.src_path)