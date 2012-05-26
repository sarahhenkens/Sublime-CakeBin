import sublime
import sublime_plugin
import urllib
import urllib2
import threading
import re
import webbrowser

class CakebinCommand(sublime_plugin.TextCommand):
	def run(self, edit):
		s = sublime.load_settings("CakeBin.sublime-settings")
		nickname = s.get('nickname')

		if nickname == False:
			self.view.window().show_input_panel('What is your nickname?', '', self.handle, self.on_change, self.on_cancel);
		else:
			self.handle(nickname)

	def handle(self, nickname):
		selection = ''
		sels = self.view.sel()
		for sel in sels:
			selection += self.view.substr(sel)

		if len(selection) == 0:
			return

		thread = CakebinApiCall(selection, self.view.settings().get('syntax'), nickname, 5)
		thread.start();

	def on_change(self, input):
		pass
	def on_cancel(self):
		pass



class CakebinApiCall(threading.Thread):
	def __init__(self, string, syntax, nickname, timeout):
		self.string = string
		self.syntax = syntax
		self.nickname = nickname
		self.timeout = timeout
		self.result = None
		threading.Thread.__init__(self)

	def run(self):
		try:
			#Fetch form to get the security tokens
			request = urllib2.Request('http://bin.cakephp.org/index.php',
				headers={"User-Agent": "Sublime CakeBin"})
			http_file = urllib2.urlopen(request, timeout=self.timeout)
			self.result = http_file.read()

			tokenKey = re.search('name="data\[_Token\]\[key\]" value="(.+?)"', self.result).group(1)
			tokenFields = re.search('name="data\[_Token\]\[fields\]" value="(.+?)"', self.result).group(1)

			#Submit form data
			lang = self.parseSyntax(self.syntax)

			data = {
				'data[_Token][key]':tokenKey,
				'data[NewPaste][body]': self.string,
				'data[NewPaste][nick]': self.nickname,
				'data[NewPaste][lang]': lang,
				'data[NewPaste][note]': '',
				'data[NewPaste][save]': '0',
				'data[NewPaste][tags]': '',
				'data[Other][title]': '',
				'data[Other][date]': '',
				'data[_Token][fields]':tokenFields
			}

			request = urllib2.Request('http://bin.cakephp.org/index.php',
				headers={"User-Agent": "Sublime CakeBin"},
				data=urllib.urlencode(data))

			http_file = urllib2.urlopen(request, timeout=self.timeout)

			webbrowser.open_new(http_file.geturl())

			return

		except (urllib2.HTTPError) as (e):
			err = '%s: HTTP error %s contacting bin.cakephp.org' % (__name__, str(e.code))
		except (urllib2.URLError) as (e):
			err = '%s: URL error %s contacting bin.cakephp.org' % (__name__, str(e.reason))

		sublime.error_message(err)
		self.result = False

	def parseSyntax(self, syntax):
		lookup = {
			'Packages/Python/Python.tmLanguage': 'python',
			'Packages/PHP/PHP.tmLanguage': 'php',
			'Packages/SQL/SQL.tmLanguage': 'sql',
			'Packages/CSS/CSS.tmLanguage': 'css',
			'Packages/JavaScript/JavaScript.tmLanguage': 'javascript'
		}

		#Default to plain text
		cakeSyntax = 'text'

		if syntax in lookup:
			cakeSyntax = lookup[syntax]


		return cakeSyntax



