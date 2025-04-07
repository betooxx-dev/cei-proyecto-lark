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

// Print statement (preserve existing functionality)
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
        self.transform(items[2])
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

class MiInterpreter(Transformer):
    def __init__(self):
        super().__init__()
        self.variables = {}

    def number(self, items):
        val = items[0].value
        try:
            return int(val)
        except ValueError:
            return float(val)

    def string(self, items):
        return items[0].value[1:-1]

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
        if var_name == 'i':
            self.variables[var_name] = 0  
        if var_name not in self.variables:
            raise NameError(f"Variable '{var_name}' no ha sido asignada.")
        
        return self.variables[var_name]

    def _division_by_zero(self): 
        raise ZeroDivisionError("División por cero.")
    def comparison(self, items):
      print(f"[DEBUG] Comparison items: {items}")
      if len(items) == 1: 
          return items[0]
      elif len(items) == 2:
          left, right = items
          return left == right
      elif len(items) == 3:
          left = items[0]
          op_token = items[1]
          right = items[2]
          op = op_token.value
          try:
              if op == '<': return left < right
              if op == '>': return left > right
              if op == '<=': return left <= right
              if op == '>=': return left >= right
              if op == '==': return left == right
              if op == '!=': return left != right
          except TypeError:
              raise TypeError(f"Operación de comparación '{op}' inválida entre los tipos {type(left).__name__} y {type(right).__name__} (valores: {repr(left)}, {repr(right)})")
    def add(self, items):
     print(items)
     # Si el elemento ya es primitivo (string, int, etc.), lo usamos tal cual
     left = items[0] if not hasattr(items[0], 'children') else self.transform(items[0])
     right = items[1] if not hasattr(items[1], 'children') else self.transform(items[1])
     
     if isinstance(left, str) or isinstance(right, str):
          # Concatenación si alguno es string
          return str(left) + str(right)
     elif isinstance(left, (int, float)) and isinstance(right, (int, float)):
          return left + right
     else:
          # Si no se permite otra combinación, se lanza error
          raise TypeError(f"Operación '+' inválida entre {type(left).__name__} y {type(right).__name__}")



    def sub(self, items):
        left = self.transform(items[0])
        right = self.transform(items[1])
        if isinstance(left, (int, float)) and isinstance(right, (int, float)):
            return left - right
        else:
            raise TypeError(f"Operación '-' inválida entre {type(left).__name__} y {type(right).__name__}")

    def mul(self, items):
        left = self.transform(items[0])
        right = self.transform(items[1])
        if isinstance(left, (int, float)) and isinstance(right, (int, float)):
            return left * right
        else:
            # Podrías permitir string * int para repetición si quieres
            raise TypeError(f"Operación '*' inválida entre {type(left).__name__} y {type(right).__name__}")

    def div(self, items):
        left = self.transform(items[0])
        right = self.transform(items[1])
        if isinstance(left, (int, float)) and isinstance(right, (int, float)):
            if right == 0:
                self._division_by_zero()
            # Considerar división entera vs flotante si es necesario
            return left / right
        else:
            raise TypeError(f"Operación '/' inválida entre {type(left).__name__} y {type(right).__name__}")


    def assignment_statement(self, items):
     print("[DEBUG] assignment_statement items:", items)
     assignment_expr = items[0]
     print("[DEBUG] assignment_expr:", assignment_expr)
     var_token, value_node = assignment_expr.children
     self._assign(var_token, value_node)
     return None
 

    def _assign(self, var_token, value):
        var_name = var_token.value if hasattr(var_token, "value") else str(var_token)
        self.variables[var_name] = value
     
    def expression_statement(self, items): 
        return None

    def print_statement(self, items):
        print(f"[DEBUG] Items received in print_statement: {items}")
        if len(items) == 2:
             value_to_print = items[1]
             print(f"[DEBUG] Print_statement: Valor a imprimir (de items[1]): {repr(value_to_print)}")
             print(value_to_print)
        else:
           value_to_print = items[0]
        return None

    def if_statement(self, items):
     print("[DEBUG] if_statement items:", items)
     # Se asume que items[0] es la condición
     condition_result = items[0] if not isinstance(items[0], Tree) else self.transform(items[0])
     if condition_result:  # Si la condición se evalúa como verdadera
          self.transform(items[1])  # Ejecutar el bloque "then"
     elif len(items) == 3:  # Si existe un bloque "else"
          self.transform(items[2])
     return None


    def program(self, items): 
        return None

    def for_statement(self, items):
     print(items)
     init_result = items[0]
     condition_result = items[1]
     update_result = items[2]
     body_result = items[3]
     
     # Inicialización de la variable 'i' si es necesario
     if isinstance(init_result, Tree) and init_result.data == 'assignment_statement':
         var_token = init_result.children[0]
         if var_token.value == 'i':  # Inicializamos 'i' a 0 o el valor que necesites.
             self.variables['i'] = 0  # Establecer el valor inicial aquí (por ejemplo, 0).
     

         
     return None
 
 

    def for_init_part(self, items):
        if not items:
            return None
        return items[0]

    def for_condition_part(self, items):
        if not items:
            return True
        return items[0]

    def for_update_part(self, items):
        if not items:
            return None
        return items[0]
    
    def func_call(self, items):
        function_name = items[0].value
        arguments = items[1:] if len(items) > 1 else []
        
        if function_name not in self.functions:
            raise NameError(f"Función '{function_name}' no está definida.")
        
        function_info = self.functions[function_name]
        parameters = function_info["parameters"]
        body = function_info["body"]
        return_type = function_info["return_type"]
        
        # Create a new scope for function variables
        old_variables = self.variables.copy()
        self.variables = {}
        
        # Assign arguments to parameters
        for i, param in enumerate(parameters):
            if i < len(arguments):
                param_name, param_type = param
                self.variables[param_name] = arguments[i]
            else:
                raise ValueError(f"Faltan argumentos para la función '{function_name}'")
        
        # Remember we're in a function to handle return statements
        old_in_function = self.in_function
        self.in_function = True
        old_return_value = self.return_value
        self.return_value = None
        
        # Execute function body
        self.transform(body)
        
        # Get the return value and restore state
        result = self.return_value
        self.return_value = old_return_value
        self.in_function = old_in_function
        self.variables = old_variables
        
        return result
    
    # Method for function declaration
    def function_declaration(self, items):
        return_type = items[0].value
        function_name = items[1].value
        parameters = items[2] if len(items) > 2 else []
        body = items[-1]  # Last item is the function body
        
        self.functions[function_name] = {
            "return_type": return_type,
            "parameters": parameters,
            "body": body
        }
        
        return None
    
    # Method for parameter list
    def parameter_list(self, items):
        return items
    
    # Method for individual parameters
    def parameter(self, items):
        param_type = items[0].value
        param_name = items[1].value
        return (param_name, param_type)
    
    # Method for return statements
    def return_statement(self, items):
        if not self.in_function:
            raise SyntaxError("Return statement outside of function")
        
        return_value = self.transform(items[0])
        self.return_value = return_value
        return None
    
    # Method for while statements
    def while_statement(self, items):
        condition_node = items[0]
        body_node = items[1]
        
        while self.transform(condition_node):
            self.transform(body_node)
        
        return None
    
    # Method for variable declarations with types
    def variable_declaration(self, items):
        var_type = items[0].value
        var_name = items[1].value
        
        # If there's an initializer expression
        if len(items) > 2:
            init_value = self.transform(items[2])
            # Should do type checking here
            self.variables[var_name] = init_value
        else:
            # Initialize with default value based on type
            if var_type == "int":
                self.variables[var_name] = 0
            elif var_type == "float":
                self.variables[var_name] = 0.0
            elif var_type == "string":
                self.variables[var_name] = ""
        
        return None
    
    # Update logical operators
    def logical_expr(self, items):
        if len(items) == 1:
            return items[0]
        
        left = items[0]
        op = items[1].value
        right = items[2]
        
        if op == "&&":
            return left and right
        elif op == "||":
            return left or right
        
        
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
    print("Bienvenido al programa de prueba!");
    nombre = "Mundo";
    a=22;
    pato=88;
    c="gato";
    if (c=="calabaza") then {}
    x=a>12;
    print("alogo");
    print("Hola, " + nombre + "!");
    contador = 0;
    limite = 3;
    print("Iniciando 'bucle' for (simulado)...");
    for (i = 0; i < limite; i = i + 1) {
      print("Dentro del for ");
      print(i); 
      contador = contador + 10; 
    }
    print("Después del 'bucle' for.");
    print("Valor final de i (después de una inicialización y una actualización):");
    print(i); 
    print("Valor final de contador (después de una ejecución del cuerpo):");
    print(contador); 
    print("--- Fin del programa ---");
    """

    try:
        parse_tree = parser.parse(codigo_fuente)
        print("\n--- Árbol de sintaxis abstracta (AST) ---")
        print(parse_tree.pretty())
        print("\n--- Interpretación / Ejecución con Transformer ---")
        interpreter = MiInterpreter()
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