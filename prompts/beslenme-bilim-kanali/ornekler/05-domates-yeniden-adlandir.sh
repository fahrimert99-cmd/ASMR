#!/usr/bin/env bash
# Domates videosu - gorselleri 83 bloklu SRT numaralandirmasina tasir.
# Kullanim:  ./05-domates-yeniden-adlandir.sh [klasor] [--dry-run]
#
# Eski numaralandirma cumle bazliydi (1-80). ElevenLabs bazi cumleleri bolup
# bazilarini birlestirince SRT 83 blok verdi. Bu betik mevcut 78 dosyayi yeni
# blok numarasina tasir; eslesmeyen dosyalari silmez, "kullanilmayan/" altina
# alir. Kalan 5 numara (05, 30, 31, 35, 58) yeni uretilecek gorseller icindir.
set -euo pipefail

DIR="${1:-.}"
DRY=0
for a in "$@"; do [ "$a" = "--dry-run" ] && DRY=1; done
[ -d "$DIR" ] || { echo "klasor yok: $DIR" >&2; exit 1; }
cd "$DIR"

declare -A MAP
MAP[2]=1
MAP[3]=2
MAP[4]=3
MAP[5]=4
MAP[6]=6
MAP[7]=7
MAP[8]=8
MAP[9]=9
MAP[10]=10
MAP[11]=11
MAP[12]=12
MAP[13]=13
MAP[14]=14
MAP[15]=15
MAP[16]=16
MAP[17]=17
MAP[18]=18
MAP[19]=19
MAP[21]=20
MAP[22]=21
MAP[23]=22
MAP[24]=23
MAP[25]=24
MAP[26]=25
MAP[27]=26
MAP[28]=27
MAP[29]=28
MAP[30]=29
MAP[31]=32
MAP[32]=33
MAP[33]=34
MAP[34]=36
MAP[35]=37
MAP[36]=38
MAP[37]=39
MAP[38]=40
MAP[39]=41
MAP[40]=42
MAP[41]=43
MAP[42]=44
MAP[43]=45
MAP[44]=46
MAP[45]=47
MAP[46]=48
MAP[47]=49
MAP[48]=50
MAP[49]=51
MAP[50]=52
MAP[51]=53
MAP[52]=54
MAP[53]=55
MAP[54]=56
MAP[55]=57
MAP[56]=59
MAP[57]=60
MAP[58]=61
MAP[59]=62
MAP[60]=63
MAP[61]=64
MAP[62]=65
MAP[63]=66
MAP[64]=67
MAP[65]=68
MAP[66]=69
MAP[67]=70
MAP[68]=71
MAP[69]=72
MAP[70]=73
MAP[71]=74
MAP[72]=75
MAP[73]=76
MAP[74]=77
MAP[75]=78
MAP[76]=79
MAP[77]=80
MAP[78]=81
MAP[79]=82
MAP[80]=83

say() { if [ "$DRY" = 1 ]; then echo "  [kuru] $*"; else echo "  $*"; fi; }
mv_() { if [ "$DRY" = 0 ]; then mv -n -- "$1" "$2"; fi; }

pad() { printf '%02d' "$1"; }

echo "== Faz 1: gecici adlara =="
moved=0
for old in "${!MAP[@]}"; do
  new="${MAP[$old]}"
  for f in $(pad "$old").* "$old".*; do
    [ -e "$f" ] || continue
    ext="${f##*.}"
    say "$f -> tmp_$(pad "$new").$ext"
    mv_ "$f" "tmp_$(pad "$new").$ext"
    moved=$((moved+1))
    break
  done
done
echo "  tasinan: $moved / 78"

echo "== Faz 1b: eslesmeyen dosyalar =="
extra=0
for f in [0-9][0-9].* [0-9].*; do
  [ -e "$f" ] || continue
  base="${f%%.*}"; num=$((10#$base))
  # kuru calismada Faz 1 dosyalari yerinde biraktigi icin eslesenleri atla
  [ "$DRY" = 1 ] && [ -n "${MAP[$num]+x}" ] && continue
  say "kullanilmayan/ -> $f"
  if [ "$DRY" = 0 ]; then mkdir -p kullanilmayan; mv -n -- "$f" kullanilmayan/; fi
  extra=$((extra+1))
done
[ "$extra" = 0 ] && echo "  yok"

echo "== Faz 2: nihai adlar =="
for f in tmp_*; do
  [ -e "$f" ] || continue
  say "$f -> ${f#tmp_}"
  mv_ "$f" "${f#tmp_}"
done

echo
echo "Bitti. Eksik kalan numaralar (yeni uretilecek): 05 30 31 35 58"
echo "Tamamlandiginda klasorde tam 83 dosya olmali."
