import sys
import os
import argparse
parser = argparse.ArgumentParser(description='Capture the screen')
parser.add_argument('--screenshot', nargs='?', metavar='')
parser.add_argument('--record', nargs='?', metavar='')
args = parser.parse_args()

if __name__ == '__main__':
    # Define our Environment
    os.environ['QT_AUTO_SCREEN_SCALE_FACTOR'] = '1'
    from strand.client import StrandClient
    client = StrandClient('capture')
    client.sendPayload('')
    if client.errored:
        import capture
        capture.app.main(sys.argv)
