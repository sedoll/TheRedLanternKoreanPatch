@echo off
chcp 65001 >nul
setlocal
echo ==============================================
echo  The Red Lantern 한글패치 제거
echo ==============================================
set "GAME=%~1"
if "%GAME%"=="" set "GAME=%CD%"
if not exist "%GAME%\TheRedLantern_sw.exe" (
  set /p "GAME=TheRedLantern_sw.exe 가 있는 게임 폴더 경로를 입력하세요: "
)
set "GAME=%GAME:"=%"
set "D=TheRedLantern_sw_Data\StreamingAssets"
set "BK=%GAME%\KoreanPatch_Backup"
if not exist "%BK%\TheRedLantern_v001-Built.twig" (
  echo [오류] 백업 파일이 없습니다. Steam에서 "게임 파일 무결성 확인"으로 원본을 복구하세요.
  pause & exit /b 1
)
copy /y "%BK%\TheRedLantern_v001-Built.twig" "%GAME%\%D%\Flume\" >nul
copy /y "%BK%\managers_and_interfaces_assets_guimanager.bundle" "%GAME%\%D%\aa\StandaloneWindows64\" >nul
echo 원본으로 복구했습니다.
pause
