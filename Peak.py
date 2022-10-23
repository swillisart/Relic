import sys
import os
import argparse
parser = argparse.ArgumentParser(description='Viewer for 3D & 2D Assets')
parser.add_argument('--annotate', action='store_true')
parser.add_argument('--path', nargs='?', metavar='')

args = parser.parse_args()

if __name__ == '__main__':
    # Define the launch Environment
    os.environ['QT_AUTO_SCREEN_SCALE_FACTOR'] = '1'

    import viewer

    if args.path:
        # Attempt to use existing session
        from intercom import Client
        client = Client('peak')
        client.sendPayload(args.path)
        if client.errored:
            viewer.app.main(args)
    else:
        viewer.app.main(args)
