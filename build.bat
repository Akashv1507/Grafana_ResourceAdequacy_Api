
pyinstaller ^
  --clean ^
  --collect-all numpy ^
  --collect-all pandas ^
  --hidden-import=numpy ^
  --hidden-import=pandas ^
  server.py


xcopy /s /i /y "config" "dist/server/config"