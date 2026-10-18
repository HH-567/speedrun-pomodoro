#!/bin/bash
cd "$(dirname "$0")"
dl(){ echo "[start] $2"; curl -L --fail --retry 3 --retry-delay 2 -o "$2" "$1" 2>"/tmp/err_$2.log" && echo "[done] $2 $(stat -c%s "$2") bytes" || echo "[FAIL] $2"; }
dl "https://dl.google.com/android/repository/build-tools_r34-windows.zip" build-tools.zip &
dl "https://dl.google.com/android/repository/platform-34-ext7_r03.zip" platform-34.zip &
dl "https://aka.ms/download-jdk/microsoft-jdk-17.0.11-windows-x64.zip" jdk17.zip &
wait
echo "=== ALL DONE ==="
ls -la
