# path: core/classes/
# filename: view.py

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
import web
import yaml

import datetime
import os
import re
import sys

import logging




''' internal imports
'''
import classes.content
import lib.marker.methods

''' classes
'''
class View(object):
	
	def __init__(self):
		
		#start logging
		loglevel = logging.INFO
		logging.basicConfig(format='%(asctime)s %(message)s', datefmt='%Y-%m-%d %H:%M:%S', level=loglevel)		

		''' vars
		'''
		self.error = None # is this still used?
		
		# timestamp - used by debug
		self.start_time = datetime.datetime.now()
		
		# web.py sessions
		try:
			self.session = web.ctx.session #WSGI application
		except AttributeError:
			self.session = session #Cherry webserver
		
		# debug 
		#self.session.kill() 
		
		# urls.cfg
		self.urls_config_file = 'conf/urls.cfg'
		
		
		# top/view Vars
		self.path_vars = {}
		self.get_vars = {}
		self.post_vars = {}
		self.post = False
		self.marker_map = {}
		
		self.cache = {}
		self.raw = {}
		self.attributes = {}

		# session vars
		if 'vars' not in dir(self.session):
			self.session.vars= {}

		
		# marker attributes
		self.marker_map = {

			# Attributes
			
			# Caches
			'cache': 'self.top.cache', # this should be depricated
			'session': 'self.top.session.vars',
			
			# URI/GET/POST
			'path': 'self.top.path_vars',
			'get': 'self.top.get_vars',
			'post': 'self.top.post_vars',
			'getpost': 'self.top.getpost_vars',
			'raw': 'self.top.raw',
			'header': 'self.top.header',			

			# ATTRIBUTES
			'this': 'self.attributes',	
			'parent': 'self.parent.attributes',
			'top': 'self.top.attributes',
			'view': 'self.view.attributes',
			'data': 'self.data',
		
		}
		
		# add marker methods
		self.mmethods = lib.marker.methods
		self.marker_map.update(self.mmethods.marker_map)
		
		return None
	
	
	def GET(self,path=None):
		
		self.log('Received GET request','debug')
		
		''' vars
		'''
		self.path = path
		
		# RAW
		self.raw = web.data()		

		# GET vars
		self.get_vars = self.build_get_vars()
		self.getpost_vars = self.get_vars
		
		# build page
		return self.run()
	
	
	def POST(self,path=None):
		
		self.log('Received POST request','debug')
	
		# This is required to for file uploads Input
		x = web.input()
		
		# vars
		self.path = path
		self.post = True

		# RAW
		self.raw = web.data()

		#debug
		#print(self.raw)

		# POST vars
		self.post_vars = self.build_post_vars()
		
		#print("POST vars: "+str(self.post_vars))
		
		# GET vars
		self.get_vars = self.build_get_vars()
		
		self.getpost_vars = self.post_vars

		# remove GET vars from POST vars
		#self.remove_get_vars_from_post_vars()
	
		# build page
		return self.run()


	def build_get_vars(self):
		
		get_vars = web.webapi.rawinput("GET")
		
		return get_vars
	
	
	def build_post_vars(self):
		
		post_vars = web.webapi.rawinput("POST")

		
		#convert to dict
		tmp_post_vars = {}
		for key in post_vars:
			tmp_post_vars[key] = post_vars[key]
		post_vars = tmp_post_vars
		
		return post_vars

	
	def remove_get_vars_from_post_vars(self):
		
		# this fixes both a security vularibility and a functionality problem
		# but it assumes that get vars come before post vars and has been problematic
		# this method is not currently being used
		
		for key in self.post_vars:
			
			if key in self.get_vars:
				
				for value in self.get_vars[key]:
					
					self.post_vars[key].remove(value)
					
		return None


	def run(self):
		
		# vars
		
		# result of urls conf file
		web.framework['urls']  = web.framework['configuration_object'].load_views(self.urls_config_file)
		available_urls = web.framework['urls']		
		
		content_config_files = []
		
		# cache the path for use by fnr
		self.cache['url'] = '%s/%s' %(web.ctx.home,self.path)
		self.cache['path'] = '/%s' %self.path
		self.cache['rurl'] = web.ctx.env.get('HTTP_REFERER')
		self.header = web.ctx.env
		
		# convert the requested url into a  "/" delimited list
		url_list = self.path.split('/')
		
		if url_list[0] == '':
			url_list.pop(0)
		
		url_list.insert(0,'/')

		# convert the requested url back into a string with leading /
		requested_url = url_list[0]+"/".join(url_list[1:])
		self.requested_url = requested_url
		
		# compare visitor url with urls in url config	
		for i in range(0,len(available_urls)):
			
			# this should return one dict key which is the url segment
			for available_url in available_urls[i]:
				
				#debug
				#print(available_url)
				#print("Type: "+ str(type(available_url)))
				
				r = "%s/"%requested_url.lower()
				a = "%s/"%available_url.lower()
				
				# if the requested url starts with the available url then the request is part of a path
				if r.startswith(a):

					'''	View Confiuration
					'''

					'''
						I am not sure i want this feature anymore
						
					# assign/update attributes - supports inheritence /1/2/ inherits from /1
					self.attributes.update(available_urls[i][available_url])						
					'''
					
					# view attributes
					self.attributes = available_urls[i][available_url]
					
					# view name - used for caching content configuration
					self.attributes['name'] = a					

					'''	This sting to list conversion should happen at another level
					'''
					# get a list of configuration files to load for this url
					content_config_files = self.attributes.get('conf',[])
					
					# allow conf to be a string.  convert to list
					if isinstance(content_config_files,str):
						content_config_files = [content_config_files]
					
					# update conf attribute
					self.attributes['conf'] = content_config_files
					
					
					'''	PATH vars
					'''					
					# filter removes any empty items casued by multiple slashes (//)
					requested_url_list = list(filter(None, requested_url.split("/")))
					available_url_list = list(filter(None, available_url.split("/")))
					
					# remove the available url from the requested url to get the path vars
					path_vars = requested_url_list[len(available_url_list):]
		
		# apply log level
		if self.attributes.get('log_level'):
			logging.getLogger().setLevel(self.attributes['log_level'].upper())
			print('log_level is now %s'%self.attributes['log_level'].upper())		
		
		# Handle 404 errors
		if not 'conf' in self.attributes or len(self.attributes['conf']) == 0:

			print("Config Error:  No configuration files were found for the view '%s'." %requested_url)
			
			return self.error404()


		''' Custom Headers
		'''
		if 'header' in self.attributes:
			
			if not isinstance(self.attributes['header'], list):
			
				self.attributes['header'] = [self.attributes['header']]
		
			for header in self.attributes['header']:
					
				eval('web.header(%s)' %header)
				
		else:
			web.header('Content-Type','text/html; charset=utf-8')
		
		
		'''Cache Output - READ
			This cache is used to make static copies of final output generated by WebYAML.
			If your view requires dynamic processing DO NOT use this type of cache.
		'''
		if 'cache' in self.attributes and self.attributes['cache'] == 'output':
			
			cache_file = "cache/_:_%s" %str(requested_url.strip("/").replace("/","_:_"))
			
			# is page in cache?
			try:
				f = open(cache_file,'r')
				output = f.read()
				f.close()
				
				#debug
				#print('found cache file')
				
				return output
				
			except IOError:
				
				# warn - the page will still be generated
				print("cache file '%s' not found" %cache_file)
					
		
		'''	This view is not cached, therefore path vars must be assigned
		'''
		# assign path_vars as dict with keys arg0, arg1, etc...
		for i in range(0, len(path_vars)):
			self.path_vars['arg'+str(i)] = path_vars[i]
		
		# debug
		if self.get_vars:
			self.log("GET vars: %s"%str(dict(self.get_vars)),'debug')

		if self.post_vars:
			self.log("POST vars: %s"%str(self.post_vars),'debug')
		
		if self.path_vars:
			self.log("PATH vars: "+str(self.path_vars),'debug')

		
		# CACHE INPUT
		
		''' 	The view configuration file may be cached in memory.
			If the configuration is not found load from file(s).
		'''
		if 'cache' in self.attributes and self.attributes['cache'] == 'input':
			
			# search for configuration cache
			if self.attributes['name'] in web.framework['configuration_object'].cache['conf']:
				
				# read configuration from cache
				self.conf = web.framework['configuration_object'].cache['conf'][self.attributes['name']]
				
				#debug
				#print("reading configuration for view '%s' from cache"%self.attributes['name'])
				
			else:
				
				# load core config files
				content_config_files.insert(0,"conf/processors/core.cfg")
				content_config_files.insert(0,"conf/elements/core.cfg")
				
				# load configuration files		
				self.conf =  web.framework['configuration_object'].load(*content_config_files)
				
				# write configuration to cache
				web.framework['configuration_object'].cache['conf'][self.attributes['name']] = self.conf
				
				#debug
				#print("writing configuration for view '%s' to cache"%self.attributes['name'])
			
		else:
			# load core config files
			content_config_files.insert(0,"conf/processors/core.cfg")
			content_config_files.insert(0,"conf/elements/core.cfg")
			
			# load configuration files		
			self.conf =  web.framework['configuration_object'].load(*content_config_files)
		
		
		''' Generate Output	
		'''
		#Create the Content Objects and perform Pre-processing
		c = classes.content.Content(self,self.conf)
		
		#Render all elements of the Content Tree
		output = c.render()
		
		
		# debug
		if self.cache:
			self.log('Cache vars: %s'%str(self.cache),'debug')
		
		if self.session.vars:
			self.log('Session vars: %s'%str(self.session.vars),'debug')
		
		
		'''	Unless otherwise indicated remove any remaining markers
		'''
		# Remove any markers from output before returning
		if 'keepmarkers' not in self.attributes:
			
			pattern = re.compile(r'({{[\w|\(|\)|\.|\:|\-]+}})')
			markers = list(set(pattern.findall(output)))

			for marker in markers:
				output = output.replace(marker,'') #python3
		
		'''	Extra Debugging output
		'''
		if 'debug' in self.attributes:
			
			# add debugging information
			length = len(output)

			# timestamp
			self.end_time = datetime.datetime.now()
			
			duration_seconds = (self.end_time-self.start_time).seconds
			duration_microseconds = ((self.end_time-self.start_time).microseconds)/float(1000000)
			debug = '''
<div><pre>
	Size: %d
	Time: %s
<div></pre>
''' %(length, duration_seconds+duration_microseconds)

			output = debug+output
		
		
		'''	Cache Output - Write
			This cache is used to make static copies of final output generated by WebYAML.
			If your view requires dynamic processing do not use this type of cache.
		'''
		if 'cache' in self.attributes and self.attributes['cache'] == 'output':
			cache_file = "cache/_:_%s" %str(requested_url.strip("/").replace("/","_:_"))
			
			try:
				f = open(cache_file,'w')
				f.write(output)
				f.close()
				
				print("wrote cache file '%s'." %cache_file)
				
			except IOError:
				
				print("could not write cache file '%s' not found" %cache_file)
		
		''' Debug - Write final configuration to a file
		This is usefull for debugging generated attributes in content blocks
		'''
		if 'debug' in self.attributes and self.attributes['debug'] == 'conf':
			cache_file = "debug/_:_%s" %str(requested_url.strip("/").replace("/","_:_"))
			
			# not sure if allow_unicode=True is still needed in python3
			debug_output = yaml.dump(self.conf, allow_unicode=True, default_flow_style=False)

			try:
				f = open(cache_file,'w')
				f.write(debug_output)
				f.close()
				
				print("wrote debug file '%s'." %cache_file)
				
			except IOError:
				
				print("could not write debug file '%s' does the debug folder exist?" %cache_file)		
		
		
		'''	Return Output
		'''
		
		return output
		



	def error404(self):
		
		# vars
		gfx_agents = [
			"Chrome",
			"MSIE",
			"Firefox",
			"Safari",
			"AppleWebKit",
			"Gecko",
			"Dalvik",
		]

		for item in gfx_agents:
			if 'HTTP_USER_AGENT' in web.ctx.env and item in web.ctx.env['HTTP_USER_AGENT']:
				message_404 = '''<!DOCTYPE HTML PUBLIC "-//IETF//DTD HTML 2.0//EN">
<html><head>
<title>404 Not Found</title>
</head><body>
<h1>Not Found</h1>
<p>The requested URL %s was not found on this server.</p>
<hr>
<address>WebYAML Application Server</address>
</body></html>''' %self.requested_url
		
				raise web.notfound(message_404)
				
		raise web.notfound()


	def	log(self, msg, level="WARNING"):
		
		levels = {
			"DEBUG": logging.debug,
			"INFO": logging.info,
			"WARNING": logging.warning,
			"ERROR": logging.error,
			"CRITICAL": logging.critical,
			#"NOTSET": pass,
		}
		#print(msg)
		levels[level.upper()]('%s:%s %s "%s %s" %s'%(web.ctx.env.get('REMOTE_ADDR'),web.ctx.env.get('REMOTE_PORT'),level.upper(),web.ctx.env.get('REQUEST_METHOD'),web.ctx.env.get('REQUEST_URI'),msg))		

		'''
		web.ctx.env.get:
		https://webpy.org/cookbook/ctx
		
		{
			'ACTUAL_SERVER_PROTOCOL': 'HTTP/1.1', 
			'PATH_INFO': '/', 
			'QUERY_STRING': '', 
			'REMOTE_ADDR': '10.0.0.11', 
			'REMOTE_PORT': '33514', 
			'REQUEST_METHOD': 'GET', 
			'REQUEST_URI': '/', 
			'SCRIPT_NAME': '', 
			'SERVER_NAME': 'localhost', 
			'SERVER_PROTOCOL': 'HTTP/1.1', 
			'SERVER_SOFTWARE': 'Cheroot/8.3.0 Server', 
			'wsgi.errors': <_io.TextIOWrapper name='<stderr>' mode='w' encoding='UTF-8'>, 
			'wsgi.input': <cheroot.server.KnownLengthRFile object at 0x7fe9dce359b0>, 
			'wsgi.input_terminated': False, 
			'wsgi.multiprocess': False, 
			'wsgi.multithread': True, 
			'wsgi.run_once': False, 
			'wsgi.url_scheme': 'http', 
			'wsgi.version': (1, 0), 
			'SERVER_PORT': '8080', 
			'HTTP_HOST': '10.0.0.11:8080', 
			'HTTP_CONNECTION': 'keep-alive', 
			'HTTP_CACHE_CONTROL': 'max-age=0', 
			'HTTP_UPGRADE_INSECURE_REQUESTS': '1', 
			'HTTP_USER_AGENT': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.110 Safari/537.36', 
			'HTTP_ACCEPT': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8', 
			'HTTP_ACCEPT_ENCODING': 'gzip, deflate', 
			'HTTP_ACCEPT_LANGUAGE': 'en-US,en;q=0.9', 
			'HTTP_COOKIE': 'webpy_session_id=cdfe70ffceaaa9c8ee41c5faddfdfef385cea767'
		}

		
		
		environ a.k.a. env - a dictionary containing the standard WSGI environment variables
		home - the base path for the application, including any parts "consumed" by outer applications http://example.org/admin
		homedomain - ? (appears to be protocol + host) http://example.org
		homepath - The part of the path requested by the user which was trimmed off the current app. That is homepath + path = the path actually requested in HTTP by the user. E.g. /admin This seems to be derived during startup from the environment variable REAL_SCRIPT_NAME. It affects what web.url() will prepend to supplied urls. This in turn affects where web.seeother() will go, which might interact badly with your url rewriting scheme (e.g. mod_rewrite)
		host - the hostname (domain) and (if not default) the port requested by the user. E.g. example.org, example.org:8080
		ip - the IP address of the user. E.g. xxx.xxx.xxx.xxx
		method - the HTTP method used. E.g. GET
		path - the path requested by the user, relative to the current application. If you are using subapplications, any part of the url matched by the outer application will be trimmed off. E.g. you have a main app in code.py, and a subapplication called admin.py. In code.py, you point /admin to admin.app. In admin.py, you point /stories to a class called stories. Within stories, web.ctx.path will be /stories, not /admin/stories. E.g. /articles/845
		protocol - the protocol used. E.g. https
		query - an empty string if there are no query arguments otherwise a ? followed by the query string. E.g. ?fourlegs=good&twolegs=bad
		fullpath a.k.a. path + query - the path requested including query arguments but not including homepath. E.g. /articles/845?fourlegs=good&twolegs=bad
'''
