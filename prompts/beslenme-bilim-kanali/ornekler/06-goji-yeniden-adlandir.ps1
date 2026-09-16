<#
  Goji gorsellerini montaj aracinin bekledigi 01-40 adlandirmasina cevirir.
      .\06-goji-yeniden-adlandir.ps1 -Dir "C:\gorseller\goji" -WhatIf
      .\06-goji-yeniden-adlandir.ps1 -Dir "C:\gorseller\goji"
  Uretilen adlarda Turkce karakter ve uzun aciklama var; Moskova belgeselinde
  ad icindeki aksanli bir harf montaj aracinda hata vermisti.
#>
[CmdletBinding(SupportsShouldProcess=$true)]
param([string]$Dir = ".")
$ErrorActionPreference = "Stop"
if (-not (Test-Path -LiteralPath $Dir)) { throw "klasor yok: $Dir" }
Push-Location $Dir

Write-Host "== Faz 1: gecici adlara =="
$n = 0
foreach ($f in Get-ChildItem -File) {
  if ($f.Name -notmatch 'rsel[_ ]*(\d{1,2})') { Write-Host "  atlandi: $($f.Name)"; continue }
  $tmp = "tmp_{0:d2}{1}" -f [int]$Matches[1], $f.Extension
  if ($PSCmdlet.ShouldProcess($f.Name, "-> $tmp")) { Rename-Item -LiteralPath $f.FullName -NewName $tmp }
  else { Write-Host "  [kuru] $($f.Name) -> $tmp" }
  $n++
}
Write-Host "  eslesen: $n"

Write-Host "== Faz 2: nihai adlar =="
foreach ($f in Get-ChildItem -File -Filter "tmp_*") {
  $final = $f.Name.Substring(4)
  if ($PSCmdlet.ShouldProcess($f.Name, "-> $final")) { Rename-Item -LiteralPath $f.FullName -NewName $final }
  else { Write-Host "  [kuru] $($f.Name) -> $final" }
}
Write-Host ""
Write-Host "Bitti. Klasorde 01..40 araliginda tam 40 dosya olmali."
Pop-Location
