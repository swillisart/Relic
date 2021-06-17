import sys
import os
from pathlib import Path
import argparse

parser = argparse.ArgumentParser(description='Asset Repository, Browser and Manager')
parser.add_argument('--path', nargs='?', metavar='')
parser.add_argument('relic', nargs='?', metavar='')

args = parser.parse_args()

exe = Path(sys.argv[0])
root = exe.parent
icon = root / 'resources/icons/app_icon.ico'
new_env = os.environ.copy()

if __name__ == '__main__':
    #os.environ['PYTHONPATH'] = root.as_posix() + ';{}/pypackages36'.format(root.as_posix())
    os.environ['PATH'] = os.environ['PATH'] + ';{}/bin'.format(root.as_posix())
    sys.path.insert(0, root.as_posix())
    #sys.path.insert(0, '{}/pypackages36'.format(root.as_posix()))
    os.environ['QT_AUTO_SCREEN_SCALE_FACTOR'] = '1'
    import library
    library.app.main(args)
