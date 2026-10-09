param([Parameter(Mandatory=$true)][string]$Executable)
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Drawing
$Icon = [System.Drawing.Icon]::ExtractAssociatedIcon($Executable)
if ($null -eq $Icon) { exit 1 }
$Bitmap = $Icon.ToBitmap()
$Buffer = New-Object System.IO.MemoryStream
try {
    $Bitmap.Save($Buffer, [System.Drawing.Imaging.ImageFormat]::Png)
    [Console]::Write([Convert]::ToBase64String($Buffer.ToArray()))
} finally {
    $Buffer.Dispose()
    $Bitmap.Dispose()
    $Icon.Dispose()
}
