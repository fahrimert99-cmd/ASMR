<#
  Domates videosu - gorselleri 83 bloklu SRT numaralandirmasina tasir.
  Kullanim:
      .\05-domates-yeniden-adlandir.ps1 -Dir "C:\gorseller\domates" -WhatIf
      .\05-domates-yeniden-adlandir.ps1 -Dir "C:\gorseller\domates"

  Eski numaralandirma cumle bazliydi (1-80). ElevenLabs bazi cumleleri bolup
  bazilarini birlestirince SRT 83 blok verdi. Bu betik mevcut 78 dosyayi yeni
  blok numarasina tasir; eslesmeyen dosyalari silmez, "kullanilmayan" klasorune
  alir. Kalan 5 numara (05, 30, 31, 35, 58) yeni uretilecek gorseller icindir.
#>
[CmdletBinding(SupportsShouldProcess=$true)]
param([string]$Dir = ".")

$ErrorActionPreference = "Stop"
if (-not (Test-Path -LiteralPath $Dir)) { throw "klasor yok: $Dir" }
Push-Location $Dir

$map = @{
    2 = 1
    3 = 2
    4 = 3
    5 = 4
    6 = 6
    7 = 7
    8 = 8
    9 = 9
    10 = 10
    11 = 11
    12 = 12
    13 = 13
    14 = 14
    15 = 15
    16 = 16
    17 = 17
    18 = 18
    19 = 19
    21 = 20
    22 = 21
    23 = 22
    24 = 23
    25 = 24
    26 = 25
    27 = 26
    28 = 27
    29 = 28
    30 = 29
    31 = 32
    32 = 33
    33 = 34
    34 = 36
    35 = 37
    36 = 38
    37 = 39
    38 = 40
    39 = 41
    40 = 42
    41 = 43
    42 = 44
    43 = 45
    44 = 46
    45 = 47
    46 = 48
    47 = 49
    48 = 50
    49 = 51
    50 = 52
    51 = 53
    52 = 54
    53 = 55
    54 = 56
    55 = 57
    56 = 59
    57 = 60
    58 = 61
    59 = 62
    60 = 63
    61 = 64
    62 = 65
    63 = 66
    64 = 67
    65 = 68
    66 = 69
    67 = 70
    68 = 71
    69 = 72
    70 = 73
    71 = 74
    72 = 75
    73 = 76
    74 = 77
    75 = 78
    76 = 79
    77 = 80
    78 = 81
    79 = 82
    80 = 83
}

function Get-Num([string]$name) {
  if ($name -match '^(\d{1,2})\.[^.]+$') { return [int]$Matches[1] }
  return $null
}

Write-Host "== Faz 1: gecici adlara =="
$moved = 0
foreach ($f in Get-ChildItem -File) {
  $n = Get-Num $f.Name
  if ($null -eq $n -or -not $map.ContainsKey($n)) { continue }
  $new = '{0:d2}' -f $map[$n]
  $tmp = "tmp_$new$($f.Extension)"
  if ($PSCmdlet.ShouldProcess($f.Name, "-> $tmp")) { Rename-Item -LiteralPath $f.FullName -NewName $tmp }
  else { Write-Host "  [kuru] $($f.Name) -> $tmp" }
  $moved++
}
Write-Host "  tasinan: $moved / 78"

Write-Host "== Faz 1b: eslesmeyen dosyalar =="
$extra = 0
foreach ($f in Get-ChildItem -File) {
  if ($null -eq (Get-Num $f.Name)) { continue }
  if ($PSCmdlet.ShouldProcess($f.Name, "-> kullanilmayan")) {
    New-Item -ItemType Directory -Force -Path "kullanilmayan" | Out-Null
    Move-Item -LiteralPath $f.FullName -Destination "kullanilmayan"
  } else { Write-Host "  [kuru] kullanilmayan\ -> $($f.Name)" }
  $extra++
}
if ($extra -eq 0) { Write-Host "  yok" }

Write-Host "== Faz 2: nihai adlar =="
foreach ($f in Get-ChildItem -File -Filter "tmp_*") {
  $final = $f.Name.Substring(4)
  if ($PSCmdlet.ShouldProcess($f.Name, "-> $final")) { Rename-Item -LiteralPath $f.FullName -NewName $final }
  else { Write-Host "  [kuru] $($f.Name) -> $final" }
}

Write-Host ""
Write-Host "Bitti. Eksik kalan numaralar (yeni uretilecek): 05 30 31 35 58"
Write-Host "Tamamlandiginda klasorde tam 83 dosya olmali."
Pop-Location
