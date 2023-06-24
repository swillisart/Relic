import sys
import os
import argparse
parser = argparse.ArgumentParser(description='Asset Repository, Browser and Manager.')
parser.add_argument('--path', nargs='?', metavar='')
parser.add_argument('--loglevel', nargs='?', metavar='')

args = parser.parse_args()

# Define the launch Environment
os.environ['QT_AUTO_SCREEN_SCALE_FACTOR'] = '1'
if args.loglevel:
    os.environ['LOGLEVEL'] = str(args.loglevel).upper()

import library

if args.path:
    # Attempt to use existing session
    from intercom import Client
    client = Client('relic')
    client.sendPayload(args.path)
    if client.errored:
        library.app.main(args)
else:
    library.app.main(args)
