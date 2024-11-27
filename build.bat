@echo off
chcp 65001 >nul
REM Скрипт для автоматической сборки проекта и проверки тестов

echo Сборка проекта...

set PYTHON_PATH=py

%PYTHON_PATH% --version >nul 2>&1
IF ERRORLEVEL 1 (
    echo Ошибка: Python не найден или не добавлен в PATH.
    goto end
)

echo Проверка синтаксиса скрипта...
%PYTHON_PATH% -m py_compile config_parser.py
IF ERRORLEVEL 1 (
    echo Ошибка: Обнаружены ошибки в синтаксисе скрипта.
    goto end
)

echo Тестирование с input.txt...
type input.txt | %PYTHON_PATH% config_parser.py > output.json 2>&1

echo Тестирование с input2.txt...
type input2.txt | %PYTHON_PATH% config_parser.py > output2.json 2>&1

echo Тестирование с input3.txt...
type input3.txt | %PYTHON_PATH% config_parser.py > output3.json 2>&1

echo Тестирование с input4.txt...
type input4.txt | %PYTHON_PATH% config_parser.py > output4.json 2>&1

echo Сборка и тестирование завершены успешно.

:end
