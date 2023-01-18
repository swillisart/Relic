killapp exiftool
$dst = './dist/Relic'
if (Test-Path -path $dst ){
    remove-item $dst -r -Force -Confirm:$False
}
./scripts/activate
pyinstaller --noconfirm ./Relic.spec

Copy-item -path './Lib/site-packages/imagine/libraw/libraw.dll' -destination $dst
Copy-item -path './gifski.exe' -destination $dst
Copy-item -path './hdr_create.exe' -destination $dst
Copy-item -path './exiftool.exe' -destination $dst
Copy-item -path './README.md' -destination $dst

robocopy /E /xc './dist/Peak' './dist/Relic' 
robocopy /E /xc './dist/Capture' './dist/Relic'
robocopy /E /xc './Lib/site-packages/freetype' ($dst + '/freetype')
robocopy /E /xc './Lib/site-packages/cv2/data' ($dst + '/cv2/data')
robocopy /E /xc './viewer/luts' ($dst + '/luts')

remove-item './dist/Peak' -r -Force -Confirm:$False
remove-item './dist/Capture' -r -Force -Confirm:$False
