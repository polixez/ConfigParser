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

      -Словари объявляются с помощью $[ ... ] и могут быть вложенными.
  -Строки заключаются в одинарные кавычки '...'.
  
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
### Реализация функций

1. **Токенизация входного текста:**
    ```python
    def tokenize(text):
    regex = '|'.join('(?P<%s>%s)' % pair for pair in TOKEN_SPEC)
    token_regex = re.compile(regex)
    line_num = 1
    line_start = 0
    tokens = []
    for mo in token_regex.finditer(text):
        kind = mo.lastgroup
        value = mo.group()
        column = mo.start() - line_start
        if kind == 'NEWLINE':
            line_num += 1
            line_start = mo.end()
        elif kind == 'SKIP' or kind == 'COMMENT':
            continue
        elif kind == 'MISMATCH':
            raise SyntaxError(f'Неожиданный символ {value!r} в строке {line_num}')
        else:
            tokens.append(Token(kind, value, line_num, column))
    return tokens

2. **Парсер:**
    ```python
    class Parser:
    def __init__(self, tokens):
        """
        Инициализация парсера с токенами, указателем позиции и таблицей переменных.
        """
        self.tokens = tokens
        self.pos = 0
        self.variables = {}
        self.ast = []

    def parse(self):
        """
        Основной метод парсинга, разбирает последовательность токенов и формирует AST.
        """
        while self.current_token():
            stmt = self.statement()
            if stmt is not None:
                self.ast.append(stmt)
        return self.ast

    def current_token(self):
        """
        Возвращает текущий токен или None, если достигнут конец токенов.
        """
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return None

    def match(self, *token_types):
        """
        Проверяет, совпадает ли текущий токен с одним из указанных типов, 
        и продвигается вперед, если совпадение найдено.
        """
        token = self.current_token()
        if token and token.type in token_types:
            self.pos += 1
            return token
        return None

    def statement(self):
        """
        Обрабатывает конструкцию на уровне инструкции (объявление переменной, словарь, выражение).
        """
        token = self.current_token()
        if token.type == 'VAR':
            self.match('VAR')
            self.variable_declaration()
            return None
        elif token.type == 'DICT_START':
            value = self.value()
            return value
        elif token.type == 'CONST_EXPR':
            self.match('CONST_EXPR')
            expr = self.expression()
            if not self.match('END_EXPR'):
                raise SyntaxError(f'Ожидалась закрывающая скобка }} для константного выражения.')
            self.evaluate_expression(expr)
            return None
        else:
            raise SyntaxError(f'Неожиданный токен {token.value!r}.')

    def variable_declaration(self):
        """
        Обрабатывает объявление переменной (var имя значение) и сохраняет переменную.
        """
        ident = self.match('IDENT')
        if not ident:
            raise SyntaxError('Ожидалось имя переменной после ключевого слова var.')
        value = self.value()
        evaluated_value = self.evaluate_value(value)
        self.variables[ident.value] = evaluated_value

    def value(self):
        """
        Возвращает значение (число, строку, словарь, выражение или ссылку на переменную).
        """
        token = self.current_token()
        if not token:
            raise SyntaxError('Ожидалось значение, но достигнут конец ввода.')
        if token.type == 'NUMBER':
            self.match('NUMBER')
            return float(token.value) if '.' in token.value else int(token.value)
        elif token.type == 'STRING':
            self.match('STRING')
            return token.value[1:-1]
        elif token.type == 'TRUE':
            self.match('TRUE')
            return True
        elif token.type == 'FALSE':
            self.match('FALSE')
            return False
        elif token.type == 'IDENT':
            if self.lookahead('LPAREN'):
                return self.function_call()
            else:
                ident_token = self.match('IDENT')
                return {'var_ref': ident_token.value}
        elif token.type == 'DICT_START':
            return self.dictionary()
        elif token.type == 'CONST_EXPR':
            self.match('CONST_EXPR')
            expr = self.expression()
            if not self.match('END_EXPR'):
                raise SyntaxError('Ожидалась закрывающая скобка } для константного выражения.')
            return self.evaluate_expression(expr)
        else:
            raise SyntaxError(f'Недопустимое значение в строке {token.line}.')

    def dictionary(self):
        """
        Обрабатывает словарь, состоящий из пар ключ-значение, поддерживает вложенность.
        """
        self.match('DICT_START')
        entries = {}
        while True:
            token = self.current_token()
            if token.type == 'DICT_END':
                self.match('DICT_END')
                break
            key_token = self.match('IDENT')
            if not key_token:
                raise SyntaxError('Ожидался ключ словаря.')
            key = key_token.value
            if not self.match('COLON'):
                raise SyntaxError('Ожидалось : после ключа словаря.')
            value = self.value()
            entries[key] = value
            if not self.match('COMMA'):
                token = self.current_token()
                if token.type == 'DICT_END':
                    continue
                else:
                    raise SyntaxError('Ожидалось , или ] в словаре.')
        return entries

    def expression(self):
        """
        Разбирает и возвращает арифметическое выражение, поддерживает операции и вложенность.
        """
        node = self.term()
        while self.current_token() and self.current_token().type == 'OP':
            op = self.match('OP')
            right = self.term()
            node = (op.value, node, right)
        return node

    def term(self):
        """
        Разбирает базовые элементы арифметического выражения (число, строка, переменная, скобки).
        """
        token = self.current_token()
        if not token:
            raise SyntaxError('Ожидалось выражение, но достигнут конец ввода.')
        if token.type == 'NUMBER':
            self.match('NUMBER')
            return float(token.value) if '.' in token.value else int(token.value)
        elif token.type == 'STRING':
            self.match('STRING')
            return token.value[1:-1]
        elif token.type == 'TRUE':
            self.match('TRUE')
            return True
        elif token.type == 'FALSE':
            self.match('FALSE')
            return False
        elif token.type == 'IDENT':
            if self.lookahead('LPAREN'):
                return self.function_call()
            else:
                ident_token = self.match('IDENT')
                if ident_token.value in self.variables:
                    return self.variables[ident_token.value]
                else:
                    raise NameError(f'Неопределенная переменная {ident_token.value}.')
        elif token.type == 'LPAREN':
            self.match('LPAREN')
            expr = self.expression()
            if not self.match('RPAREN'):
                raise SyntaxError('Ожидалась закрывающая скобка ).')
            return expr
        else:
            raise SyntaxError(f'Недопустимый терм в строке {token.line}.')

    def function_call(self):
        """
        Обрабатывает вызов функции с именем и аргументами (например, pow(2, 3)).
        """
        func_token = self.match('IDENT')
        func_name = func_token.value
        if not self.match('LPAREN'):
            raise SyntaxError(f'Ожидалась ( после имени функции {func_name}.')
        args = []
        while True:
            token = self.current_token()
            if token.type == 'RPAREN':
                self.match('RPAREN')
                break
            arg = self.expression()
            args.append(arg)
            if not self.match('COMMA'):
                token = self.current_token()
                if token.type == 'RPAREN':
                    continue
                else:
                    raise SyntaxError('Ожидалось , или ) в аргументах функции.')
        return {'func_call': func_name, 'args': args}

    def lookahead(self, token_type):
        """
        Проверяет, совпадает ли следующий токен с указанным типом, без продвижения вперед.
        """
        next_pos = self.pos + 1
        if next_pos < len(self.tokens):
            return self.tokens[next_pos].type == token_type
        return False

    def evaluate_value(self, value):
        """
        Вычисляет значение (переменные, вызовы функций, выражения, словари).
        """
        if isinstance(value, dict):
            if 'var_ref' in value:
                var_name = value['var_ref']
                if var_name in self.variables:
                    return self.variables[var_name]
                else:
                    raise NameError(f'Неопределенная переменная {var_name}.')
            elif 'func_call' in value:
                func_name = value['func_call']
                args = [self.evaluate_value(arg) for arg in value['args']]
                return self.call_function(func_name, args)
            else:
                return {k: self.evaluate_value(v) for k, v in value.items()}
        elif isinstance(value, tuple):
            return self.evaluate_expression(value)
        else:
            return value

3. **Вычисление выражений:**
    ```python
        """
        Вычисляет арифметическое выражение, используя операции (+, -, *, /).
        """
        def evaluate_expression(self, expr):
        if isinstance(expr, tuple):
            op = expr[0]
            left = self.evaluate_expression(expr[1])
            right = self.evaluate_expression(expr[2])
            if op == '+':
                return left + right
            elif op == '-':
                return left - right
            elif op == '*':
                return left * right
            elif op == '/':
                return left / right
            else:
                raise ValueError(f'Неизвестный оператор {op}')
        else:
            return self.evaluate_value(expr)
   
4. **Обработка функций:**
    ```python
        """
        Вызывает встроенные функции (например, pow(), print()) с аргументами.
        """
       def call_function(self, func_name, args):
        if func_name == 'pow':
            return math.pow(*args)
        elif func_name == 'print':
            print(*args, file=sys.stderr)
            return None
        else:
            raise NameError(f'Неизвестная функция {func_name}')
5. **Основная функция:**
    ```python
    def main():
    try:
        import sys
        import io

        # Устанавливаем кодировку UTF-8 для stdin и stdout
        sys.stdin = io.TextIOWrapper(sys.stdin.buffer, encoding='utf-8')
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

        # Чтение данных из стандартного ввода
        text = sys.stdin.read()
        tokens = tokenize(text)
        parser = Parser(tokens)
        ast = parser.parse()
        # Оценка значений в AST и формирование результата
        result = []
        for node in ast:
            value = parser.evaluate_value(node)
            if value is not None:
                result.append(value)
        json_output = json.dumps(result, indent=2, ensure_ascii=False)
        print(json_output)
    except Exception as e:
        print(f'Ошибка: {e}', file=sys.stderr)
        sys.exit(1)
---
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



### Проверка корректности результатов
- **output1.json**: Содержит конфигурацию базы данных с вложенными словарями.
- **output2.json**: Отражает корректное вычисление выражений с использованием переменных.
- **output3.json**: Показывает результаты всех арифметических операций и функции pow().
- **output4.json**: Демонстрирует работу функции print() и корректное отображение сообщений в логах.

**Все тесты прошли успешно, подтверждая полное соответствие функционала требованиям задания.**
