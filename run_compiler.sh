#!/bin/bash

# Script para ejecutar el compilador
# Uso: ./run_compiler.sh [nombre_del_archivo]

# Verificar si Lark está instalado
if ! pip show lark > /dev/null 2>&1; then
    echo "Instalando Lark (requiere pip)..."
    pip install lark
fi

# Copiar la gramática a un archivo
cat > mini_lang.lark << 'EOL'
// mini_lang.lark - Gramática para un lenguaje simple

// Punto de inicio del programa
start: statement*

// Definición de instrucciones
statement: var_declaration
         | assignment
         | if_statement
         | while_loop
         | for_loop
         | print_statement
         | input_statement
         | block

// Declaración de variables
var_declaration: "var" NAME ("=" expression)? ";"

// Asignación
assignment: NAME "=" expression ";"

// Estructuras de control
if_statement: "if" "(" expression ")" statement ["else" statement]
while_loop: "while" "(" expression ")" statement
for_loop: "for" "(" [for_init] ";" [expression] ";" [for_update] ")" statement
for_init: for_var_declaration | for_assignment | expression
for_var_declaration: "var" NAME ("=" expression)?  // Sin punto y coma
for_update: for_assignment | expression

// Asignación especial para for (sin punto y coma)
for_assignment: NAME "=" expression

// Entrada/Salida
print_statement: "print" "(" [expression ("," expression)*] ")" ";"
input_statement: "input" "(" NAME ")" ";"

// Bloques de código
block: "{" statement* "}"

// Expresiones
expression: or_expr

or_expr: and_expr ("||" and_expr)*
and_expr: equality ("&&" equality)*
equality: comparison (("==" | "!=") comparison)*
comparison: term (("<" | ">" | "<=" | ">=") term)*
term: factor (("+" | "-") factor)*
factor: unary (("*" | "/") unary)*
unary: ("!" | "-")? primary
primary: NUMBER | STRING | NAME | "(" expression ")" | function_call

// Llamada a funciones (extensión)
function_call: NAME "(" [expression ("," expression)*] ")"

// Tokens
NAME: /[a-zA-Z_][a-zA-Z0-9_]*/
NUMBER: /[0-9]+(\.[0-9]+)?/
STRING: /"[^"]*"/ | /'[^']*'/
COMMENT: /\/\/[^\n]*/ | /\/\*(.|\n)*?\*\//

// Ignorar espacios en blanco y comentarios
%import common.WS
%ignore WS
%ignore COMMENT
EOL

# Determinar el archivo a compilar
if [ "$#" -eq 1 ]; then
    INPUT_FILE="$1"
    
    # Verificar si el archivo existe
    if [ ! -f "$INPUT_FILE" ]; then
        echo "Error: El archivo $INPUT_FILE no existe."
        exit 1
    fi
else
    # Usar el programa de ejemplo por defecto
    cat > example.mini << 'EOL'
// Programa de ejemplo en nuestro lenguaje simple
// Calcula el factorial de un número

var n = 5;  // Número para calcular el factorial
var fact = 1;
var i = 1;

print("Calculando el factorial de", n);

// Usando un ciclo while
while (i <= n) {
    fact = fact * i;
    i = i + 1;
}

print("El factorial usando while es:", fact);

// Reiniciar el cálculo
fact = 1;

// Usando un ciclo for
for (var j = 1; j <= n; j = j + 1) {
    fact = fact * j;
}

print("El factorial usando for es:", fact);

// Probar condicionales
if (n > 10) {
    print("El número es mayor que 10");
} else {
    print("El número es menor o igual a 10");
}

// Entrada del usuario
print("Ingrese un número:");
input(n);
print("Has ingresado:", n);

// Calcular factorial del número ingresado
fact = 1;
for (i = 1; i <= n; i = i + 1) {
    fact = fact * i;
}

print("El factorial de", n, "es:", fact);
EOL
    INPUT_FILE="example.mini"
    echo "Usando programa de ejemplo: example.mini"
fi

# Ejecutar el compilador
python3 compiler.py "$INPUT_FILE"