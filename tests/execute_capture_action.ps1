$sockpipe = New-Object System.IO.Pipes.NamedPipeClientStream('capture')
$sockpipe.Connect()
