# Attempt to send a capture payload to re-use the existing session
from intercom import Client, Server
client = Client('capture')
client.sendPayload('')

# If the client errored, there is no existing active session so create a new one
if client.errored:
	import os
	import sys
	import ctypes
	import argparse
	parser = argparse.ArgumentParser(description='Capture the screen')
	parser.add_argument('--screenshot', action='store_true')
	parser.add_argument('--record', action='store_true')
	parser.add_argument('--loglevel', nargs='?', metavar='')
	args = parser.parse_args()

	# Define our Environment
	#os.environ['QT_AUTO_SCREEN_SCALE_FACTOR'] = '1'
	if args.loglevel:
		os.environ['LOGLEVEL'] = str(args.loglevel).upper()

	#os.environ['PYAV_LOGGING'] = 'off'

	from capture.app import CaptureWindow
	from relic.qt.util import readAllContents
	from PySide6.QtWidgets import QApplication
	from PySide6.QtGui import QIcon

	# C Python Windowing
	ctypes.windll.kernel32.SetConsoleTitleW('Capture')
	ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(u'resarts.relic.capture')

	app = QApplication()
	base_style = readAllContents(':base_style.qss')
	app_style = readAllContents(':style/app_style.qss')
	app.setStyleSheet(base_style + app_style)

	window = CaptureWindow()
	window.setWindowIcon(QIcon(':icons/capture.svg'))
	app.processEvents()
	window.show()
	server = Server('capture')
	server.incomingFile.connect(window.performScreenshot)
	window.taskbar_pin(True)
	if args.screenshot:
		window.performScreenshot()
	elif args.record:
		window.recordButton.click()
	window.show()
	sys.exit(app.exec())
