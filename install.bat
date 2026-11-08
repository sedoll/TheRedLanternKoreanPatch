@echo off
chcp 65001 >nul
setlocal
echo ==============================================
echo  The Red Lantern 한글패치 설치
echo ==============================================
set "SRC=%~dp0patch"
set "GAME=%~1"
if "%GAME%"=="" set "GAME=%CD%"
if not exist "%GAME%\TheRedLantern_sw.exe" (
  echo 게임 폴더를 찾을 수 없습니다.
  set /p "GAME=TheRedLantern_sw.exe 가 있는 게임 폴더 경로를 입력하세요: "
)
set "GAME=%GAME:"=%"
if not exist "%GAME%\TheRedLantern_sw.exe" (
  echo [오류] "%GAME%" 에 TheRedLantern_sw.exe 가 없습니다.
  pause & exit /b 1
)
set "D=TheRedLantern_sw_Data\StreamingAssets"
set "BK=%GAME%\KoreanPatch_Backup"
if not exist "%BK%\TheRedLantern_v001-Built.twig" (
  mkdir "%BK%" 2>nul
  copy /y "%GAME%\%D%\Flume\TheRedLantern_v001-Built.twig" "%BK%\" >nul
  copy /y "%GAME%\%D%\aa\StandaloneWindows64\managers_and_interfaces_assets_guimanager.bundle" "%BK%\" >nul
  echo 원본 파일을 KoreanPatch_Backup 폴더에 백업했습니다.
)
copy /y "%SRC%\%D%\Flume\TheRedLantern_v001-Built.twig" "%GAME%\%D%\Flume\" >nul || goto :fail
copy /y "%SRC%\%D%\aa\StandaloneWindows64\managers_and_interfaces_assets_guimanager.bundle" "%GAME%\%D%\aa\StandaloneWindows64\" >nul || goto :fail
echo 설치가 완료되었습니다. 게임을 실행하세요.
pause & exit /b 0
:fail
echo [오류] 파일 복사에 실패했습니다. 게임이 실행 중이면 종료한 뒤 다시 시도하세요.
pause & exit /b 1
