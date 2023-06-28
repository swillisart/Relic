import sys
import os
import argparse
import registry

parser = argparse.ArgumentParser(description='Asset Repository, Browser and Manager.')
parser.add_argument('--path', nargs='?', metavar='')
parser.add_argument('--loglevel', nargs='?', metavar='')

args = parser.parse_args()

# Define the program Environment
os.environ['QT_AUTO_SCREEN_SCALE_FACTOR'] = '1'
if args.loglevel:
    os.environ['LOGLEVEL'] = str(args.loglevel).upper()

# Registry Entries
command = '"{}" --path "%1"'.format(str(sys.argv[0]).replace('/', '\\'))
protocol = 'relic'
registry.protocolRegistryEntry(command, protocol)

# Launch 
if args.path:
    # Attempt to use existing session
    from intercom import Client
    client = Client('relic')
    client.sendPayload(args.path)
    if client.errored:
        import library
        library.app.main(args)
else:
    import library
    library.app.main(args)
