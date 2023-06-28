import sys
import os
import argparse
import registry

parser = argparse.ArgumentParser(description='Viewer for 3D & 2D Assets')
parser.add_argument('--path', nargs='?', metavar='')
parser.add_argument('--loglevel', nargs='?', metavar='')
parser.add_argument('--annotate', action='store_true')

args = parser.parse_args()

# Define the program Environment
os.environ['QT_AUTO_SCREEN_SCALE_FACTOR'] = '1'
if args.loglevel:
    os.environ['LOGLEVEL'] = str(args.loglevel).upper()

# Registry Entries
command = '"{}" --path "%1"'.format(sys.argv[0])
protocol = 'peak'
registry.protocolRegistryEntry(command, protocol)

# Launch

if args.path:
    # Attempt to use existing session
    from intercom import Client
    client = Client('peak')
    client.sendPayload(args.path)
    if client.errored:
        import viewer
        viewer.app.main(args)
else:
    import viewer
    viewer.app.main(args)
