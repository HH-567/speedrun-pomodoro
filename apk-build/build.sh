#!/bin/bash
# 一键构建 APK（aapt2 + javac + d8 + zipalign + apksigner，不依赖 Gradle）
set -e

ROOT="$(cd "$(dirname "$0")" && pwd -W)"
TC="$ROOT/tools"
BT="$TC/sdk/build-tools"
PLAT="$TC/sdk/platform/android.jar"
JDK="$TC/jdk17/bin"
OUT="$ROOT/out"
KS="$(cd "$HOME" && pwd -W)/.android/debug.keystore"

if [ ! -f "$PLAT" ]; then
  echo "缺少 SDK，请先解压 tools 下的压缩包"; exit 1
fi

rm -rf "$OUT"
mkdir -p "$OUT/classes" "$OUT/dex"

echo "[1/7] 编译资源"
"$BT/aapt2.exe" compile --dir "$ROOT/res" -o "$OUT/res.zip"

echo "[2/7] 链接资源与 assets"
"$BT/aapt2.exe" link -o "$OUT/base.apk" -I "$PLAT" \
    --manifest "$ROOT/AndroidManifest.xml" -A "$ROOT/assets" "$OUT/res.zip"

echo "[3/7] 编译 Java"
find "$ROOT/src" -name "*.java" > "$OUT/sources.txt"
"$JDK/javac.exe" -encoding UTF-8 -source 8 -target 8 \
    -bootclasspath "$PLAT" -classpath "$PLAT" \
    -d "$OUT/classes" @"$OUT/sources.txt"

echo "[4/7] 转为 dex"
find "$OUT/classes" -name "*.class" > "$OUT/classes.txt"
"$JDK/java.exe" -cp "$BT/lib/d8.jar" com.android.tools.r8.D8 \
    --lib "$PLAT" --min-api 21 --release \
    --output "$OUT/dex" $(cat "$OUT/classes.txt")

echo "[5/7] 打包 dex"
(cd "$OUT/dex" && "$JDK/jar.exe" uf "$OUT/base.apk" classes.dex)

echo "[6/7] 对齐"
"$BT/zipalign.exe" -f -p 4 "$OUT/base.apk" "$OUT/aligned.apk"

echo "[7/7] 签名"
"$JDK/java.exe" -jar "$BT/lib/apksigner.jar" sign \
    --ks "$KS" \
    --ks-pass pass:android --key-pass pass:android \
    --ks-key-alias androiddebugkey --min-sdk-version 21 \
    --out "$OUT/tomato.apk" "$OUT/aligned.apk"

echo
echo "构建完成: $OUT/tomato.apk"
ls -la "$OUT/tomato.apk"
