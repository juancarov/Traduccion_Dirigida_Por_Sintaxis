from graphviz import Digraph

# ------------------ GRAMÁTICA ------------------
gramatica = (
    ("E", ["E", "+", "T"]),
    ("E", ["E", "-", "T"]),
    ("E", ["T"]),
    ("T", ["T", "*", "F"]),
    ("T", ["T", "/", "F"]),
    ("T", ["F"]),
    ("F", ["(", "E", ")"]),
    ("F", ["id"]),
    ("F", ["num"])
)

# ------------------ ATRIBUTOS ------------------
atributos = {
    "E": {"val": "float"},
    "T": {"val": "float"},
    "F": {"val": "float"},
    "id": {"tipo": "string"},
    "num": {"tipo": "float"}
}

# ------------------ PRIMEROS ------------------
def primeros(gramatica):
    primeros = {}
    for nt, _ in gramatica:
        primeros[nt] = set()

    cambio = True
    while cambio:
        cambio = False
        for nt, prod in gramatica:
            simbolo = prod[0]
            if simbolo not in [x for x, _ in gramatica]:
                primeros[nt].add(simbolo)
            else:
                primeros[nt] |= primeros.get(simbolo, set())
    return primeros

# ------------------ SIGUIENTES ------------------
def siguientes(gramatica, first):
    siguientes = {nt: set() for nt, _ in gramatica}
    siguientes["E"].add("$")

    cambio = True
    while cambio:
        cambio = False
        for nt, prod in gramatica:
            for i, simbolo in enumerate(prod):
                if simbolo in [x for x, _ in gramatica]:
                    siguiente = prod[i + 1:] if i + 1 < len(prod) else None
                    if siguiente:
                        prox = siguiente[0]
                        if prox in [x for x, _ in gramatica]:
                            siguientes[simbolo] |= first[prox]
                        else:
                            siguientes[simbolo].add(prox)
                    else:
                        siguientes[simbolo] |= siguientes[nt]
    return siguientes

# ------------------ PREDICCIÓN ------------------
def prediccion(gramatica, first, follow):
    predict = {}
    for nt, prod in gramatica:
        simbolo = prod[0]
        conjunto = set()
        if simbolo not in [x for x, _ in gramatica]:
            conjunto.add(simbolo)
        else:
            conjunto |= first[simbolo]
        if "ε" in conjunto:
            conjunto.remove("ε")
            conjunto |= follow[nt]
        predict[(nt, " ".join(prod))] = conjunto
    return predict

# ------------------ NODO AST ------------------
class Nodo:
    def __init__(self, valor, tipo=None, val=None, izq=None, der=None):
        self.valor = valor
        self.tipo = tipo
        self.val = val
        self.izq = izq
        self.der = der

    def __repr__(self, nivel=0):
        sangria = "  " * nivel
        texto = f"{sangria}{self.valor}"
        if self.tipo or self.val is not None:
            texto += f" -> "
            if self.tipo:
                texto += f"tipo={self.tipo} "
            if self.val is not None:
                texto += f"val={self.val}"
        texto += "\n"
        if self.izq:
            texto += self.izq.__repr__(nivel + 1)
        if self.der:
            texto += self.der.__repr__(nivel + 1)
        return texto

# ------------------ TABLA DE SÍMBOLOS ------------------
tabla_simbolos = {}
traza_semantica = []  # Aquí guardamos las reglas semánticas ejecutadas

def leer_variables():
    print("Ingrese variables (ej: a=4, b=3). Enter vacío para continuar:")
    while True:
        linea = input("> ").strip()
        if not linea:
            break
        if "=" in linea:
            nombre, valor = linea.split("=")
            nombre, valor = nombre.strip(), valor.strip()
            try:
                valor = float(valor)
            except ValueError:
                print("Valor no numérico, se ignora.")
                continue
            tabla_simbolos[nombre] = {"val": valor, "tipo": "ENTERO"}
        else:
            print("Formato inválido. Use a=3")

# ------------------ ANALIZADOR CON ACCIONES SEMÁNTICAS ------------------
def analizar_expresion(expresion):
    tokens = expresion.replace('(', ' ( ').replace(')', ' ) ').split()
    pos = 0

    def E():
        nonlocal pos
        nodo = T()
        E_val = nodo.val
        traza_semantica.append("E → T\t{ E.val = T.val }")

        while pos < len(tokens) and tokens[pos] in ['+', '-']:
            op = tokens[pos]
            pos += 1
            der = T()
            if op == '+':
                E_val = nodo.val + der.val
                traza_semantica.append("E → E1 + T\t{ E.val = E1.val + T.val }")
            elif op == '-':
                E_val = nodo.val - der.val
                traza_semantica.append("E → E1 - T\t{ E.val = E1.val - T.val }")
            nodo = Nodo(f"op({op})", izq=nodo, der=der, val=E_val)
        nodo.val = E_val
        return nodo

    def T():
        nonlocal pos
        nodo = F()
        T_val = nodo.val
        traza_semantica.append("T → F\t{ T.val = F.val }")

        while pos < len(tokens) and tokens[pos] in ['*', '/']:
            op = tokens[pos]
            pos += 1
            der = F()
            if op == '*':
                T_val = nodo.val * der.val
                traza_semantica.append("T → T1 * F\t{ T.val = T1.val * F.val }")
            elif op == '/':
                T_val = nodo.val / der.val
                traza_semantica.append("T → T1 / F\t{ T.val = T1.val / F.val }")
            nodo = Nodo(f"op({op})", izq=nodo, der=der, val=T_val)
        nodo.val = T_val
        return nodo

    def F():
        nonlocal pos
        tok = tokens[pos]

        if tok == '(':
            pos += 1
            nodo = E()
            pos += 1
            nodoF = Nodo("()", izq=nodo, val=nodo.val)
            traza_semantica.append("F → (E)\t{ F.val = E.val }")
            return nodoF

        elif tok.isalpha():
            pos += 1
            if tok not in tabla_simbolos:
                raise ValueError(f"Variable '{tok}' no definida.")
            val = tabla_simbolos[tok]["val"]
            tipo = tabla_simbolos[tok]["tipo"]
            nodo = Nodo(f"id({tok})", tipo=tipo, val=val)
            traza_semantica.append("F → id\t{ F.val = buscar(id) }")
            return nodo

        else:
            pos += 1
            val = float(tok)
            nodo = Nodo(f"num({tok})", tipo="REAL", val=val)
            traza_semantica.append("F → num\t{ F.val = num.lexval }")
            return nodo

    return E()

# ------------------ DIBUJAR AST ------------------
def dibujar_ast(nodo):
    dot = Digraph(comment="AST Decorado")

    def recorrer(n, padre=None):
        etiqueta = f"{n.valor}\\nval={n.val}"
        dot.node(str(id(n)), etiqueta)
        if padre:
            dot.edge(str(id(padre)), str(id(n)))
        if n.izq:
            recorrer(n.izq, n)
        if n.der:
            recorrer(n.der, n)

    recorrer(nodo)
    dot.render("AST_Decorado", format="png", cleanup=True)
    print("AST decorado generado como 'AST_Decorado.png'")

# ------------------ PROGRAMA PRINCIPAL ------------------
if __name__ == "__main__":
    leer_variables()
    expresion = input("Ingrese la expresión (ej: c = a * b + 2): ").strip()

    first = primeros(gramatica)
    follow = siguientes(gramatica, first)
    predict = prediccion(gramatica, first, follow)

    print("\n=== CONJUNTOS PRIMEROS ===")
    for nt, conj in first.items():
        print(f"PRIMEROS({nt}) = {conj}")

    print("\n=== CONJUNTOS SIGUIENTES ===")
    for nt, conj in follow.items():
        print(f"SIGUIENTES({nt}) = {conj}")

    print("\n=== CONJUNTOS DE PREDICCIÓN ===")
    for (nt, prod), conj in predict.items():
        print(f"PREDICCIÓN({nt} → {prod}) = {conj}")

    print("\n=== TABLA DE SÍMBOLOS ===")
    for var, info in tabla_simbolos.items():
        print(f"{var} -> {info}")

    if "=" in expresion:
        var, expr = expresion.split("=")
        var = var.strip()
        expr = expr.strip()

        ast = analizar_expresion(expr)
        resultado = ast.val
        tabla_simbolos[var] = {"val": resultado, "tipo": "REAL"}

        print("\n=== AST DECORADO ===")
        print(ast)
        print(f"Resultado de {var}: {resultado}")

        print("\n=== GRAMÁTICA DE ATRIBUTOS EJECUTADA ===")
        for regla in traza_semantica:
            print(regla)

        dibujar_ast(ast)
    else:
        print("La expresión debe tener una asignación.")
