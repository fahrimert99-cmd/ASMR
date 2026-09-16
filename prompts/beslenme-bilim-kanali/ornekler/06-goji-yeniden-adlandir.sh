#!/usr/bin/env bash
# Goji gorsellerini montaj aracinin bekledigi 01-40 adlandirmasina cevirir.
# Kullanim:  ./06-goji-yeniden-adlandir.sh [klasor] [--dry-run]
#
# Uretilen adlar "Gorsel_7__Oxygen_bubbles_..._20260916141619.jpeg" seklinde ve
# icinde Turkce karakter var. Moskova belgeselinde ad icindeki bir aksanli harf
# montaj aracinda "dosya bulunamadi" hatasi vermisti; bu yuzden adlar sadelesir.
set -euo pipefail
DIR="${1:-.}"; DRY=0
for x in "$@"; do [ "$x" = "--dry-run" ] && DRY=1; done
[ -d "$DIR" ] || { echo "klasor yok: $DIR" >&2; exit 1; }
cd "$DIR"

echo "== Faz 1: gecici adlara =="
found=0
for f in *; do
  [ -f "$f" ] || continue
  # ad icindeki "...rsel" den sonraki ilk sayi = gorsel numarasi
  num=$(printf '%s' "$f" | sed -n 's/.*rsel[_ ]*\([0-9]\{1,2\}\).*/\1/p')
  [ -n "$num" ] || { echo "  atlandi (numara okunamadi): $f"; continue; }
  ext="${f##*.}"
  new=$(printf 'tmp_%02d.%s' "$num" "$ext")
  if [ "$DRY" = 1 ]; then echo "  [kuru] $f -> $new"; else mv -n -- "$f" "$new"; fi
  found=$((found+1))
done
echo "  eslesen: $found"

echo "== Faz 2: nihai adlar =="
for f in tmp_*; do
  [ -e "$f" ] || continue
  if [ "$DRY" = 1 ]; then echo "  [kuru] $f -> ${f#tmp_}"; else mv -n -- "$f" "${f#tmp_}"; fi
done
echo
echo "Bitti. Klasorde 01..40 araliginda tam 40 dosya olmali."
