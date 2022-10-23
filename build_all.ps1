﻿$dst = './dist/Relic'
if (Test-Path -path $dst ){
    remove-item $dst -r -Force -Confirm:$False
}
./scripts/activate
pyinstaller --noconfirm ./Relic.spec

Copy-item -path './Lib/site-packages/cv2/data' -destination ($dst + '/cv2/data')
Copy-item -path './Lib/site-packages/imagine/libraw/libraw.dll' -destination $dst
Copy-item -path './Lib/site-packages/freetype' -destination ($dst + '/freetype')
Copy-item -path './viewer/luts' -destination ($dst + '/luts')
Copy-item -path './gifski.exe' -destination $dst
Copy-item -path './hdr_create.exe' -destination $dst
Copy-item -path './exiftool.exe' -destination $dst
Copy-item -path './README.md' -destination $dst

robocopy /E /xc './dist/Peak' './dist/Relic' 
robocopy /E /xc './dist/Capture' './dist/Relic'

remove-item './dist/Peak' -r -Force -Confirm:$False
remove-item './dist/Capture' -r -Force -Confirm:$False
