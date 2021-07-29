## *CI5437 - Inteligencia Aritificial I* 
# **Proyecto 4: Forest Tiles MDP**

**Forest Tiles** es un *Markov Decision Process* donde un agente
debe moverse a través de un mapa cuadrado con elementos como
rocas, charcos, grama, etc hasta llegar a alguna casilla *GOAL*. 
El objetivo de este proyecto es visualizar los valores de estado 
aprendidos por el agente utilizando los métodos de *Value Iteration* 
y *Real Time Dinamyc Programming*, mientras resuelve un *Forest Tiles*.
 
## **Requisitos**

1. `Python 3.7+`

## **Ejecucion**

Para ejecutar el script se debe seguir la siguiente sintaxis:

```bash
python ForestTilesMDP.py WORLD ITERATIONS ERROR_RATE [SLEEP_TIME]
```

Donde ```WORLD``` es la dirección de un archivo que contiene las
especificaciones del mapa (cuya configuración se explicará más
adelante). ```ITERATIONS``` es el número de iteraciones durante 
el cual se aplicará el método *Value Iteration*. ```ERROR_RATE```
es la probabilidad de que el robot escoja una acción aleatoria
en lugar de seguir la política aprendida, debe ser un número entre
`0.0` y `1.0`. Y ```SLEEP_TIME``` son los segundos que se esperará
entre cada iteración del VI y del RTDP, su valor por defecto es 
```0.5```.

Una vez ejecutado el script aparecerá una representación del mapa
tal que el tono del color de las casillas dependerá del valor de
la posición aprendida por el agente en ese momento (esto se 
explicará detalladamente más adelante). El mapa se irá actualizando
```ITERATIONS``` veces usando el método de *Value Iteration*. 
Luego de eso, el agente aparecerá en su posición inicial y se 
moverá según los valores aprendidos durante el *Value Iteration*,
y continuará actualizando el valor de las casillas por las que pase
usando el método *Real Time Dinamyc Programming* hasta que alcance
una casilla objetivo.

## **World**

Los archivos `.world` contienen la especificación del mapa sobre el
que se moverá el agente. Esta configuración consiste en una serie
de instrucciones, las cuales pueden ser:

* `WORLD <M> <N>` indica que el mapa tendra `M` filas y `N`
columnas. Las filas y columnas se enumeran desde el `0`. La fila 
`0` es la que se encuentra mas arriba.

* `GOAL <M> <N>` indica que hay una casilla objetivo en la posición 
`(M, N)`, es decir, fila `M` columna `N`. Aparecen en la representación
del mapa como **GG** completamente en blanco.

* `BEGIN <M> <N>`  indica que el agente comenzara a moverse desde
la posición `(M, N)`. La casilla en la que se encuentre el agente
aparece como **MM** de color rojo.

* `WALL <M> <N>` coloca una pared en la posición `(M, N)`. El agente
no se puede mover desde ni hacia las casillas que contengan una pared. 
Aparecen en la representación del mapa como **@@** de color marrón.

* `HWALL <R> <A> <B>` coloca una pared horizontal desde la posición
`(R, A)` hasta `(R, B)`.

* `VWALL <C> <A> <B>` coloca una pared vertical desde la posición
`(A, C)` hasta `(B, C)`.

* `WATER <M> <N>` coloca un charco de agua en la posición `(M, N)`.
El agente recibe una penalización extra por moverse desde una casilla
con agua. Aparecen en la representación del mapa como **~~** de color
azul.

* `PENALWATER <P>` establece la penalización extra por moverse en un
charco en `-P`. Debe ser mayor o igual a 1. EL valor predeterminado
es 1.

* `HWATER <R> <A> <B>` coloca un charco de agua horizontal desde la 
posición `(R, A)` hasta `(R, B)`.

* `VWATER <C> <A> <B>` coloca un charco de agua vertical desde la 
posición `(A, C)` hasta `(B, C)`.

* `GRASS <M> <N>` coloca una casilla de grama en la posición `(M, N)`.
Si el robot se encuentra en una casilla con grama, entonces su 
siguiente movimiento será aleatorio. Aparecen en la representación
del mapa como **WW** de color verde.

* `HGRASS <R> <A> <B>` coloca casillas de grama desde la posición
`(R, A)` hasta `(R, B)`.

* `VGRASS <C> <A> <B>` coloca casillas de grama desde la posición
`(A, C)` hasta `(B, C)`.

* `FLOOR <M> <N>` coloca una casilla de suelo liso en la posición 
`(M, N)`. El robot recibe una penalización menor por moverse en 
suelo liso que en las casillas normales. Aparecen en la 
representación del mapa como **||** en tonos grises.

* `HFLOOR <R> <A> <B>` coloca casillas de suelo liso desde la posición
`(R, A)` hasta `(R, B)`.

* `VFLOOR <C> <A> <B>` coloca casillas de suelo liso desde la posición
`(A, C)` hasta `(B, C)`.

* `PORTAL <R1> <C1> <R2> <C2>` coloca un portal desde `(R1, C1)` hasta
`(R2, C2)`.

Las casillas normales se representan en el mapa como **##** en tonos
grises. El tono de las casillas dependerá del valor aprendido por el
agente en ese momento. La casilla con el menor valor aparecerá con el
tono más oscuro, y el resto de casillas tendrán un tono más claro 
en comparacion. Mientras más claro el tono, más cercano a 0 es su valor.
Las únicas casillas que mantienen un tono constante son el *GOAL*, pues
su valor siempre es `0`, las paredes, pues no se puede mover desde ni
hacia ellas, por lo que su valor nunca cambia y la casilla donde se
encuentre el agente. No se pueden colocar dos casillas de distinto tipo
en la misma posición, a excepción de los portales donde ni siquiera
se puede colocar dos portales en la misma posición.

## **Detalles de Implementacion**

* Hay una clase `World` que almacena todas las configuraciones que 
se encuentran en el archivo `.world`.

* Las casillas objetivo, paredes, charcos de agua, grama y pisos lisos
son almacenados en respectivos conjuntos (clase `set` de python).

* La probabilidad de moverse hacia una casilla `B` desde una casilla 
`A` durante el *Value Iteration* se calcula como 
`2^V(B) / SUM(2^V(Si))` donde `V(X)` es el valor aprendido para 
el estado `X` y `SUM(2^V(Si))` es la sumatoria sobre todos los 
posibles estados a los que se puede mover el agente desde `A`.

* Si se escogio la acción `a` y el ratio de error es `E`, entonces
la probabilidad de que el robot se mueva siguiendo la acción `a` 
es `1 - E + E/4`, mientras que la probabilidad de que se mueva en
otra direccion es `E/4`. Esto a excepción de que el agente se 
encuentre en grama, pues en ese caso la probabilidad de seguir 
cualquier acción es la misma.

## **Autores**

* Amin Arriaga
* David Segura
* Wilfredo Graterol
* Carlos Infante