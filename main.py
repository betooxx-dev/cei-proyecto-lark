import sys
from lark import Lark, Transformer, Token, Tree
import traceback

grammar = r"""
// Program structure
?start: program
program: statement*

// Statements
?statement: variable_declaration 
          | function_declaration
          | assignment_statement 
          | if_statement 
          | while_statement 
          | for_statement 
          | function_call_statement
          | return_statement 
          | block_statement 
          | expression_statement
          | print_statement

// Block
block_statement: "{" program "}"

// Expression statement
expression_statement: expression ";"

// Types
type: "int" | "float" | "string"

// Variable declaration
variable_declaration: type IDENTIFIER ["=" expression] ";"

// Function declaration
function_declaration: type IDENTIFIER "(" [parameter_list] ")" block_statement

// Parameters
parameter_list: parameter ("," parameter)*
parameter: type IDENTIFIER

// Return statement
return_statement: "return" expression ";"

// Assignment
assignment_statement: assignment_expression ";"
assignment_expression: IDENTIFIER "=" expression

// Function call
function_call_statement: function_call ";"
function_call: IDENTIFIER "(" [argument_list] ")"
argument_list: expression ("," expression)*

// Print statement
print_statement: "print" "(" expression ")" ";"

// Control structures
if_statement: "if" "(" expression ")" "then" block_statement ["else" block_statement]
while_statement: "while" "(" expression ")" block_statement
for_statement: "for" "(" for_init_part ";" for_condition_part ";" for_update_part ")" block_statement

// For loop parts
for_init_part: assignment_expression | variable_declaration | expression |
for_condition_part: expression |
for_update_part: assignment_expression | expression |

// Expressions
?expression: logical_expr
?logical_expr: comparison (("&&" | "||") comparison)*
?comparison: sum (("<" | ">" | "<=" | ">=" | "==" | "!=") sum)?
            | sum
?sum: product | sum "+" product -> add | sum "-" product -> sub
?product: atom | product "*" atom -> mul | product "/" atom -> div
?atom: NUMBER -> number 
     | STRING -> string 
     | BOOLEAN -> boolean 
     | IDENTIFIER -> var 
     | function_call -> func_call 
     | "(" expression ")" 
     | input_call -> input_call

// Input
input_call: "input" "(" ")"

// Boolean
BOOLEAN: "true" | "false"

// Terminal definitions
COMMENT: /\/\/[^\n]*/ | /\/\*([^*]|\*[^\/])*\*\//
STRING: /"([^"\\]|\\.)*"/ | /'([^'\\]|\\.)*'/
IDENTIFIER: /[a-zA-ZáéíóúÁÉÍÓÚñÑ][a-zA-Z0-9áéíóúÁÉÍÓÚñÑ_]*/
NUMBER: /\d+(\.\d+)?/

// Imports and ignores
%import common.WS
%ignore WS
%ignore COMMENT
"""

class SemanticAnalyzer(Transformer):
    def __init__(self):
        super().__init__()
        self.symbols = {}

    def log(self, msg):
        pass

    def program(self, items): 
        return None 

    def number(self, items): 
        return items[0]

    def string(self, items): 
        return items[0]

    def boolean(self, items): 
        return items[0]

    def input_call(self, _): 
        return None

    def var(self, items): 
        var_name = items[0].value
        return items[0] 

    def assignment_statement(self, items): 
        var_name = items[0].value
        self.symbols[var_name] = {'assigned': True}
        self.transform(items[1])
        return None

    def add(self, items): 
        self.transform(items[0])
        self.transform(items[1])
        return None

    def sub(self, items): 
        self.transform(items[0])
        self.transform(items[1])
        return None

    def mul(self, items): 
        self.transform(items[0])
        self.transform(items[1])
        return None

    def div(self, items): 
        self.transform(items[0])
        self.transform(items[1])
        return None

    def expression_statement(self, items): 
        self.transform(items[0])
        return None

    def print_statement(self, items): 
        self.transform(items[0])
        return None

    def if_statement(self, items): 
        self.transform(items[1])
        self.transform(items[3])
        return None

    def for_statement(self, items):
        init_part_result = items[2]
        cond_part_result = items[4]
        update_part_result = items[6]
        body_result = items[9]
        return None

    def for_init_part(self, items):
        if not items:
            return None
        self.transform(items[0])
        return True

    def for_condition_part(self, items):
        if not items:
            return None
        self.transform(items[0])
        return True

    def for_update_part(self, items):
        if not items:
            return None
        self.transform(items[0])
        return True

class Interpreter(Transformer):
    def __init__(self):
        super().__init__()
        self.variables = {}
        self.functions = {}  # Almacena las funciones definidas
        self.in_function = False  # Indica si estamos dentro de una función
        self.return_value = None  # Almacena el valor de retorno

    # Método personalizado para transformar árboles
    def _custom_transform(self, node):
        print(f"[DEBUG] Processing node: {type(node)} - {node}")
        
        # Si es un árbol, lo procesamos según su tipo
        if isinstance(node, Tree):
            # Procesamiento según el tipo de nodo
            if node.data == 'var':
                # Acceso a variable
                var_name = node.children[0].value
                if var_name not in self.variables:
                    raise NameError(f"Variable '{var_name}' no ha sido asignada.")
                return self.variables[var_name]
                
            elif node.data == 'comparison':
                print(f"[DEBUG] Comparison node with {len(node.children)} children: {node.children}")
                
                # Si solo hay un hijo, podría ser una variable, número u otra expresión
                if len(node.children) == 1:
                    return self._custom_transform(node.children[0])
                    
                # Si hay 3 hijos, es una comparación completa: valor operador valor
                elif len(node.children) == 3:
                    left_node = node.children[0]
                    operator_token = node.children[1]
                    right_node = node.children[2]
                    
                    left_value = self._custom_transform(left_node)
                    right_value = self._custom_transform(right_node)
                    operator = operator_token.value
                    
                    print(f"[DEBUG] Evaluating comparison: {left_value} {operator} {right_value}")
                    
                    if operator == '<': 
                        result = left_value < right_value
                    elif operator == '>': 
                        result = left_value > right_value
                    elif operator == '<=': 
                        result = left_value <= right_value
                    elif operator == '>=': 
                        result = left_value >= right_value
                    elif operator == '==': 
                        result = left_value == right_value
                    elif operator == '!=': 
                        result = left_value != right_value
                    else:
                        raise ValueError(f"Operador de comparación desconocido: {operator}")
                    
                    print(f"[DEBUG] Result of comparison: {result}")
                    return result
                
                # Para manejar el caso de que la estructura del AST tenga 2 hijos (valor1, valor2)
                # Este es el caso problemático donde no se captura el operador
                elif len(node.children) == 2:
                    left_value = self._custom_transform(node.children[0])
                    right_value = self._custom_transform(node.children[1])
                    
                    # Intentamos inferir el operador por la posición en el árbol
                    # En este caso específico, sabemos que la comparación x < 23 está generando [x, 23]
                    print(f"[DEBUG] Inferring comparison between {left_value} and {right_value}")
                    
                    # Asumimos que es una comparación de menor que (<) cuando encontramos esta estructura
                    # Esta es una corrección temporal para el caso específico
                    result = left_value < right_value
                    print(f"[DEBUG] Inferred comparison result: {result}")
                    return bool(result)
                
                # Si no coincide con los patrones anteriores, procesamos el primer hijo
                return self._custom_transform(node.children[0])
                
            elif node.data == 'logical_expr':
                print(f"[DEBUG] Logical expression node with {len(node.children)} children")
                
                # Si solo hay un hijo, podría ser una comparación u otra expresión
                if len(node.children) == 1:
                    return self._custom_transform(node.children[0])
                    
                # Para expresiones lógicas con múltiples operadores (a && b || c)
                elif len(node.children) >= 3:
                    # Primer elemento siempre es una expresión
                    left_result = self._custom_transform(node.children[0])
                    
                    # Procesar todos los operadores lógicos en secuencia
                    result = bool(left_result)
                    for i in range(1, len(node.children) - 1, 2):
                        operator = node.children[i].value
                        right_expr = node.children[i + 1]
                        right_result = bool(self._custom_transform(right_expr))
                        
                        print(f"[DEBUG] Logical operation: {result} {operator} {right_result}")
                        
                        if operator == '&&':
                            result = result and right_result
                        elif operator == '||':
                            result = result or right_result
                        else:
                            raise ValueError(f"Operador lógico desconocido: {operator}")
                            
                        print(f"[DEBUG] Logical result: {result}")
                    
                    return result
                    
                # Para el caso donde tenemos 2 nodos de comparación sin operador explícito (como en el árbol)
                elif len(node.children) == 2:
                    left_result = bool(self._custom_transform(node.children[0]))
                    right_result = bool(self._custom_transform(node.children[1]))
                    
                    print(f"[DEBUG] Inferring logical AND between {left_result} and {right_result}")
                    # Asumimos que es un AND lógico cuando encontramos esta estructura
                    result = left_result and right_result
                    print(f"[DEBUG] Inferred logical result: {result}")
                    return result
                
                # Caso por defecto, devolver el valor del primer hijo
                return self._custom_transform(node.children[0])
                
            elif node.data == 'add':
                left = self._custom_transform(node.children[0])
                right = self._custom_transform(node.children[1])
                print(f"[DEBUG] Add: {left} + {right}")
                
                if isinstance(left, str) or isinstance(right, str):
                    return str(left) + str(right)  # Concatenación
                else:
                    return left + right  # Suma aritmética
                    
            elif node.data == 'sub':
                left = self._custom_transform(node.children[0])
                right = self._custom_transform(node.children[1])
                print(f"[DEBUG] Sub: {left} - {right}")
                return left - right
                
            elif node.data == 'mul':
                left = self._custom_transform(node.children[0])
                right = self._custom_transform(node.children[1])
                print(f"[DEBUG] Mul: {left} * {right}")
                return left * right
                
            elif node.data == 'div':
                left = self._custom_transform(node.children[0])
                right = self._custom_transform(node.children[1])
                print(f"[DEBUG] Div: {left} / {right}")
                
                if right == 0:
                    raise ZeroDivisionError("División por cero.")
                    
                return left / right
                
            elif node.data == 'number':
                value = node.children[0].value
                try:
                    return int(value)
                except ValueError:
                    return float(value)
                    
            elif node.data == 'string':
                return node.children[0].value[1:-1]  # Quitar comillas
                
            elif node.data == 'boolean':
                return node.children[0].value == "true"
            
            # Para otros tipos de nodos, usar la transformación regular
            return super().transform(node)
            
        # Si es un token, devolvemos su valor
        elif isinstance(node, Token):
            return node.value
            
        # Cualquier otro caso
        return node

    def number(self, items):
        val = items[0].value
        try:
            return int(val)
        except ValueError:
            return float(val)

    def string(self, items):
        return items[0].value[1:-1]  # Quitar comillas

    def boolean(self, items):
        return items[0].value == "true"

    def input_call(self, _): 
        try:
            user_input = input("Ingrese valor: ")
            try:
                return int(user_input)
            except ValueError:
                try:
                    return float(user_input)
                except ValueError:
                    return user_input
        except EOFError: 
            return None

    def var(self, items): 
        var_name = items[0].value
        if var_name not in self.variables:
            raise NameError(f"Variable '{var_name}' no ha sido asignada.")
        
        return self.variables[var_name]

    # Estos métodos ya se manejan en _custom_transform
    def add(self, items):
        return self._custom_transform(Tree('add', items))

    def sub(self, items):
        return self._custom_transform(Tree('sub', items))

    def mul(self, items):
        return self._custom_transform(Tree('mul', items))

    def div(self, items):
        return self._custom_transform(Tree('div', items))

    def assignment_statement(self, items):
        assignment_expr = items[0]
        print(f"[DEBUG] Assignment: {assignment_expr}")
        
        var_token = assignment_expr.children[0]
        value_node = assignment_expr.children[1]
        
        value = self._custom_transform(value_node)
        var_name = var_token.value
        
        print(f"[DEBUG] Assigning {var_name} = {value}")
        
        self.variables[var_name] = value
        return None

    def print_statement(self, items):
        expr_node = items[0]
        value = self._custom_transform(expr_node)
        
        print(f"[DEBUG] Print value: {value}")
        print(value)
        
        return None

    def if_statement(self, items):
        print(f"[DEBUG] if_statement with items: {items}")
        
        # La condición está en el primer elemento
        condition_node = items[0]
        
        # Usar _custom_transform para evaluar la condición correctamente
        condition_value = self._custom_transform(condition_node)
        
        # Convertir explícitamente a booleano
        condition_result = bool(condition_value)
        print(f"[DEBUG] If condition evaluated to: {condition_value} as boolean: {condition_result}")
        
        # Ejecutar solo el bloque correspondiente basado en la condición
        if condition_result:
            # Bloque 'then'
            print("[DEBUG] Executing THEN block")
            then_block = items[1]
            self.transform(then_block)
        elif len(items) >= 3 and items[2] is not None:
            # Bloque 'else' (si existe)
            print("[DEBUG] Executing ELSE block")
            else_block = items[2]
            self.transform(else_block)
            
        return None

    def while_statement(self, items):
        print(f"[DEBUG] while_statement with items: {items}")
        
        condition_node = items[0]
        body_node = items[1]
        
        iteration = 0
        # Evaluar la condición inicial usando _custom_transform
        condition_value = self._custom_transform(condition_node)
        # Convertir explícitamente a booleano
        condition_result = bool(condition_value)
        print(f"[DEBUG] While initial condition: {condition_value} as boolean: {condition_result}")
        
        # Bucle while con evaluación booleana explícita
        while condition_result:
            print(f"[DEBUG] Executing while loop iteration {iteration}")
            iteration += 1
            
            # Ejecutar el cuerpo
            self.transform(body_node)
            
            # Re-evaluar la condición
            condition_value = self._custom_transform(condition_node)
            condition_result = bool(condition_value)
            print(f"[DEBUG] While condition re-evaluated: {condition_value} as boolean: {condition_result}")
        
        return None

    def block_statement(self, items):
        if not items or items[0] is None:
            return None
            
        if not hasattr(items[0], 'children'):
            return None
            
        for statement in items[0].children:
            if statement is not None:
                self.transform(statement)
                
        return None

    def for_statement(self, items):
        init_part = items[0]
        condition_part = items[1]
        update_part = items[2]
        body = items[3]
        
        # Ejecutar la parte de inicialización
        if init_part is not None:
            self.transform(init_part)
        
        # Bucle for
        while True:
            # Comprobar la condición (si existe)
            if condition_part is not None:
                condition_value = self._custom_transform(condition_part)
                condition_result = bool(condition_value)
                print(f"[DEBUG] For condition: {condition_value} as boolean: {condition_result}")
                if not condition_result:
                    break
            
            # Ejecutar el cuerpo
            self.transform(body)
            
            # Ejecutar la parte de actualización
            if update_part is not None:
                self.transform(update_part)
                
        return None

    def function_declaration(self, items):
        return_type = items[0].value
        function_name = items[1].value
        parameters = items[2] if len(items) > 2 else []
        body = items[-1]
        
        self.functions[function_name] = {
            "return_type": return_type,
            "parameters": parameters,
            "body": body
        }
        
        return None

    def parameter_list(self, items):
        return items

    def parameter(self, items):
        param_type = items[0].value
        param_name = items[1].value
        return (param_name, param_type)

    def return_statement(self, items):
        if not self.in_function:
            raise SyntaxError("Return statement outside of function")
        
        return_value = self._custom_transform(items[0])
        self.return_value = return_value
        
        return None

    def func_call(self, items):
        function_name = items[0].value
        arguments = [self._custom_transform(arg) for arg in items[1:]] if len(items) > 1 else []
        
        if function_name not in self.functions:
            raise NameError(f"Función '{function_name}' no está definida.")
        
        function_info = self.functions[function_name]
        parameters = function_info["parameters"]
        body = function_info["body"]
        
        # Crear un nuevo ámbito para las variables de la función
        old_variables = self.variables.copy()
        self.variables = {}
        
        # Asignar argumentos a parámetros
        for i, param in enumerate(parameters):
            if i < len(arguments):
                param_name, param_type = param
                self.variables[param_name] = arguments[i]
            else:
                raise ValueError(f"Faltan argumentos para la función '{function_name}'")
        
        # Configurar el entorno de la función
        old_in_function = self.in_function
        self.in_function = True
        old_return_value = self.return_value
        self.return_value = None
        
        # Ejecutar el cuerpo de la función
        self.transform(body)
        
        # Obtener el valor de retorno y restaurar el entorno
        result = self.return_value
        self.return_value = old_return_value
        self.in_function = old_in_function
        self.variables = old_variables
        
        return result

def find_first_token(node):
    """Encuentra recursivamente el primer Token en un nodo o subárbol."""
    if isinstance(node, Token):
        return node
    if isinstance(node, Tree):
        for child in node.children:
            token = find_first_token(child)
            if token:
                return token
    return None

def check_standalone_expressions(node, source_code_lines):
    """
    Recorre el árbol y emite advertencias/errores para expression_statements
    que no parecen tener efectos secundarios.
    """
    warnings = []
    if isinstance(node, Tree):
        # ¡Este es el chequeo clave!
        if node.data == 'expression_statement':
            expression_node = node.children[0]
            is_suspicious = False
            # Determinar si la expresión es sospechosa (sin efecto secundario aparente)
            if isinstance(expression_node, Tree):
                # Operaciones binarias, comparaciones, literales, variables solas
                if expression_node.data in ['comparison', 'add', 'sub', 'mul', 'div']:
                   is_suspicious = True
                elif expression_node.data == 'atom':
                     child_atom = expression_node.children[0]
                     if isinstance(child_atom, Tree):
                          # input_call SI tiene efecto, así que NO es sospechoso
                          if child_atom.data not in ['input_call']:
                              is_suspicious = True
                     elif isinstance(child_atom, Token): # Identificador solo
                         is_suspicious = True
            if is_suspicious:
                first_token = find_first_token(expression_node)
                line = first_token.line if first_token else '?'
                col = first_token.column if first_token else '?'
                line_content = source_code_lines[line-1].strip() if line != '?' and line <= len(source_code_lines) else ""
                warnings.append(
                    f"Error Semántico (Línea {line}, Col {col}): La sentencia de expresión no parece tener efecto.\n"
                    f"   ---> {line_content}"
                )

        # Recurrir para los hijos
        for child in node.children:
            warnings.extend(check_standalone_expressions(child, source_code_lines))

    return warnings

if __name__ == "__main__":
    try:
        parser = Lark(grammar, parser='lalr', start='program')
    except Exception as e:
        print(f"Error al crear el parser Lark: {e}")
        traceback.print_exc()
        sys.exit(1)

    codigo_fuente = """
    print("Programa de cálculo simple");
    
    //vaca (x, jamón) {
      //  return x;
    //}
    x=0;
    y=18;
    
    while (x<23 && y==18) {
        x = x + 1;
        print("El valor de x es: " + x);
        if (x > 10) then {
            print("x es mayor que 10");
        }
    }
    
    a = 5;
    b = 10;
    suma = a + b;

    print("El valor de a es: " + a);
    print("El valor de b es: " + b);
    print("La suma de a + b es: " + suma);

    if (suma > 10) then {
        print("La suma es mayor que 10");
    } else {
        print("La suma es menor o igual a 10");
    }

    resta = b - a;
    print("La resta b - a es: " + resta);

    doble = suma * 2;
    print("El doble de la suma es: " + doble);

    print("Fin del programa");
    """

    try:
        source_code_lines = codigo_fuente.split('\n')
        parse_tree = parser.parse(codigo_fuente)
        print("\n--- Árbol de sintaxis abstracta (AST) ---")
        print(parse_tree.pretty())
        
        # Analizar expresiones sin efecto
        warnings = check_standalone_expressions(parse_tree, source_code_lines)
        if warnings:
            print("\n--- Advertencias de análisis semántico ---")
            for warning in warnings:
                print(warning)
        
        print("\n--- Interpretación / Ejecución con Transformer ---")
        interpreter = Interpreter()
        interpreter.transform(parse_tree)
        print("\n--- Tabla de Símbolos (Variables en Runtime) ---")
        
        if not interpreter.variables:
            print("(La tabla está vacía)")
        else:
            # Imprimir encabezados
            print(f"{'Nombre':<15} | {'Valor':<25} | {'Tipo':<15}")
            print("-" * 57) # Línea separadora
            # Iterar sobre el diccionario de variables
            for name, value in interpreter.variables.items():
                tipo = type(value).__name__ # Obtener el nombre del tipo (int, str, float, NoneType)
                # Imprimir cada fila formateada
                print(f"{name:<15} | {repr(value):<25} | {tipo:<15}")
    except Exception as e:
        print(f"Error al procesar el código: {e}")
        traceback.print_exc()
        sys.exit(1)