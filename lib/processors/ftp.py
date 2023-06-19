# path: lib/processors/
# filename: ftp.py
# description: WSGI application sugar api processors

''' 
	Copyright 2017 Mark Madere

	Licensed under the Apache License, Version 2.0 (the "License");
	you may not use this file except in compliance with the License.
	You may obtain a copy of the License at

	http://www.apache.org/licenses/LICENSE-2.0

	Unless required by applicable law or agreed to in writing, software
	distributed under the License is distributed on an "AS IS" BASIS,
	WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
	See the License for the specific language governing permissions and
	limitations under the License.
'''

''' external imports
'''
import ftplib
import os

''' internal imports
'''
import classes.processor

class Upload(classes.processor.Processor):

	'''
	# example usage
	
	process:
		type: lib.processors.ftp.Upload
		conf:
			host: ftp.example.com
			port: 21
			user: myusername
			pass: mysecret
		file: relative/to/application/filename.ext
		remotepath: /path/to/place/file/on/server/	
	'''

	def run(self):
	
		conf = self.conf
		debug = False
		
		if conf.get('debug'):
			print('lib.processors.ftp.Upload')
			debug = True

		# ftp server conf

		if 'conf' not in conf:
			print('missing ftp configuration (conf)')
			return False

		if 'host' not in conf['conf']:
			print('missing ftp host')
			return False
		
		conf['conf']['port'] = int(conf['conf'].get('port',"21"))
			
		if 'user' not in conf['conf']:
			print('missing ftp user')
			return False			

		if 'pass' not in conf['conf']:
			print('missing ftp pass')
			return False
			
		# file to upload
		if 'file' not in conf:
			print('missing file')
			return False

		# connect to ftp server
		ftp = ftplib.FTP(self.content.fnr(conf['conf']['host']))
		ftp.login(self.content.fnr(conf['conf']['user']),self.content.fnr(conf['conf']['pass']))
		
		# change remote directory (optional)
		if 'remotepath' in conf:
			ftp.cwd(self.content.fnr(conf['remotepath']))		
		
		# upload file
		ftp.storbinary("STOR " + self.content.fnr(os.path.split(conf['file'])[1]), open(self.content.fnr(conf['file']), "rb"), 8192)
		
		return True


class Download(classes.processor.Processor):

	'''
	# example usage
	
	process:
		type: lib.processors.ftp.Download
		conf:
			host: ftp.example.com
			port: 21
			user: myusername
			pass: mysecret
			
		file: filename.ext
		remotepath: /path/to/retrieve/file/on/server/
		localpath: save/file/relative/to/application/
	'''

	def run(self):

		conf = self.conf
		debug = False
		
		if conf.get('debug'):
			print('lib.processors.ftp.Download')
			debug = True

		# ftp server conf

		if 'conf' not in conf:
			print('missing ftp configuration (conf)')
			return False

		if 'host' not in conf['conf']:
			print('missing ftp host')
			return False
		
		conf['conf']['port'] = int(conf['conf'].get('port',"21"))
			
		if 'user' not in conf['conf']:
			print('missing ftp user')
			return False			

		if 'pass' not in conf['conf']:
			print('missing ftp pass')
			return False
			
		# file to upload
		if 'file' not in conf:
			print('missing file')
			return False

		# connect to ftp server
		ftp = ftplib.FTP(self.content.fnr(conf['conf']['host']))
		ftp.login(self.content.fnr(conf['conf']['user']),self.content.fnr(conf['conf']['pass']))
		
		# change remote directory (optional)
		if 'remotepath' in conf:
			ftp.cwd(self.content.fnr(conf['remotepath']))		

		# define local path
		localpath = self.content.fnr(conf.get('localpath','.'))	
		
		# Download file
		ftp.retrbinary("RETR " +  self.content.fnr(conf['file']) ,open("%s/%s"%(localpath,self.content.fnr(os.path.split(conf['file'])[1])), 'wb').write)
		
		return True

 

