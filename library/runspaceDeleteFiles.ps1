$sources=@()
ls -r -Directory | %{$sources+=$_.FullName}

$pool = [runspacefactory]::CreateRunspacePool(1, [int]$env:NUMBER_OF_PROCESSORS-4)
$pool.ApartmentState = "MTA"
$pool.Open()
$runspaces = @()

$scriptblock = {
    Param(
        [string]$source
    )
    $now = Get-Date
    $all_files = ls -Path $source | where {$_.Extension -eq ".exr"}
    foreach ($f in $all_files) {
        $prop = Get-ItemProperty $f.FullName
        if (($prop.LastWriteTimeUtc.Date -lt $now.Date.AddDays(-20))) {
            $na = $f.Name
            $v = $prop.LastWriteTimeUtc.Date
            set-content ".\RM\$na.txt" -value "$v"
            #Remove-Item $f.FullName -Force
        }
    }
}

for($i=0; $i -lt $sources.Count; $i++){
    $runspace = [PowerShell]::Create()
    $null = $runspace.AddScript($scriptblock)
    $null = $runspace.AddArgument($sources[$i])
    $runspace.RunspacePool = $pool
    $runspaces += [PSCustomObject]@{ Pipe = $runspace; Status = $runspace.BeginInvoke()}
}

 while ($runspaces.Status.IsCompleted -notcontains $true) {}
 
 foreach ($runspace in $runspaces) {
     $results = $runspace.Pipe.EndInvoke($runspace.Status)
     $results
     $runspace.Pipe.Dispose()
 }
 
$pool.Close()
$pool.Dispose()