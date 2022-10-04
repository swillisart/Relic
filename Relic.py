import sys
import os
import argparse
parser = argparse.ArgumentParser(description='Asset Repository, Browser and Manager')
parser.add_argument('--path', nargs='?', metavar='')

args = parser.parse_args()

if __name__ == '__main__':
    # Define the launch Environment
    os.environ['QT_AUTO_SCREEN_SCALE_FACTOR'] = '1'
    os.environ['PYAV_LOGGING'] = 'off'
    import library

    if args.path:
        # Attempt to use existing session
        from relic.qt.strand.client import StrandClient
        client = StrandClient('relic')
        client.sendPayload(args.path)
        if client.errored:
            library.app.main(args)
    else:
        library.app.main(args)
