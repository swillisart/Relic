import argparse
import time

parser = argparse.ArgumentParser(description="Process Maya in Standalone")
parser.add_argument("--pushDependencies", nargs=1, required=False)
parser.add_argument("--ies", nargs=1, required=False)
args = parser.parse_args()


def main(args):
    import maya.standalone

    maya.standalone.initialize(name="python")
    import maya.cmds as cmds
    import alMaya

    if args.pushDependencies:
        cmds.file(args.pushDependencies, f=True, o=True)
        dependent_files = alMaya.getAllPaths()
        print("DEPENDENCIES BRUH", dependent_files)
    if args.ies:
        print(args.ies)
    maya.standalone.uninitialize()


if __name__ == "__main__":
    main(args)
