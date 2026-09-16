# Moskova gorsellerini 01.webp - 59.webp seklinde yeniden adlandirir.
# Kullanim: gorsellerin oldugu klasorde sag tik -> "Run with PowerShell"
# veya:  powershell -ExecutionPolicy Bypass -File yeniden-adlandir.ps1

Get-ChildItem -Filter "*.webp" | ForEach-Object {
    if ($_.Name -match '^(\d{1,3})[_\-]') {
        $n = [int]$Matches[1]
        $yeni = "{0:D2}.webp" -f $n
        if ($_.Name -ne $yeni) {
            Rename-Item -LiteralPath $_.FullName -NewName $yeni
            Write-Host "$($_.Name)  ->  $yeni"
        }
    }
}
Write-Host ""
Write-Host "Bitti. Dosya sayisi: $((Get-ChildItem -Filter '*.webp').Count)"
