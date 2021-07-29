from typing import *
from random import choices
from time import sleep
from sys import argv, stderr

TOP, RIGHT, DOWN, LEFT = 0, 1, 2, 3
ACTIONS = [TOP, RIGHT, DOWN, LEFT]

class World:
  """
    Representacion del mapa sobre el que se movera el robot.
  """
  def __init__(self):
    self.special = set()
    self.goals = set()
    self.walls = set()
    self.water = set()
    self.grass = set()
    self.floor = set()
    self.portals = {}
    self.nPortals = 0
    self.penalWater = 1.0
    self.pos = (0,0)

  def verify(self, pos: Tuple[int, int], rightSet: Set[Tuple[int, int]], line: int):
    """
      Verifica que en una casilla no hay algun elemento especial excepto el de un
      tipo especifico.

      Argumentos:
        pos: Tuple[int, int]  ->  Casilla a verificar.
        rightSet: Set[Tuple[int, int]]  ->  Conjunto al que si puede pertenecer la casilla.
        line: int ->  Linea del archivo que se esta leyendo actualmente.
    """
    if pos in self.special and pos not in rightSet:
      print(
        f'\033[1;31mError.\033[0m Linea {line+1}. \n' +\
          'No se pueden colocar 2 objetos de distinto tipo en la misma posicion.',
        file=stderr
      )
      exit(1)
    self.special.add(pos)

  def read(self, filename: str):
    """
      Lee la configuracion de una cuadricula desde un archivo.
    """
    with open(filename, 'r') as f:
      for k, line in enumerate(f.readlines()):
        line = line.split()

        if not line: 
          continue

        elif line[0] == 'WORLD':
          self.M = int(line[1])
          self.N = int(line[2])

        elif line[0] == 'GOAL':
          pos = (int(line[1]), int(line[2]))
          self.verify(pos, self.goals, k)
          self.goals.add(pos)

        elif line[0] == 'BEGIN':
          self.pos = (int(line[1]), int(line[2]))

        elif line[0] == 'WALL':
          pos = (int(line[1]), int(line[2]))
          self.verify(pos, self.walls, k)
          self.walls.add(pos)

        elif line[0] == 'HWALL':
          row = int(line[1])
          for i in range(int(line[2]), int(line[3])+1):
            pos = (row, i)
            self.verify(pos, self.walls, k)
            self.walls.add(pos)

        elif line[0] == 'VWALL':
          col = int(line[1])
          for i in range(int(line[2]), int(line[3])+1):
            pos = (i, col)
            self.verify(pos, self.walls, k)
            self.walls.add(pos)


        elif line[0] == 'PENALWATER':
          self.penalWater = max(1.0, float(line[1]))

        elif line[0] == 'WATER':
          pos = (int(line[1]), int(line[2]))
          self.verify(pos, self.water, k)
          self.water.add(pos)

        elif line[0] == 'HWATER':
          row = int(line[1])
          for i in range(int(line[2]), int(line[3])+1):
            pos = (row, i)
            self.verify(pos, self.water, k)
            self.water.add(pos)

        elif line[0] == 'VWATER':
          col = int(line[1])
          for i in range(int(line[2]), int(line[3])+1):
            pos = (i, col)
            self.verify(pos, self.water, k)
            self.water.add(pos)


        elif line[0] == 'GRASS':
          pos = (int(line[1]), int(line[2]))
          self.verify(pos, self.grass, k)
          self.grass.add(pos)

        elif line[0] == 'HGRASS':
          row = int(line[1])
          for i in range(int(line[2]), int(line[3])+1):
            pos = (row, i)
            self.verify(pos, self.grass, k)
            self.grass.add(pos)

        elif line[0] == 'VGRASS':
          col = int(line[1])
          for i in range(int(line[2]), int(line[3])+1):
            pos = (i, col)
            self.verify(pos, self.grass, k)
            self.grass.add(pos)


        elif line[0] == 'FLOOR':
          pos = (int(line[1]), int(line[2]))
          self.verify(pos, self.floor, k)
          self.floor.add(pos)

        elif line[0] == 'HFLOOR':
          row = int(line[1])
          for i in range(int(line[2]), int(line[3])+1):
            pos = (row, i)
            self.verify(pos, self.floor, k)
            self.floor.add(pos)

        elif line[0] == 'VFLOOR':
          col = int(line[1])
          for i in range(int(line[2]), int(line[3])+1):
            pos = (i, col)
            self.verify(pos, self.floor, k)
            self.floor.add(pos)

        
        elif line[0] == 'PORTAL':
          pos1 = (int(line[1]), int(line[2]))
          pos2 = (int(line[3]), int(line[4]))
          self.verify(pos1, set(), k)
          self.verify(pos2, set(), k)
          self.portals[pos1] = (pos2, self.nPortals)
          self.portals[pos2] = (pos1, self.nPortals)
          self.nPortals += 1

      if self.pos in self.walls:
        print(
          f'\033[1;31mError.\033[0m El estado inicial no se puede encontrar en una pared.',
          file=stderr
        )

  def reward(self, state: Tuple[int, int]) -> int:
    """
      Recompensa que se obtiene al moverse desde un estado.

      Argumentos:
        state: Tuple[int, int]  ->  Estado desde el que se movera.
    """
    if state in self.water: return -1 - self.penalWater 
    elif state in self.floor: return -0.05
    else: return -1

class MDP:
  """
    Implementacion de un Markov Decision Process sobre una cuadricula con paredes,
    agua, grama, piso liso y portales.
  """
  def __init__(
      self, world: World, 
      gamma: float=1.0, 
      errorRate: float=0.0, 
      sleepTime: float=0.5
  ):
    """
      Inicializacion del MDP

      Argumentos:
        world: World  ->  Mapa sobre el que se movera el agente.
        gamma: float  ->  Factor de desvanecimiento. Valor por defecto: 1.0
        errorRate: float  ->  Factor de error del agente. Valor por defecto: 0.0
        sleepTime: float  ->  Tiempo que se esperara entre cada movimiento del agente
    """
    self.world = world
    self.gamma = gamma
    self.errorRate = errorRate
    self.values = [[-1]*self.world.N for _ in range(self.world.M)]
    for goal in self.world.goals:
      self.values[goal[0]][goal[1]] = 0
    self.pos = (-1,-1)
    self.sleepTime = sleepTime

  def verifyPortal(self, pos: Tuple[int, int]) -> Tuple[int, int]:
    """
      Verifica que en una posicion es un portal. Si es asi, retorna la 
      posicion a la que apunta, si no, retorna la misma posicion.
    """
    if pos in self.world.portals: return self.world.portals[pos][0]
    else: return pos
    
  def getStates(self, state: Tuple[int, int], action: int) -> List[Tuple[Tuple[int, int], int]]:
    """
      Dado un estado y una accion, obtenemos los estados adyacentes y la probabilidad de
      movernos hacia ellos.

      Argumentos:
        state: Tuple[int, int]  ->  Estado inicial.
        action: int ->  Movimiento.
      Salida:
        List[Tuple[Tuple[int, int], int]] ->  Lista de tuplas (s, p) tal que s es una estado
            adyacente al estado inicial y p la probabilidad de moverse a ese estado siguiendo
            la accion a.
    """
    states = []

    # Estado resultante de moverse hacia arriba.
    y, x = state[0] - (state[0] > 0), state[1]
    if (y, x) in self.world.walls: y, x = state[0], state[1]
    y, x = self.verifyPortal((y, x))
    p = self.errorRate / 4 + (action == TOP) * (1 - self.errorRate)
    states.append(((y, x), p))

    # Estado resultante de moverse hacia la derecha.
    y, x = state[0], state[1] + (state[1] < self.world.N-1)
    if (y, x) in self.world.walls: y, x = state[0], state[1]
    y, x = self.verifyPortal((y, x))
    p = self.errorRate / 4 + (action == RIGHT) * (1 - self.errorRate)
    states.append(((y, x), p))

    # Estado resultante de moverse hacia abajo.
    y, x = state[0] + (state[0] < self.world.M-1), state[1]
    if (y, x) in self.world.walls: y, x = state[0], state[1]
    y, x = self.verifyPortal((y, x))
    p = self.errorRate / 4 + (action == DOWN) * (1 - self.errorRate)
    states.append(((y, x), p))

    # Estado resultante de moverse hacia la izquierda.
    y, x = state[0], state[1] - (state[1] > 0)
    if (y, x) in self.world.walls: y, x = state[0], state[1]
    y, x = self.verifyPortal((y, x))
    p = self.errorRate / 4 + (action == LEFT) * (1 - self.errorRate)
    states.append(((y, x), p))

    return states

  def VI(self):
    """
      Aplicamos una iteracion para actualizar el valor de los estados.
    """
    # Aqui almacenaremos los nuevos valores de estados.
    new_values = [[0]*self.world.N for _ in range(self.world.M)]
    for m in range(self.world.M):
      for n in range(self.world.N):
        # Por cada posible estado
        state = (m, n)

        # Si el estado se encuentra en grama, entonces el nuevo valor sera el promedio
        # de los valores obtenidos por cada accion
        if state in self.world.grass:
          new_values[m][n] = 0
          for a in ACTIONS:
            for s, p_s in self.getStates(state, a):
              # Actualizamos el valor del estado (m,n)
              new_values[m][n] += p_s * (self.world.reward(state) + self.gamma * self.values[s[0]][s[1]]) / 4

        # En caso contrario, si no es una pared ni un GOAL, se toma la accion que maximice
        # el valor de estado
        elif not state in self.world.walls and not state in self.world.goals:
          new_values[m][n] = -float('inf')
          for a in ACTIONS:
            value_a = 0
            for s, p_s in self.getStates(state, a):
              # Actualizamos el valor del estado (m,n)
              value_a += p_s * (self.world.reward(state) + self.gamma * self.values[s[0]][s[1]])
            new_values[m][n] = max(new_values[m][n], value_a)

    self.values = new_values

  def updateValue(self, state: Tuple[int, int]):
    """
      Actualiza el valor de estado de una sola casilla.
    """
    new_value = 0

    # Si el estado se encuentra en grama, entonces el nuevo valor sera el promedio
    # de los valores obtenidos por cada accion
    if state in self.world.grass:
      for a in ACTIONS:
        for s, p_s in self.getStates(state, a):
          # Actualizamos el valor del estado (m,n)
          new_value += p_s * (self.world.reward(state) + self.gamma * self.values[s[0]][s[1]]) / 4

    # En caso contrario, si no es una pared ni un GOAL, se toma la accion que maximice
    # el valor de estado
    elif not state in self.world.walls and not state in self.world.goals:
      new_value = -float('inf')
      for a in ACTIONS:
        value_a = 0
        for s, p_s in self.getStates(state, a):
          # Actualizamos el valor del estado (m,n)
          value_a += p_s * (self.world.reward(state) + self.gamma * self.values[s[0]][s[1]])
        new_value = max(new_value, value_a)

    self.values[state[0]][state[1]] = new_value
 
  def printWorld(self):
    """
      Imprime una representacion del mapa actual coloreando los estados tal que
      mientras mas claro, mayor valor. Los tonos grises son estados normales, los
      numerales son paredes y los tonos azules son charcos.
    """
    # Obtenemos el peor valor del estado.
    worst = min([min(v) for v in self.values])
    if worst == 0: worst = 1

    mapStr = '┌' + '─'*3*self.world.N + '┐\n'
    for m in range(self.world.M):
      mapStr += '│'
      for n in range(self.world.N):
        if (m,n) in self.world.walls:
          mapStr += f'\033[1m\033[38;2;60;37;13m@@ \033[0m'

        elif (m,n) == self.pos:
          mapStr += f'\033[1m\033[38;2;255;0;0mMM \033[0m'

        elif (m,n) in self.world.goals:
          mapStr += f'\033[1m\033[38;2;255;255;255mGG \033[0m'

        elif (m,n) in self.world.grass:
          val = self.values[m][n]
          colorRatio = (val / worst) ** (1/1.35)
          color = max(0, int(255 * (1 - colorRatio)))
          mapStr += f'\033[1m\033[38;2;{color};255;{color}mWW \033[0m'

        elif (m,n) in self.world.water:
          val = self.values[m][n]
          colorRatio = (val / worst) ** (1/1.35)
          color = max(0, int(255 * (1 - colorRatio)))
          mapStr += f'\033[1m\033[38;2;{color};{color};255m~~ \033[0m'

        elif (m,n) in self.world.floor:
          val = self.values[m][n]
          colorRatio = (val / worst) ** (1/1.35)
          color = max(0, int(255 * (1 - colorRatio)))
          mapStr += f'\033[1m\033[38;2;{color};{color};{color}m|| \033[0m'

        elif (m,n) in self.world.portals:
          val = self.values[m][n]
          colorRatio = (val / worst) ** (1/1.35)
          color = max(0, int(255 * (1 - colorRatio)))

          index = self.world.portals[(m,n)][1]
          if index < 10: index = f'0{index}'
          else: index = str(index)

          mapStr += f'\033[1m\033[38;2;{color};0;{color}m{index} \033[0m'

        else:
          val = self.values[m][n]
          colorRatio = (val / worst) ** (1/1.35)
          color = max(0, int(255 * (1 - colorRatio)))
          mapStr += f'\033[1m\033[38;2;{color};{color};{color}m## \033[0m'
      mapStr += '│\n'
    mapStr += '└' + '─'*3*self.world.N + '┘\n'

    print(mapStr)

  def viewUpdates(self, k: int):
    """
      Actualiza los valores de estados k veces e imprime la representacion de los 
      estados en cada iteracion.
    """
    for i in range(k):
      self.VI()
      print('\033[H\033[2J\n')
      self.printWorld()
      print(f'ITERATION: {i} / {k}')
      sleep(self.sleepTime)

  def RTDP(self) -> int:
    """
      Realiza un movimiento en base a los valores de estado aprendidos usando
      Real Time Dinamyc Programming. Retorna el movimiento escogido.
    """
    probs = []

    X = [None]*4
    Y = [None]*4

    # Almacenamos el valor de los estados resultantes al realizar cada accion.
    Y[0], X[0] = self.pos[0] - (self.pos[0] > 0), self.pos[1]
    if (Y[0], X[0]) in self.world.walls: Y[0], X[0] = self.pos[0], self.pos[1]
    Y[0], X[0] = self.verifyPortal((Y[0], X[0]))
    probs.append(self.values[Y[0]][X[0]])

    Y[1], X[1] = self.pos[0], self.pos[1] + (self.pos[1] < self.world.N-1)
    if (Y[1], X[1]) in self.world.walls: Y[1], X[1] = self.pos[0], self.pos[1]
    Y[1], X[1] = self.verifyPortal((Y[1], X[1]))
    probs.append(self.values[Y[1]][X[1]])

    Y[2], X[2] = self.pos[0] + (self.pos[0] < self.world.M-1), self.pos[1]
    if (Y[2], X[2]) in self.world.walls: Y[2], X[2] = self.pos[0], self.pos[1]
    Y[2], X[2] = self.verifyPortal((Y[2], X[2]))
    probs.append(self.values[Y[2]][X[2]])

    Y[3], X[3] = self.pos[0], self.pos[1] - (self.pos[1] > 0)
    if (Y[3], X[3]) in self.world.walls: Y[3], X[3] = self.pos[0], self.pos[1]
    Y[3], X[3] = self.verifyPortal((Y[3], X[3]))
    probs.append(self.values[Y[3]][X[3]])

    real_probs = [0]*4
    for i in range(4):
      real_probs[i] = sum([
        p * (self.errorRate / 4 + (k == i) * (1 - self.errorRate)) for k, p in enumerate(probs)
      ])
    probs = real_probs

    if self.pos in self.world.grass: 
      # Agarramos una accion aleatoria
      action = choices(ACTIONS, weights=[0.25]*4, k=1)[0]
    else:
      # Agarramos la accion que nos de mayor valor
      maxP = max(probs)
      action = choices([i for i,p in enumerate(probs) if p == maxP], k=1)[0]

    # Probabilidad de error
    action = choices(
      ACTIONS, 
      weights=[self.errorRate / 4 + (a == action) * (1 - self.errorRate) for a in ACTIONS],
      k=1
    )[0]

    # Actualizamos el valor de la posicion
    self.updateValue(self.pos)

    # Actualizamos la posicion
    self.pos = (Y[action], X[action])

    return action

  def play(self):
    """
      Inicia la secuencia de movimiento a realizar por el agente en base a los 
      valores de estado aprendidos. Se imprime el mapa por cada movimiento.
      Se seguira ejecutando hasta que el agente alcance alguna meta.
    """
    self.pos = self.world.pos
    totalCost = 0

    # Imprimimos el mapa inicial.
    print('\033[H\033[2J\n')
    self.printWorld()
    print('GO!!!')
    sleep(self.sleepTime)

    nMoves = 0
    # Imprimimos el mapa luego de cada movimiento hasta que alcance una meta.
    while not self.pos in self.world.goals:
      print('\033[H\033[2J\n')
      totalCost += self.world.reward(self.pos)
      a = self.RTDP()
      self.printWorld()

      # Imprimimos el movimiento escogido.
      if a == TOP:      print('ACTION: TOP')
      elif a == RIGHT:  print('ACTION: RIGHT')
      elif a == DOWN:   print('ACTION: DOWN')
      elif a == LEFT:   print('ACTION: LEFT')
      print(f'CURRENT COST: {round(totalCost, 2)}')

      nMoves += 1
      sleep(self.sleepTime)

    print(
      f'\nSe alcanzo la meta en \033[1m{nMoves}\033[0m movimientos, con un costo ' +\
      f'total de \033[1m{round(totalCost, 2)}\033[0m.'
    )


if __name__ == '__main__':
  if len(argv) != 4 and len(argv) != 5:
    print(
      f'\033[1;31mError.\033[0m Sintaxis invalida. Ejecute el script como\n\n' +\
      '    \033[1mpython ForestTilesMDP.py\033[0m \033[4mWORLD_FILE\033[0m ' +\
      '\033[4mITERATIONS\033[0m \033[4mERROR_RATE\033[0m [ \033[4mSLEEP_TIME\033[0m ]',
      file=stderr
    )
    exit(1)

  if len(argv) == 5: sleepTime = float(argv[4])
  else: sleepTime = 0.5

  # Archivo con la descripcion del tile.
  worldFile = argv[1]
  # Numero de iteraciones en las que se aplicara VI.
  iterations = int(argv[2])
  # Probabilidad de escoger una accion aleatoria.
  errorRate = float(argv[3])

  world = World()
  world.read(worldFile)
  mdp = MDP(world, 1, errorRate, sleepTime)
  mdp.viewUpdates(iterations)
  mdp.play()
