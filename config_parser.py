# -*- coding: utf-8 -*-
import sys
import re
import json
import math

# Определение токенов для лексера
TOKEN_SPEC = [
    ('COMMENT',     r'\*>\s.*'),          # Однострочные комментарии
    ('VAR',         r'var\b'),            # Объявление переменной
    ('CONST_EXPR',  r'\?\{'),             # Начало константного выражения
    ('END_EXPR',    r'\}'),               # Конец константного выражения
    ('DICT_START',  r'\$\['),             # Начало словаря
    ('DICT_END',    r'\]'),               # Конец словаря
    ('COLON',       r':'),                # Двоеточие
    ('COMMA',       r','),                # Запятая
    ('STRING',      r'\'[^\']*\''),       # Строки в одинарных кавычках
    ('NUMBER',      r'\d+(\.\d+)?'),      # Числа (целые и с плавающей точкой)
    ('TRUE',        r'\btrue\b'),         # Булевое значение true
    ('FALSE',       r'\bfalse\b'),        # Булевое значение false
    ('IDENT',       r'[a-zA-Z_]\w*'),     # Идентификаторы
    ('OP',          r'[\+\-\*/]'),        # Операторы +, -, *, /
    ('LPAREN',      r'\('),               # Открывающая скобка (
    ('RPAREN',      r'\)'),               # Закрывающая скобка )
    ('SKIP',        r'[ \t]+'),           # Пробелы и табуляции
    ('NEWLINE',     r'\n'),               # Перенос строки
    ('MISMATCH',    r'.'),                # Любой другой символ
]

# Класс токена
from collections import namedtuple
Token = namedtuple('Token', ['type', 'value', 'line', 'column'])

# Лексер
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

# Парсер
class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0
        self.variables = {}
        self.ast = []

    def parse(self):
        while self.current_token():
            stmt = self.statement()
            if stmt is not None:
                self.ast.append(stmt)
        return self.ast

    def current_token(self):
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return None

    def match(self, *token_types):
        token = self.current_token()
        if token and token.type in token_types:
            self.pos += 1
            return token
        return None

    def statement(self):
        if self.match('VAR'):
            self.variable_declaration()
            return None
        elif self.match('DICT_START'):
            self.pos -= 1  # Возвращаемся назад для корректной обработки словаря
            value = self.value()
            return value
        elif self.match('CONST_EXPR'):
            expr = self.expression()
            if not self.match('END_EXPR'):
                token = self.current_token()
                if token:
                    raise SyntaxError(f'Ожидалась закрывающая скобка }} для константного выражения в строке {token.line}')
                else:
                    raise SyntaxError('Ожидалась закрывающая скобка } для константного выражения')
            self.evaluate_expression(expr)
            return None
        else:
            token = self.current_token()
            if token and token.type in ('COMMENT', 'NEWLINE'):
                self.pos += 1
                return None
            elif token:
                raise SyntaxError(f'Неожиданный токен {token.value!r} в строке {token.line}')
            else:
                return None

    def variable_declaration(self):
        ident = self.match('IDENT')
        if not ident:
            raise SyntaxError('Ожидалось имя переменной после ключевого слова var')
        value = self.value()
        evaluated_value = self.evaluate_value(value)
        self.variables[ident.value] = evaluated_value

    def value(self):
        token = self.current_token()
        if not token:
            raise SyntaxError('Ожидалось значение, но достигнут конец ввода')
        if token.type == 'NUMBER':
            self.pos += 1
            return float(token.value) if '.' in token.value else int(token.value)
        elif token.type == 'STRING':
            self.pos += 1
            return token.value[1:-1]  # Удаляем одинарные кавычки
        elif token.type == 'TRUE':
            self.pos += 1
            return True
        elif token.type == 'FALSE':
            self.pos += 1
            return False
        elif token.type == 'IDENT':
            if self.lookahead('LPAREN'):
                return self.function_call()
            else:
                self.pos += 1
                return {'var_ref': token.value}
        elif token.type == 'DICT_START':
            return self.dictionary()
        elif token.type == 'CONST_EXPR':
            self.pos += 1
            expr = self.expression()
            if not self.match('END_EXPR'):
                token = self.current_token()
                if token:
                    raise SyntaxError(f'Ожидалась закрывающая скобка }} для константного выражения в строке {token.line}')
                else:
                    raise SyntaxError('Ожидалась закрывающая скобка } для константного выражения')
            result = self.evaluate_expression(expr)
            return result
        else:
            raise SyntaxError(f'Недопустимое значение в строке {token.line}')

    def dictionary(self):
        if not self.match('DICT_START'):
            token = self.current_token()
            if token:
                raise SyntaxError(f'Ожидалось $[ для начала словаря в строке {token.line}')
            else:
                raise SyntaxError('Ожидалось $[ для начала словаря')
        entries = {}
        while not self.match('DICT_END'):
            key_token = self.match('IDENT')
            if not key_token:
                raise SyntaxError('Ожидался ключ словаря')
            key = key_token.value
            if not self.match('COLON'):
                raise SyntaxError('Ожидалось : после ключа словаря')
            value = self.value()
            entries[key] = value
            if not self.match('COMMA'):
                if self.current_token() and self.current_token().type != 'DICT_END':
                    raise SyntaxError('Ожидалось , или ] в словаре')
                elif not self.current_token():
                    raise SyntaxError('Ожидался конец словаря ]')
        return entries

    def expression(self):
        node = self.term()
        while self.current_token() and self.current_token().type == 'OP':
            op = self.match('OP')
            right = self.term()
            node = (op.value, node, right)
        return node

    def term(self):
        token = self.current_token()
        if not token:
            raise SyntaxError('Ожидалось выражение, но достигнут конец ввода')
        if token.type == 'NUMBER':
            self.pos += 1
            return float(token.value) if '.' in token.value else int(token.value)
        elif token.type == 'STRING':
            self.pos += 1
            return token.value[1:-1]
        elif token.type == 'TRUE':
            self.pos += 1
            return True
        elif token.type == 'FALSE':
            self.pos += 1
            return False
        elif token.type == 'IDENT':
            if self.lookahead('LPAREN'):
                return self.function_call()
            else:
                self.pos += 1
                if token.value in self.variables:
                    return self.variables[token.value]
                else:
                    raise NameError(f'Неопределенная переменная {token.value}')
        elif token.type == 'LPAREN':
            self.pos += 1
            expr = self.expression()
            if not self.match('RPAREN'):
                raise SyntaxError('Ожидалась закрывающая скобка )')
            return expr
        else:
            raise SyntaxError(f'Недопустимый терм в строке {token.line}')

    def function_call(self):
        func_token = self.match('IDENT')
        func_name = func_token.value
        if not self.match('LPAREN'):
            raise SyntaxError(f'Ожидалась ( после имени функции {func_name}')
        args = []
        while not self.match('RPAREN'):
            arg = self.expression()
            args.append(arg)
            if not self.match('COMMA'):
                if not self.current_token() or self.current_token().type != 'RPAREN':
                    raise SyntaxError('Ожидалось , или ) в аргументах функции')
        return {'func_call': func_name, 'args': args}

    def lookahead(self, token_type):
        next_pos = self.pos + 1
        if next_pos < len(self.tokens):
            return self.tokens[next_pos].type == token_type
        return False

    def evaluate_value(self, value):
        if isinstance(value, dict):
            if 'var_ref' in value:
                var_name = value['var_ref']
                if var_name in self.variables:
                    return self.variables[var_name]
                else:
                    raise NameError(f'Неопределенная переменная {var_name}')
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

    def call_function(self, func_name, args):
        if func_name == 'pow':
            return math.pow(*args)
        elif func_name == 'print':
            print(*args, file=sys.stderr)
            return None
        else:
            raise NameError(f'Неизвестная функция {func_name}')

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

if __name__ == '__main__':
    main()
