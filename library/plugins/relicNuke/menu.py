import sys
#sys.path.append('P:/Code/Relic/library/plugins/Lib')
import nuke
import nukescripts

if nuke.GUI:
    import relicNukePlugin
    relicNukePlugin.main()
