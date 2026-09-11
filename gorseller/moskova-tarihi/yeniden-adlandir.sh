#!/usr/bin/env bash
# Moskova gorsellerini 01.webp - 59.webp seklinde yeniden adlandirir.
# Kullanim: gorsellerin oldugu klasorde  bash yeniden-adlandir.sh
set -e
for f in *.webp; do
  n=$(printf '%s' "$f" | sed -E 's/^0*([0-9]{1,3})[_-].*/\1/')
  [ "$n" = "$f" ] && continue
  yeni=$(printf '%02d.webp' "$n")
  [ "$f" = "$yeni" ] || { mv -- "$f" "$yeni"; echo "$f -> $yeni"; }
done
echo "Bitti. Dosya sayisi: $(ls -1 *.webp | wc -l)"
