.\Scripts\pyside6-rcc.exe .\resources.qrc -o .\resources_rc.py
.\Scripts\pyside6-rcc.exe  .\Lib\site-packages\qtshared6\resources.qrc -o .\Lib\site-packages\qtshared6\resources.py
# Get all .ui files in the dir and build them with uic.
ls -Path .\library\ui -Filter "*.ui" | % {.\Scripts\pyside6-uic.exe $_.FullName -o $_.FullName.Replace(".ui", ".py")}
C:\Users\Resartist\AppData\Local\Programs\Python\Python37\Scripts\pyside2-uic.exe .\library\plugins\Lib\relic_base\ui\title_bar.ui -o .\library\plugins\Lib\relic_base\ui\title_bar.py
C:\Users\Resartist\AppData\Local\Programs\Python\Python37\Scripts\pyside2-uic.exe .\library\ui\compact_delegate.ui -o .\library\plugins\Lib\relic_base\ui\compact_delegate.py
C:\Users\Resartist\AppData\Local\Programs\Python\Python37\Scripts\pyside2-uic.exe .\library\ui\expandableTabs.ui -o .\library\plugins\Lib\relic_base\ui\expandableTabs.py