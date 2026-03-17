@echo off
chcp 65001 > nul
echo ========================================
echo   Doc Converter — сборка EXE
echo ========================================
echo.

:: Проверяем PyInstaller
python -m PyInstaller --version > nul 2>&1
if errorlevel 1 (
    echo [!] PyInstaller не найден. Устанавливаем...
    pip install pyinstaller
)

:: Очищаем предыдущую сборку
if exist "dist\DocConverter.exe" (
    echo [*] Удаляем предыдущую сборку...
    del /q "dist\DocConverter.exe"
)
if exist "build" rmdir /s /q build

:: Запускаем сборку
echo [*] Запускаем PyInstaller...
python -m PyInstaller doc_converter.spec --noconfirm

if errorlevel 1 (
    echo.
    echo [!] Сборка завершилась с ошибкой.
    pause
    exit /b 1
)

echo.
echo [OK] Готово! Файл: dist\DocConverter.exe
echo.

:: Открываем папку dist
explorer dist

pause
