"""生成 build.bat（纯 ASCII + CRLF），供用户双击重建 APK。"""

BAT = """@echo off
setlocal
set "ROOT=%~dp0"
set "ROOT=%ROOT:~0,-1%"
set "BT=%ROOT%\\tools\\sdk\\build-tools"
set "PLAT=%ROOT%\\tools\\sdk\\platform\\android.jar"
set "JDK=%ROOT%\\tools\\jdk17\\bin"
set "OUT=%ROOT%\\out"
set "KS=%USERPROFILE%\\.android\\debug.keystore"

if exist "%OUT%" rmdir /s /q "%OUT%"
mkdir "%OUT%\\classes" 2>nul
mkdir "%OUT%\\dex" 2>nul

echo [1/7] compiling resources ...
"%BT%\\aapt2.exe" compile --dir "%ROOT%\\res" -o "%OUT%\\res.zip"
if errorlevel 1 goto fail

echo [2/7] linking ...
"%BT%\\aapt2.exe" link -o "%OUT%\\base.apk" -I "%PLAT%" --manifest "%ROOT%\\AndroidManifest.xml" -A "%ROOT%\\assets" "%OUT%\\res.zip"
if errorlevel 1 goto fail

echo [3/7] compiling java ...
dir /s /b "%ROOT%\\src\\*.java" > "%OUT%\\sources.txt"
"%JDK%\\javac.exe" -encoding UTF-8 -source 8 -target 8 -bootclasspath "%PLAT%" -classpath "%PLAT%" -d "%OUT%\\classes" "@%OUT%\\sources.txt"
if errorlevel 1 goto fail

echo [4/7] dexing ...
dir /s /b "%OUT%\\classes\\*.class" > "%OUT%\\classes.txt"
"%JDK%\\java.exe" -cp "%BT%\\lib\\d8.jar" com.android.tools.r8.D8 --lib "%PLAT%" --min-api 21 --release --output "%OUT%\\dex" "@%OUT%\\classes.txt"
if errorlevel 1 goto fail

echo [5/7] packaging dex ...
pushd "%OUT%\\dex"
"%JDK%\\jar.exe" uf "%OUT%\\base.apk" classes.dex
popd
if errorlevel 1 goto fail

echo [6/7] aligning ...
"%BT%\\zipalign.exe" -f -p 4 "%OUT%\\base.apk" "%OUT%\\aligned.apk"
if errorlevel 1 goto fail

echo [7/7] signing ...
"%JDK%\\java.exe" -jar "%BT%\\lib\\apksigner.jar" sign --ks "%KS%" --ks-pass pass:android --key-pass pass:android --ks-key-alias androiddebugkey --min-sdk-version 21 --out "%OUT%\\tomato.apk" "%OUT%\\aligned.apk"
if errorlevel 1 goto fail

echo.
echo BUILD OK -^> %OUT%\\tomato.apk
if /i not "%1"=="/quiet" pause
exit /b 0

:fail
echo.
echo BUILD FAILED
if /i not "%1"=="/quiet" pause
exit /b 1
"""

with open('build.bat', 'w', encoding='ascii', newline='\r\n') as f:
    f.write(BAT)

d = open('build.bat', 'rb').read()
print('bytes:', len(d), 'CRLF:', d.count(b'\r\n'),
      'bare LF:', d.count(b'\n') - d.count(b'\r\n'),
      'non-ascii:', sum(1 for b in d if b > 127))
