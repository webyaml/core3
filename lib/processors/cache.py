# path: lib/processors/
# filename: cache.py
# description: processor to cache values in temporary storage
# note: this method is depricated by dataObjCreate
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

''' internal imports
'''
import classes.processor

''' classes
'''
class Cache(classes.processor.Processor):
	
	def run(self):
		
		self.view.log('Cache processor is depricated.  Consider using dataObjCreate instead.')
		
		conf = self.conf
		debug = False
		
		if conf.get('debug'):
			self.view.log('lib.processors.cache.Cache')
			debug = True
		
		if not conf.get('cache'):
			print('missing attribute cache')
			return False

		if not isinstance(conf['cache'],dict):
			print('attribute cache is not a dict')
			return False
			
		for var in conf['cache']:
			
			if debug:
				print('caching %s'%var)
			
			self.top.cache[var] = self.content.fnr(conf['cache'][var])
	
		return True
