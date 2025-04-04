#!/usr/bin/env python3

import sys
import os
from lark import Lark, Transformer, v_args, Token
from lark.exceptions import UnexpectedToken, UnexpectedCharacters

class Type:
    INT = "int"
    FLOAT = "float"
    STRING = "string"
    BOOLEAN = "boolean"
    ERROR = "error"

    @staticmethod
    def is_numeric(type_name):
        return type_name == Type.INT or type_name == Type.FLOAT

    @staticmethod
    def get_result_type(left_type, right_type, operator):
        if operator in ['+', '-', '*', '/']:
            if left_type == Type.ERROR or right_type == Type.ERROR:
                return Type.ERROR
            elif left_type == Type.STRING and right_type == Type.STRING and operator == '+':
                return Type.STRING
            elif not (Type.is_numeric(left_type) and Type.is_numeric(right_type)):
                if operator == '+' and (left_type == Type.STRING or right_type == Type.STRING):
                     return Type.STRING
                return Type.ERROR
            elif left_type == Type.FLOAT or right_type == Type.FLOAT:
                return Type.FLOAT
            else:
                return Type.INT
        elif operator in ['==', '!=', '<', '>', '<=', '>=', '&&', '||']:
            if left_type == Type.ERROR or right_type == Type.ERROR:
                return Type.ERROR
            elif operator in ['==', '!=']:
                if (Type.is_numeric(left_type) and Type.is_numeric(right_type)) or \
                   (left_type == Type.BOOLEAN and right_type == Type.BOOLEAN) or \
                   (left_type == Type.STRING and right_type == Type.STRING):
                    return Type.BOOLEAN
                else:
                    return Type.ERROR
            elif operator in ['<', '>', '<=', '>=']:
                if Type.is_numeric(left_type) and Type.is_numeric(right_type):
                    return Type.BOOLEAN
                elif left_type == Type.STRING and right_type == Type.STRING:
                     return Type.BOOLEAN
                else:
                    return Type.ERROR
            elif operator in ['&&', '||']:
                if left_type == Type.BOOLEAN and right_type == Type.BOOLEAN:
                    return Type.BOOLEAN
                else:
                    return Type.ERROR

        return Type.ERROR

class SemanticError(Exception):
    def __init__(self, message, line=None, column=None):
        super().__init__(message)
        self.line = line
        self.column = column

    def __str__(self):
        if self.line and self.column:
            return f"Error semántico en línea {self.line}, columna {self.column}: {super().__str__()}"
        else:
            return f"Error semántico: {super().__str__()}"

class SymbolTable:
    def __init__(self):
        self.scopes = [{}]

    def enter_scope(self):
        self.scopes.append({})

    def exit_scope(self):
        if len(self.scopes) > 1:
            self.scopes.pop()

    def declare(self, name, type_val, node=None):
        token = name
        name_str = name.value if isinstance(name, Token) else str(name)

        if name_str in self.scopes[-1]:
            line = token.line if isinstance(token, Token) else None
            col = token.column if isinstance(token, Token) else None
            raise SemanticError(f"Variable '{name_str}' ya declarada en este ámbito", line, col)
        self.scopes[-1][name_str] = {'type': type_val, 'node': node}

    def lookup(self, name):
        token = name
        name_str = name.value if isinstance(name, Token) else str(name)

        for scope in reversed(self.scopes):
            if name_str in scope:
                return scope[name_str]['type']
        line = token.line if isinstance(token, Token) else None
        col = token.column if isinstance(token, Token) else None
        raise SemanticError(f"Variable '{name_str}' no declarada", line, col)

    def update(self, name, type_val, node=None):
        token = name
        name_str = name.value if isinstance(name, Token) else str(name)

        for scope in reversed(self.scopes):
            if name_str in scope:
                return
        line = token.line if isinstance(token, Token) else None
        col = token.column if isinstance(token, Token) else None
        raise SemanticError(f"Variable '{name_str}' no declarada antes de la asignación", line, col)

class ASTNode:
     pass

class Program(ASTNode):
    def __init__(self, statements):
        self.statements = statements

class VarDeclaration(ASTNode):
    def __init__(self, name_token, initial_value=None):
        self.name_token = name_token
        self.name = name_token.value
        self.initial_value = initial_value

class Assignment(ASTNode):
    def __init__(self, name_token, value):
        self.name_token = name_token
        self.name = name_token.value
        self.value = value

class IfStatement(ASTNode):
    def __init__(self, condition, then_branch, else_branch=None):
        self.condition = condition
        self.then_branch = then_branch
        self.else_branch = else_branch

class WhileLoop(ASTNode):
    def __init__(self, condition, body):
        self.condition = condition
        self.body = body

class ForLoop(ASTNode):
    def __init__(self, init, condition, update, body):
        self.init = init
        self.condition = condition
        self.update = update
        self.body = body

class PrintStatement(ASTNode):
    def __init__(self, expressions):
        self.expressions = expressions

class InputStatement(ASTNode):
    def __init__(self, variable_token):
        self.variable_token = variable_token
        self.variable = variable_token.value

class Block(ASTNode):
    def __init__(self, statements):
        self.statements = statements

class BinaryOp(ASTNode):
    def __init__(self, left, operator_token, right):
        self.left = left
        self.operator_token = operator_token
        self.operator = operator_token.value
        self.right = right

class UnaryOp(ASTNode):
    def __init__(self, operator_token, operand):
        self.operator_token = operator_token
        self.operator = operator_token.value
        self.operand = operand

class Literal(ASTNode):
    def __init__(self, value, type_val, token):
        self.value = value
        self.type = type_val
        self.token = token

class Variable(ASTNode):
    def __init__(self, name_token):
        self.name_token = name_token
        self.name = name_token.value

class FunctionCall(ASTNode):
    def __init__(self, name_token, arguments):
        self.name_token = name_token
        self.name = name_token.value
        self.arguments = arguments

@v_args(inline=True)
class MiniLangTransformer(Transformer):
    def __init__(self):
        super().__init__()

    def NAME(self, token):
        return token

    def NUMBER(self, token):
        try:
            value = int(token.value)
            return Literal(value, Type.INT, token)
        except ValueError:
            value = float(token.value)
            return Literal(value, Type.FLOAT, token)

    def STRING(self, token):
        value = token.value[1:-1].encode().decode('unicode_escape')
        return Literal(value, Type.STRING, token)

    def start(self, *statements):
        return Program([stmt for stmt in statements if stmt is not None])

    def var_declaration(self, name_token, *args):
        initial_value = None
        if args:
             initial_value = args[-1]
        return VarDeclaration(name_token, initial_value)

    def for_var_declaration(self, name_token, *args):
        initial_value = None
        if args:
            initial_value = args[-1]
        return VarDeclaration(name_token, initial_value)

    def assignment(self, name_token, value):
        return Assignment(name_token, value)

    def for_assignment(self, name_token, value):
        return Assignment(name_token, value)

    def if_statement(self, condition, then_branch, else_branch=None):
        return IfStatement(condition, then_branch, else_branch)

    def while_loop(self, condition, body):
        return WhileLoop(condition, body)

    def for_loop(self, init, condition, update, body):
        return ForLoop(init, condition, update, body)

    def print_statement(self, *expressions):
        actual_expressions = [expr for expr in expressions if isinstance(expr, ASTNode)]
        return PrintStatement(actual_expressions)

    def input_statement(self, name_token):
        return InputStatement(name_token)

    def block(self, *statements):
        return Block([stmt for stmt in statements if stmt is not None])

    def _handle_binary_or_passthrough(self, *args):
        if len(args) == 1:
            # Just a single expression, pass it through
            return args[0]
        elif len(args) == 2:
            # Handle the case where Lark passes (left_expr, [(op, right_expr), ...])
            left, second = args
            
            # Check if second is a Variable or other non-iterable object
            if isinstance(second, ASTNode) or not hasattr(second, '__iter__'):
                return left
            
            # If it's an empty list, return left
            if len(second) == 0:
                return left
                
            # Process all operations sequentially from left to right
            result = left
            for op_right in second:
                op_token, right = op_right
                if isinstance(op_token, Token):
                    result = BinaryOp(result, op_token, right)
                else:
                    raise TypeError(f"Binary operation expected Token as operator, got {type(op_token)}")
            
            return result
        elif len(args) == 3:
            # Handle the case of a single binary operation (left, op, right)
            left, op_token, right = args
            if isinstance(op_token, Token):
                return BinaryOp(left, op_token, right)
            else:
                raise TypeError(f"Binary operation expected Token as operator, got {type(op_token)}")
        else:
            raise TypeError(f"Binary operation transformer received unexpected number of arguments: {len(args)}")

    def or_expr(self, *args): return self._handle_binary_or_passthrough(*args)
    def and_expr(self, *args): return self._handle_binary_or_passthrough(*args)
    def equality(self, *args): return self._handle_binary_or_passthrough(*args)
    def comparison(self, *args): return self._handle_binary_or_passthrough(*args)
    def term(self, *args): return self._handle_binary_or_passthrough(*args)
    def factor(self, *args): return self._handle_binary_or_passthrough(*args)


    def unary(self, *args):
         if len(args) == 1:
             return args[0]
         elif len(args) == 2:
             op_token, operand = args
             if isinstance(op_token, Token) and op_token.value in ['!', '-']:
                  return UnaryOp(op_token, operand)
             else:
                 raise TypeError(f"Transformer 'unary' esperaba (Token Operador, Operando), recibió: ({type(op_token)}, {type(operand)})")
         else:
              raise TypeError(f"Transformer 'unary' recibió un número inesperado de argumentos: {len(args)}")

    def variable(self, name_token):
        return Variable(name_token)


    def function_call(self, name_token, *args):
         arguments = list(args)
         arguments = [arg for arg in arguments if arg is not None]
         return FunctionCall(name_token, arguments)

    def primary(self, node):
        if isinstance(node, Token) and node.type == 'NAME':
            return Variable(node)
        return node


class SemanticAnalyzer:
    def __init__(self):
        self.symbol_table = SymbolTable()
        self.errors = []
        self.current_node = None

    def analyze(self, ast):
        try:
            self._analyze_node(ast)
        except SemanticError as e:
            self.errors.append(str(e))
        except Exception as e:
             location = ""
             node_info = ""
             if self.current_node:
                 node_info = f" (Nodo: {type(self.current_node).__name__})"
                 token = None
                 if hasattr(self.current_node, 'token'): token = self.current_node.token
                 elif hasattr(self.current_node, 'name_token'): token = self.current_node.name_token
                 elif hasattr(self.current_node, 'operator_token'): token = self.current_node.operator_token

                 if token and hasattr(token, 'line') and hasattr(token, 'column'):
                     location = f" cerca de línea {token.line}, columna {token.column}"


             self.errors.append(f"Error interno del analizador{location}{node_info}: {e}")

        return len(self.errors) == 0

    def _analyze_node(self, node):
        if node is None: return
        original_node = self.current_node
        self.current_node = node

        method_name = '_analyze_' + type(node).__name__
        visitor = getattr(self, method_name, self._analyze_default)
        result = visitor(node)

        self.current_node = original_node
        return result

    def _analyze_default(self, node):
        pass

    def _analyze_Program(self, node):
        for stmt in node.statements:
            self._analyze_node(stmt)

    def _analyze_VarDeclaration(self, node):
        var_type = Type.INT
        if node.initial_value:
            expr_type = self._get_expression_type(node.initial_value)
            if expr_type != Type.ERROR:
                var_type = expr_type
            else:
                var_type = Type.ERROR

        if var_type != Type.ERROR:
             try:
                 self.symbol_table.declare(node.name_token, var_type, node)
             except SemanticError as e:
                 self.errors.append(str(e))


    def _analyze_Assignment(self, node):
        try:
            var_type = self.symbol_table.lookup(node.name_token)
            expr_type = self._get_expression_type(node.value)

            if var_type != Type.ERROR and expr_type != Type.ERROR:
                 if not self._is_assignment_compatible(var_type, expr_type):
                     token = node.name_token
                     line = token.line if token else '?'
                     col = token.column if token else '?'
                     self.errors.append(f"Error de tipo en línea {line}, col {col}: no se puede asignar tipo '{expr_type}' a variable '{node.name}' de tipo '{var_type}'")

        except SemanticError as e:
            self.errors.append(str(e))


    def _analyze_IfStatement(self, node):
        condition_type = self._get_expression_type(node.condition)
        if condition_type not in [Type.BOOLEAN, Type.INT, Type.FLOAT] and condition_type != Type.ERROR:
             token = getattr(node.condition, 'token', None) or getattr(node.condition, 'name_token', None) or getattr(node.condition, 'operator_token', None)
             line = token.line if token else '?'
             col = token.column if token else '?'
             self.errors.append(f"Error de tipo en línea {line}, col {col}: condición de if debe ser booleana o numérica, no '{condition_type}'")

        self._analyze_node(node.then_branch)
        if node.else_branch:
            self._analyze_node(node.else_branch)

    def _analyze_WhileLoop(self, node):
        condition_type = self._get_expression_type(node.condition)
        if condition_type not in [Type.BOOLEAN, Type.INT, Type.FLOAT] and condition_type != Type.ERROR:
             token = getattr(node.condition, 'token', None) or getattr(node.condition, 'name_token', None) or getattr(node.condition, 'operator_token', None)
             line = token.line if token else '?'
             col = token.column if token else '?'
             self.errors.append(f"Error de tipo en línea {line}, col {col}: condición de while debe ser booleana o numérica, no '{condition_type}'")

        self._analyze_node(node.body)

    def _analyze_ForLoop(self, node):
        self.symbol_table.enter_scope()

        if node.init:
            self._analyze_node(node.init)

        if node.condition:
            condition_type = self._get_expression_type(node.condition)
            if condition_type not in [Type.BOOLEAN, Type.INT, Type.FLOAT] and condition_type != Type.ERROR:
                token = getattr(node.condition, 'token', None) or getattr(node.condition, 'name_token', None) or getattr(node.condition, 'operator_token', None)
                line = token.line if token else '?'
                col = token.column if token else '?'
                self.errors.append(f"Error de tipo en línea {line}, col {col}: condición de for debe ser booleana o numérica, no '{condition_type}'")

        if node.update:
            self._get_expression_type(node.update)

        self._analyze_node(node.body)

        self.symbol_table.exit_scope()

    def _analyze_PrintStatement(self, node):
        for expr in node.expressions:
            self._get_expression_type(expr)

    def _analyze_InputStatement(self, node):
        try:
            var_type = self.symbol_table.lookup(node.variable_token)
        except SemanticError as e:
            self.errors.append(str(e))

    def _analyze_Block(self, node):
        self.symbol_table.enter_scope()
        for stmt in node.statements:
            self._analyze_node(stmt)
        self.symbol_table.exit_scope()

    def _get_expression_type(self, expr):
        original_node = self.current_node
        if expr is None: return Type.ERROR
        self.current_node = expr

        result_type = Type.ERROR

        try:
            if isinstance(expr, Literal):
                result_type = expr.type
            elif isinstance(expr, Variable):
                try:
                    result_type = self.symbol_table.lookup(expr.name_token)
                except SemanticError as e:
                    self.errors.append(str(e))
                    result_type = Type.ERROR
            elif isinstance(expr, BinaryOp):
                left_type = self._get_expression_type(expr.left)
                right_type = self._get_expression_type(expr.right)
                op = expr.operator

                if left_type != Type.ERROR and right_type != Type.ERROR:
                    op_result_type = Type.get_result_type(left_type, right_type, op)
                    if op_result_type == Type.ERROR:
                        token = expr.operator_token
                        line = token.line if token else '?'
                        col = token.column if token else '?'
                        self.errors.append(f"Error de tipo en línea {line}, col {col}: operador '{op}' incompatible con tipos '{left_type}' y '{right_type}'")
                        result_type = Type.ERROR
                    else:
                        result_type = op_result_type
                else:
                     result_type = Type.ERROR
            elif isinstance(expr, UnaryOp):
                operand_type = self._get_expression_type(expr.operand)
                op = expr.operator

                if operand_type != Type.ERROR:
                    if op == "!":
                        if operand_type == Type.BOOLEAN or Type.is_numeric(operand_type):
                            result_type = Type.BOOLEAN
                        else:
                            token = expr.operator_token
                            line = token.line if token else '?'
                            col = token.column if token else '?'
                            self.errors.append(f"Error de tipo en línea {line}, col {col}: operador '!' incompatible con tipo '{operand_type}'")
                            result_type = Type.ERROR
                    elif op == "-":
                        if Type.is_numeric(operand_type):
                            result_type = operand_type
                        else:
                            token = expr.operator_token
                            line = token.line if token else '?'
                            col = token.column if token else '?'
                            self.errors.append(f"Error de tipo en línea {line}, col {col}: operador '-' incompatible con tipo '{operand_type}'")
                            result_type = Type.ERROR
                    else:
                         result_type = Type.ERROR
                else:
                    result_type = Type.ERROR
            elif isinstance(expr, FunctionCall):
                arg_types = [self._get_expression_type(arg) for arg in expr.arguments]
                if Type.ERROR in arg_types:
                     result_type = Type.ERROR
                else:
                    if expr.name == "len":
                         if len(expr.arguments) != 1:
                             token = expr.name_token; line, col = (token.line, token.column) if token else ('?', '?')
                             self.errors.append(f"Error de argumento en línea {line}, col {col}: función 'len' espera 1 argumento, recibió {len(expr.arguments)}")
                             result_type = Type.ERROR
                         elif arg_types[0] != Type.STRING:
                             token = expr.name_token; line, col = (token.line, token.column) if token else ('?', '?')
                             self.errors.append(f"Error de tipo en línea {line}, col {col}: función 'len' espera un string, recibió '{arg_types[0]}'")
                             result_type = Type.ERROR
                         else:
                             result_type = Type.INT
                    else:
                         token = expr.name_token; line, col = (token.line, token.column) if token else ('?', '?')
                         self.errors.append(f"Error semántico en línea {line}, col {col}: función '{expr.name}' no definida")
                         result_type = Type.ERROR
            else:
                 self.errors.append(f"Error interno: Tipo de nodo de expresión desconocido: {type(expr).__name__}")
                 result_type = Type.ERROR

        finally:
            self.current_node = original_node

        return result_type


    def _is_assignment_compatible(self, var_type, expr_type):
        if var_type == expr_type:
            return True
        if var_type == Type.FLOAT and expr_type == Type.INT:
            return True
        return False


class IntermediateCodeGenerator:
    def __init__(self):
        self.code = []
        self.temp_counter = 0
        self.label_counter = 0

    def generate(self, ast):
        self._generate_node(ast)
        return self.code

    def _new_temp(self):
        temp = f"t{self.temp_counter}"
        self.temp_counter += 1
        return temp

    def _new_label(self):
        label = f"L{self.label_counter}"
        self.label_counter += 1
        return label

    def _generate_node(self, node):
        if node is None: return None
        method_name = '_generate_' + type(node).__name__
        visitor = getattr(self, method_name, self._generate_default)
        return visitor(node)

    def _generate_default(self, node):
        if hasattr(node, '__dict__'):
             for attr_name, attr_value in vars(node).items():
                 if isinstance(attr_value, ASTNode):
                     self._generate_node(attr_value)
                 elif isinstance(attr_value, list):
                     for item in attr_value:
                         if isinstance(item, ASTNode):
                             self._generate_node(item)
        return None


    def _generate_Program(self, node):
        for stmt in node.statements:
            self._generate_node(stmt)

    def _generate_VarDeclaration(self, node):
        if node.initial_value:
            expr_temp = self._generate_node(node.initial_value)
            if expr_temp:
                 self.code.append(f"ASSIGN {node.name}, {expr_temp}")

    def _generate_Assignment(self, node):
        expr_temp = self._generate_node(node.value)
        if expr_temp:
            self.code.append(f"ASSIGN {node.name}, {expr_temp}")

    def _generate_IfStatement(self, node):
        condition_temp = self._generate_node(node.condition)
        if not condition_temp: return

        else_label = self._new_label()
        end_label = self._new_label() if node.else_branch else else_label

        self.code.append(f"IF_FALSE {condition_temp} GOTO {else_label}")
        self._generate_node(node.then_branch)

        if node.else_branch:
            self.code.append(f"GOTO {end_label}")
            self.code.append(f"LABEL {else_label}")
            self._generate_node(node.else_branch)
            self.code.append(f"LABEL {end_label}")
        else:
            self.code.append(f"LABEL {else_label}")

    def _generate_WhileLoop(self, node):
        start_label = self._new_label()
        end_label = self._new_label()

        self.code.append(f"LABEL {start_label}")
        condition_temp = self._generate_node(node.condition)
        if not condition_temp: return

        self.code.append(f"IF_FALSE {condition_temp} GOTO {end_label}")
        self._generate_node(node.body)
        self.code.append(f"GOTO {start_label}")
        self.code.append(f"LABEL {end_label}")

    def _generate_ForLoop(self, node):
        start_label = self._new_label()
        cond_label = self._new_label()
        update_label = self._new_label()
        end_label = self._new_label()

        if node.init:
            self._generate_node(node.init)

        self.code.append(f"GOTO {cond_label}")

        self.code.append(f"LABEL {start_label}")
        self._generate_node(node.body)

        self.code.append(f"LABEL {update_label}")
        if node.update:
            update_temp = self._generate_node(node.update)

        self.code.append(f"LABEL {cond_label}")
        if node.condition:
            condition_temp = self._generate_node(node.condition)
            if not condition_temp: return
            self.code.append(f"IF_TRUE {condition_temp} GOTO {start_label}")
        else:
             self.code.append(f"GOTO {start_label}")

        self.code.append(f"LABEL {end_label}")


    def _generate_PrintStatement(self, node):
        for expr in node.expressions:
            expr_temp = self._generate_node(expr)
            if expr_temp:
                self.code.append(f"PRINT {expr_temp}")

    def _generate_InputStatement(self, node):
        self.code.append(f"INPUT {node.variable}")

    def _generate_Block(self, node):
        for stmt in node.statements:
            self._generate_node(stmt)

    def _generate_Literal(self, node):
        temp = self._new_temp()
        value_repr = f'"{node.value}"' if node.type == Type.STRING else str(node.value)
        self.code.append(f"ASSIGN {temp}, {value_repr}")
        return temp

    def _generate_Variable(self, node):
        temp = self._new_temp()
        self.code.append(f"ASSIGN {temp}, {node.name}")
        return temp

    def _generate_BinaryOp(self, node):
        left_temp = self._generate_node(node.left)
        right_temp = self._generate_node(node.right)
        if not left_temp or not right_temp: return None

        result_temp = self._new_temp()
        op_map = {
            "+": "ADD", "-": "SUB", "*": "MUL", "/": "DIV",
            "==": "EQ", "!=": "NEQ", "<": "LT", ">": "GT", "<=": "LTE", ">=": "GTE",
            "&&": "AND", "||": "OR"
        }
        op_code = op_map.get(node.operator, "UNKNOWN_OP")
        if op_code == "UNKNOWN_OP": return None

        self.code.append(f"{op_code} {result_temp}, {left_temp}, {right_temp}")
        return result_temp

    def _generate_UnaryOp(self, node):
        operand_temp = self._generate_node(node.operand)
        if not operand_temp: return None

        result_temp = self._new_temp()
        if node.operator == "!":
            self.code.append(f"NOT {result_temp}, {operand_temp}")
        elif node.operator == "-":
            self.code.append(f"NEG {result_temp}, {operand_temp}")
        else: return None

        return result_temp

    def _generate_FunctionCall(self, node):
        arg_temps = []
        for arg in node.arguments:
            arg_temp = self._generate_node(arg)
            if not arg_temp: return None
            arg_temps.append(arg_temp)

        result_temp = self._new_temp()
        args_str = ", ".join(arg_temps) if arg_temps else ""
        self.code.append(f"CALL {result_temp}, {node.name}{', ' if args_str else ''}{args_str}")
        return result_temp


def compile_program(source_code, grammar_file='mini_lang.lark'):
    try:
        with open(grammar_file, 'r', encoding='utf-8') as f:
            grammar = f.read()
    except FileNotFoundError:
        print(f"Error: No se encontró el archivo de gramática '{grammar_file}'")
        return None
    except Exception as e:
        print(f"Error al leer el archivo de gramática: {e}")
        return None

    transformer = MiniLangTransformer()
    parser = Lark(grammar, parser='lalr', transformer=transformer, start='start', propagate_positions=True)

    try:
        print("Analizando léxico y sintácticamente...")
        ast = parser.parse(source_code)

        print("Analizando semánticamente...")
        semantic_analyzer = SemanticAnalyzer()
        if not semantic_analyzer.analyze(ast):
            print("\nErrores semánticos encontrados:")
            for i, error in enumerate(semantic_analyzer.errors):
                print(f"  {i+1}. {error}")
            return None
        else:
            print("Análisis semántico completado sin errores.")

        print("\nGenerando código intermedio...")
        code_generator = IntermediateCodeGenerator()
        intermediate_code = code_generator.generate(ast)
        print("Generación de código intermedio completada.")

        return intermediate_code

    except UnexpectedToken as e:
        print(f"\nError sintáctico en línea {e.line}, columna {e.column}:")
        context_lines = source_code.splitlines()
        faulty_line = context_lines[e.line-1] if e.line > 0 and e.line <= len(context_lines) else ""
        print(f"Línea {e.line}: {faulty_line}")
        print(f"{' ' * (e.column + len(str(e.line))+1)}^")
        print(f"Se encontró un token inesperado: '{e.token}' ({e.token.type})")
        expected_tokens = sorted(list(e.expected))
        max_expected_to_show = 10
        if len(expected_tokens) > max_expected_to_show:
            expected_str = ", ".join(expected_tokens[:max_expected_to_show]) + "..."
        else:
            expected_str = ", ".join(expected_tokens)
        print(f"Se esperaba uno de: {expected_str}")
        return None
    except UnexpectedCharacters as e:
        print(f"\nError léxico en línea {e.line}, columna {e.column}:")
        context_lines = source_code.splitlines()
        faulty_line = context_lines[e.line-1] if e.line > 0 and e.line <= len(context_lines) else ""
        print(f"Línea {e.line}: {faulty_line}")
        print(f"{' ' * (e.column + len(str(e.line))+1)}^")
        print(f"Se encontraron caracteres inesperados cerca de: '{e.char}'")
        print(f"Contexto: ...{source_code[e.pos_in_stream-10:e.pos_in_stream+10]}...")
        return None
    except Exception as e:
        import traceback
        print(f"\nError inesperado durante la compilación:")
        print(f"Tipo: {type(e).__name__}")
        print(f"Mensaje: {e}")
        return None

if __name__ == "__main__":
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
        try:
            print(f"Compilando archivo: {input_file}")
            with open(input_file, 'r', encoding='utf-8') as f:
                source = f.read()
        except FileNotFoundError:
            print(f"Error: El archivo '{input_file}' no existe.")
            sys.exit(1)
        except Exception as e:
            print(f"Error al leer el archivo '{input_file}': {e}")
            sys.exit(1)
    else:
        print("No se proporcionó archivo de entrada. Usando código de ejemplo interno.")
        source = """
var n = 5;
var fact = 1;
var i = 1;

print("Calculando el factorial de", n);

while (i <= n) {
    fact = fact * i;
    i = i + 1;
}

print("El factorial usando while es:", fact);

fact = 1;

for (var j = 1; j <= n; j = j + 1) {
    fact = fact * j;
}

print("El factorial usando for es:", fact);

if (n > 10) {
    print("El número es mayor que 10");
} else {
    print("El número es menor o igual a 10");
}

var neg = -n;
print("Negativo de n:", neg);


fact = 1;
i = 1;
while (i <= n) {
    fact = fact * i;
    i = i + 1;
}

print("El factorial final de", n, "es:", fact);
        """
        if not os.path.exists("example.mini"):
             try:
                 with open("example.mini", "w", encoding="utf-8") as f:
                     f.write(source)
                 print("Creado archivo example.mini con código de ejemplo.")
             except Exception as e:
                 print(f"No se pudo crear example.mini: {e}")


    if not os.path.exists("mini_lang.lark"):
         print("Error: Falta el archivo 'mini_lang.lark'.")
         sys.exit(1)

    intermediate_code = compile_program(source)

    if intermediate_code:
        print("\n--- Compilación Exitosa ---")
        print("Código Intermedio Generado:")
        print("---------------------------")
        for line_num, line_code in enumerate(intermediate_code):
            print(f"{line_num:03d}: {line_code}")
        print("---------------------------")
    else:
        print("\n--- Compilación Fallida ---")
        sys.exit(1)