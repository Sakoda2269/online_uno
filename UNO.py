import random
from collections import deque
players = {f"{i}" : 1 for i in range(4)}
order = deque()
player_tmp = list(players.keys())

while player_tmp:
    tmp = random.choice(player_tmp)
    order.append(tmp)
    player_tmp.remove(tmp)
print(order)