@echo off
chcp 65001 >nul
echo ========================================
echo    GitHub Upload Script
echo ========================================
echo.

:: Проверяем, инициализирован ли git
if not exist ".git" (
    echo Инициализация Git репозитория...
    git init
    echo.
)

:: Запрашиваем ссылку на репозиторий
set /p repo_url="Введите ссылку на GitHub репозиторий: "

:: Проверяем формат ссылки и конвертируем если нужно
echo %repo_url% | findstr /C:"github.com" >nul
if errorlevel 1 (
    echo Ошибка: Неверная ссылка на GitHub репозиторий!
    pause
    exit /b 1
)

:: Конвертируем ссылку в правильный формат если это веб-ссылка
echo %repo_url% | findstr /C:".git" >nul
if errorlevel 1 (
    set "repo_url=%repo_url%.git"
)

echo.
echo Используемая ссылка: %repo_url%
echo.

:: Удаляем существующий remote если есть
git remote remove origin 2>nul

:: Добавляем новый remote
echo Добавление удаленного репозитория...
git remote add origin %repo_url%

:: Добавляем все файлы
echo Добавление файлов...
git add .

:: Создаем коммит
echo Создание коммита...
git commit -m "Upload project to GitHub"

:: Переименовываем ветку в main
echo Переименование ветки в main...
git branch -M main

:: Загружаем в репозиторий
echo Загрузка в GitHub...
git push -f origin main

if errorlevel 1 (
    echo.
    echo Ошибка при загрузке! Проверьте:
    echo - Правильность ссылки на репозиторий
    echo - Права доступа к репозиторию
    echo - Подключение к интернету
    pause
    exit /b 1
)

echo.
echo ========================================
echo    Проект успешно загружен на GitHub!
echo ========================================
echo.
pause