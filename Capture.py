import sys
import json
import argparse
parser = argparse.ArgumentParser(description='Capture the screen')
parser.add_argument('--screenshot', action='store_true')
parser.add_argument('--record', action='store_true')
parser.add_argument('--loglevel', nargs='?', metavar='')
args = parser.parse_args()
# Attempt to send a capture payload to re-use the existing session
from intercom import Client, Server
client = Client('capture')
# TODO: Capture Command line should forward the interface args to the
# current session in the case of the program already existing.
client.sendPayload(json.dumps(args.__dict__))

# If the client errored, there is no existing active session so create a new one

if not client.errored:
	sys.exit(0)

import os
import ctypes

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
server.incomingData.connect(window.main)
window.main(args.__dict__)
window.taskbar_pin(True)
window.show()
sys.exit(app.exec())
