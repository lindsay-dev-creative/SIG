#!/usr/bin/env bash
# Cut the five Heirloom shots into one silent showcase film.
# Usage: ./assemble.sh clips-4x3 heirloom-showcase-4x3.mp4
set -euo pipefail
cd "$(dirname "$0")"

SRC=$1
OUT=$2
XF=0.6      # crossfade between shots (s)
HOLD=1.5    # freeze on the final hero frame for a logo/end card (s)
FADE_IN=0.8
FADE_OUT=1.2

inputs=()
durs=()
for n in 1 2 3 4 5; do
  f="$SRC/shot$n.mp4"
  inputs+=(-i "$f")
  durs+=("$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$f")")
done

# Normalise every clip, pad the last one with a held frame, then chain crossfades.
fc=""
for i in 0 1 2 3 4; do
  pad=""
  [ "$i" = 4 ] && pad=",tpad=stop_mode=clone:stop_duration=$HOLD"
  fc+="[$i:v]fps=24,format=yuv420p,setsar=1,settb=AVTB$pad[v$i];"
done

prev="v0"
offset=0
for i in 1 2 3 4; do
  offset=$(echo "$offset + ${durs[$((i-1))]} - $XF" | bc -l)
  fc+="[$prev][v$i]xfade=transition=fade:duration=$XF:offset=$offset[x$i];"
  prev="x$i"
done

total=$(echo "$offset + ${durs[4]} + $HOLD" | bc -l)
fo_start=$(echo "$total - $FADE_OUT" | bc -l)
fc+="[$prev]fade=t=in:st=0:d=$FADE_IN,fade=t=out:st=$fo_start:d=$FADE_OUT[out]"

ffmpeg -v error -y "${inputs[@]}" -filter_complex "$fc" -map "[out]" -an \
  -c:v libx264 -preset slow -crf 16 -pix_fmt yuv420p -movflags +faststart "$OUT"

printf '%s  %.1fs\n' "$OUT" "$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$OUT")"
