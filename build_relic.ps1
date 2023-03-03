.\Scripts\pyside6-rcc.exe .\resources.qrc -o .\resources_rc.py
.\Scripts\pyside6-rcc.exe  .\Lib\site-packages\qtshared6\resources.qrc -o .\Lib\site-packages\qtshared6\resources.py
# Get all .ui files in the dir and build them with uic.
ls -Path .\library\ui -Filter "*.ui" | % {.\Scripts\pyside6-uic.exe $_.FullName -o $_.FullName.Replace(".ui", ".py")}

.\Scripts\pyside6-rcc.exe .\plugins\LibShared\relic\qt\resources\resources.qrc -o .\plugins\LibShared\relic\qt\relic_resources6.py
C:\Users\Resartist\AppData\Local\Programs\Python\Python37\Scripts\pyside2-rcc.exe .\plugins\LibShared\relic\qt\resources\resources.qrc -o .\plugins\LibShared\relic\qt\relic_resources2.py
.\Scripts\pyside6-uic.exe .\plugins\LibShared\relic\qt\ui\expandable_group.ui -o .\plugins\LibShared\relic\qt\ui\expandable_group6.py
C:\Users\Resartist\AppData\Local\Programs\Python\Python37\Scripts\pyside2-uic.exe .\plugins\LibShared\relic\qt\ui\expandable_group.ui -o .\plugins\LibShared\relic\qt\ui\expandable_group2.py
