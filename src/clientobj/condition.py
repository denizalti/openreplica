#automatically generated by the clientobjectgenerator
from clientproxy import *

class Condition():
	def __init__(self):
		invoke_command(self, "__init__")

	def __str__(self):
		invoke_command(self, "__str__")

	def acquire(self, args):
		invoke_command(self, "acquire", args)

	def notify(self, args):
		invoke_command(self, "notify", args)

	def notifyAll(self, args):
		invoke_command(self, "notifyAll", args)

	def release(self, args):
		invoke_command(self, "release", args)

	def wait(self, args):
		invoke_command(self, "wait", args)
