# path: lib/processors
# filename: logic.py
# description: WSGI application logic processors

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
class Evaluate(classes.processor.Processor):
	
	def run(self):
		
		conf = self.conf
		debug = True		
		
		if conf.get('debug'):
			
			print('lib.processors.logic.Evaluate')
			debug = True		
		
		#print('lib.processors.logic.Evaluate')
		
		expression = conf.get('expression')

		if expression:

			if debug:
				print(expression)
			
			expression = self.content.fnr(expression)
			
			if debug:
				print(expression)
			
			if eval(expression):
				
				if debug:
					print("True")
				
				return True
				
			else:
				
				if debug:
					print("False")
				
				return False
