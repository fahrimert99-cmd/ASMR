#!/usr/bin/env bash
# 5 yeni kare eklendiginde 40'lik numaralandirmayi 45'lige kaydirir.
# Yeni kareler: 33, 34, 43, 44, 45.  Eski 33-40 -> 35-42.
# Kullanim:  ./06-goji-40tan-45e.sh [klasor] [--dry-run]
set -euo pipefail
DIR="${1:-.}"; DRY=0
for x in "$@"; do [ "$x" = "--dry-run" ] && DRY=1; done
cd "$DIR"

declare -A MAP
for i in 33 34 35 36 37 38 39 40; do MAP[$i]=$((i+2)); done

echo "== Faz 1: gecici adlara =="
for old in "${!MAP[@]}"; do
  new="${MAP[$old]}"
  for f in $(printf '%02d' "$old").*; do
    [ -e "$f" ] || continue
    ext="${f##*.}"; t=$(printf 'tmp_%02d.%s' "$new" "$ext")
    if [ "$DRY" = 1 ]; then echo "  [kuru] $f -> $t"; else mv -n -- "$f" "$t"; fi
  done
done
echo "== Faz 2: nihai adlar =="
for f in tmp_*; do
  [ -e "$f" ] || continue
  if [ "$DRY" = 1 ]; then echo "  [kuru] $f -> ${f#tmp_}"; else mv -n -- "$f" "${f#tmp_}"; fi
done
echo
echo "Bos kalan numaralar (yeni uretilecek): 33 34 43 44 45"
