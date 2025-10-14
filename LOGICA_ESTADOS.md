# logica.md
## Diseño de la lógica de estados de los barcos y flujo de decisión

### 1. Definición de estados
Cada casilla del tablero mantiene un valor entero que representa su estado:

| Valor | Significado    | Descripción breve |
|:-----:|:---------------|:------------------|
| -1    | Agua           | Casilla vacía, sin barco. |
| 0     | Barco intacto  | Parte de un barco que aún no ha sido alcanzada. |
| 1     | Tocado         | Parte de un barco alcanzada (aún no hundido). |
| 2     | Hundido        | Todas las partes de ese barco han sido alcanzadas. |

### 2. Flujo de decisión al disparar
Al recibir una coordenada (fila, columna) el backend realiza:

1. Validar coordenada (dentro de rango); si no, devolver 400.
2. Si la casilla ya fue revelada (valores -1, 1, 2) → devolver resultado "repetido" (sin cambios).
3. Si la casilla es agua (valor 0 y no pertenece a ningún barco) → marcar como -1 y devolver "agua".
4. Si la casilla pertenece a un barco:
    - Marcar la casilla como 1 (tocado).
    - Obtener el id del barco al que pertenece esa casilla.
    - Comprobar si quedan casillas del mismo id con valor 0:
        - Si sí → devolver "tocado".
        - Si no → actualizar todas las posiciones de ese id a 2 (hundido) y devolver "hundido".

### 3. Pseudocódigo básico
def disparar(fila, columna):
celda = tablero[fila][columna]

    # Caso 1: ya disparado
    if celda in (-1, 1, 2):
        return {"resultado": "repetido"}

    # Caso 2: agua
    if celda == 0:
        tablero[fila][columna] = -1
        return {"resultado": "agua"}

    # Caso 3: parte de un barco
    id_barco = obtener_id_barco(fila, columna)
    tablero[fila][columna] = 1  # marcado como tocado

    if quedan_partes_sin_tocar(id_barco):
        return {"resultado": "tocado"}
    else:
        marcar_como_hundido(id_barco)
        return {"resultado": "hundido"}
