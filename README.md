# Инструмент для обработки конфигурационного языка (ConfigParser)

---

## 1. Общее описание
Данный проект реализует инструмент командной строки для преобразования текста из учебного конфигурационного языка в формат JSON. Инструмент принимает входной текст из стандартного ввода и выводит результат в стандартный вывод, осуществляя вычисления константных выражений на этапе трансляции и выявляя синтаксические ошибки с сообщениями.

Конфигурационный язык поддерживает различные конструкции, включая объявления переменных, вычисление выражений, словари и строки. Проект включает тесты, покрывающие все конструкции языка.

---

## 2. Функции и настройки
### Основные функции
- **Преобразование конфигураций в JSON:**

    - Парсинг входного текста на учебном конфигурационном языке.
    - Вывод результата в формате JSON с сохранением структуры данных.

- **Обработка константных выражений**:

  - Вычисление выражений, заключённых в ?{} на этапе трансляции.
  - Поддержка арифметических операций: +, -, *, /.
  - Поддержка функций: pow(), print().
- **Объявление переменных:**

    - Использование ключевого слова var для объявления констант на этапе трансляции.
  - **Поддержка словарей и строк:** 

      - Словари объявляются с помощью $[ ... ] и могут быть вложенными.
  - Строки заключаются в одинарные кавычки '...'.
  
### Пример синтаксиса
````
  *> Однострочный комментарий
  var имя значение
  $[
    ключ1 : значение1,
    ключ2 : $[
      вложенный_ключ : вложенное_значение
    ],
    ключ3 : ?{ выражение }
  ]
 ````

### Основные компоненты

1. **Парсер (```config_parser.py```)**

- Цель: Переводит исходный код программы на языке ассемблера УВМ в бинарный файл (```binary.bin```) и создает лог-файл (```log.xml```) с информацией об инструкциях.


2. **Файл-скрипт для автоматической сборки (```build.py```)**

- Цель: Автоматизирует процесс сборки и выполнения программы, последовательной проверки тестов.

## 3. Команды для сборки проекта
Для автоматической сборки проекта используется скрипт ```build.bat```.

### Сборка и запуск тестов:
1. **Запуск сборки через ```build.bat```:**

    ```batch
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

Скрипт выполняет следующие действия:
- Проверяет наличие интерпретатора Python.
- Проверяет синтаксис скрипта ```config_parser.py```.
- Выполняет тесты с использованием входных файлов ```input.txt```, ```input2.txt```, ```input3.txt```, ```input4.txt```.
- Результаты сохраняются в директорию ```outputs```.

2. **Структура директории outputs:**

- output1.json, output2.json, ... — файлы с результатами в формате JSON.
- output1.err, output2.err, ... — файлы с выводом ошибок и сообщений print().

---

## 4. Примеры использования

### Пример 1: Конфигурация базы данных
**Входной файл ```input.txt```:**

```plaintext
*> Конфигурация базы данных
var timeout 30
$[
  host : 'localhost',
  port : 5432,
  credentials : $[
    user : 'admin',
    pass : 'secret'
  ],
  options : $[
    timeout : ?{ timeout },
    ssl : true
  ]
]
```
**Команда для запуска:**

```batch
py config_parser.py < input.txt > outputs\output1.json 2> outputs\output1.err
```
**Результат (outputs\output1.json):**

![image](https://github.com/user-attachments/assets/a5fd6ea9-941d-440b-b804-28ef854ca534)

### Пример 2: Конфигурация графического интерфейса
**Входной файл ```input2.txt```:**

```plaintext
*> Конфигурация графического интерфейса
var baseWidth 800
var baseHeight 600
var scaleFactor 1.5

$[
  window : $[
    width : ?{ baseWidth * scaleFactor },
    height : ?{ baseHeight * scaleFactor }
  ],
  colors : $[
    background : 'white',
    foreground : 'black'
  ],
  title : 'Мое приложение'
]
```
**Команда для запуска:**

```batch
py config_parser.py < input2.txt > outputs\output2.json 2> outputs\output2.err
```
**Результат (outputs\output2.json):**

![image](https://github.com/user-attachments/assets/bdb242b2-8adb-455e-af86-463a4dbc1567)

### Пример 3: Использование всех операций и функции ```pow()```
**Входной файл ```input3.txt```:**

```plaintext
*> Конфигурация вычислений
var baseValue 10
var increment 5
var multiplier 2
var exponent 3

$[
  calculation : $[
    addition : ?{ baseValue + increment },
    subtraction : ?{ baseValue - increment },
    multiplication : ?{ baseValue * multiplier },
    division : ?{ baseValue / multiplier },
    power : ?{ pow(baseValue, exponent) }
  ]
]
```
**Команда для запуска:**

```batch
py config_parser.py < input3.txt > outputs\output3.json 2> outputs\output3.err
```
**Результат (outputs\output3.json):**

![image](https://github.com/user-attachments/assets/e3c6cd62-13af-4b27-b2d6-19c3dab0fa8b)

### Пример 4: Использование функции ```print()``` и вложенных словарей
**Входной файл ```input4.txt```:**

```plaintext
*> Конфигурация системы логирования
var logLevel 1
var logMessage 'Системное сообщение'

?{ print('Уровень логирования:', logLevel) }
?{ print('Сообщение:', logMessage) }

$[
  logging : $[
    level : ?{ logLevel },
    messages : $[
      system : ?{ logMessage },
      error : 'Ошибка системы'
    ]
  ]
]
```
**Команда для запуска:**

```batch
py config_parser.py < input4.txt > outputs\output4.json 2> outputs\output4.err
```
**Результат (outputs\output4.json):**

![image](https://github.com/user-attachments/assets/eb941c84-2df7-4908-9882-622cd2ad7ee5)

![image](https://github.com/user-attachments/assets/36ea4139-ccb4-4e0f-b658-bcf3a63bc3ba)

---

## 5. Результаты прогона тестов
**Все тестовые файлы успешно обработаны, что подтверждает корректность работы всех функций парсера.**

**Вывод сборки и тестирования (```build.bat```):**

![image](https://github.com/user-attachments/assets/91ca9a74-d5e5-41f1-b4f5-e2c4703d5fe8)


### Проверка корректности результатов
- **output1.json**: Содержит конфигурацию базы данных с вложенными словарями.
- **output2.json**: Отражает корректное вычисление выражений с использованием переменных.
- **output3.json**: Показывает результаты всех арифметических операций и функции pow().
- **output4.json**: Демонстрирует работу функции print() и корректное отображение сообщений в логах.

**Все тесты прошли успешно, подтверждая полное соответствие функционала требованиям задания.**
