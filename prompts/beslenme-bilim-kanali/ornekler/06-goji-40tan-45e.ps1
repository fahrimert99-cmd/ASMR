<#
  5 yeni kare eklendiginde 40'lik numaralandirmayi 45'lige kaydirir.
  Yeni kareler: 33, 34, 43, 44, 45.  Eski 33-40 -> 35-42.
      .\06-goji-40tan-45e.ps1 -Dir "C:\gorseller\goji" -WhatIf
#>
[CmdletBinding(SupportsShouldProcess=$true)]
param([string]$Dir = ".")
$ErrorActionPreference = "Stop"
Push-Location $Dir
$map = @{}
33..40 | ForEach-Object { $map[$_] = $_ + 2 }

Write-Host "== Faz 1: gecici adlara =="
foreach ($f in Get-ChildItem -File) {
  if ($f.Name -notmatch '^(\d{1,2})\.[^.]+$') { continue }
  $old = [int]$Matches[1]
  if (-not $map.ContainsKey($old)) { continue }
  $tmp = "tmp_{0:d2}{1}" -f $map[$old], $f.Extension
  if ($PSCmdlet.ShouldProcess($f.Name, "-> $tmp")) { Rename-Item -LiteralPath $f.FullName -NewName $tmp }
  else { Write-Host "  [kuru] $($f.Name) -> $tmp" }
}
Write-Host "== Faz 2: nihai adlar =="
foreach ($f in Get-ChildItem -File -Filter "tmp_*") {
  $final = $f.Name.Substring(4)
  if ($PSCmdlet.ShouldProcess($f.Name, "-> $final")) { Rename-Item -LiteralPath $f.FullName -NewName $final }
  else { Write-Host "  [kuru] $($f.Name) -> $final" }
}
Write-Host ""
Write-Host "Bos kalan numaralar (yeni uretilecek): 33 34 43 44 45"
Pop-Location
