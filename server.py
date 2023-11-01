import logging
from websocket_server import WebsocketServer
import json
import uuid
import random
from collections import deque
import time
import threading



class UNO_server:
    players = {} # id : (client, name)
    player_name = {}
    player_card = {}
    host_id = ""
    wait_recv = False
    wild = ""

    cards = []
    order = deque()
    table_card = ""

    def new_client(self, client, server):
        new_id = str(uuid.uuid4())
        self.players[new_id] = client
        if len(self.players) == 1:
            self.host_id = new_id
        server.send_message(client, self.dataGen("join", [new_id, self.host_id == new_id]))
        pass

    def on_recieve(self, client, server, message):
        data = json.loads(message)
        if data["method"] == "join":
            self.player_name[data["id"]] = data["data"]
            server.send_message_to_all(self.dataGen("message", f"{data['data']} joined this game!"))

        if data["method"] == "start":
            start_thread = threading.Thread(target=self.start_UNO, args=(server,))
            start_thread.start()
        
        if data["method"] == "turn":
            num_card = {}
            for p in self.players:
                num_card[self.player_name[p]] = len(self.player_card[p])
            if data["data"]["act"] == "skip":
                tmp = self.order.popleft()
                self.order.append(tmp)
                server.send_message_to_all(self.dataGen("message", 
                                                        f"{self.player_name[tmp]}'s turn has been skiped!"))
                server.send_message_to_all(self.dataGen("turn", {
                    "turn_id":self.order[0],
                    "turn_name":self.player_name[self.order[0]],
                    "table_card":self.table_card,
                    "processed":True,
                    "cards":self.cards,
                    "num_card":num_card
                }))
            if data["data"]["act"] in {"d1", "d2", "d4"}:
                tmp = self.order.popleft()
                self.order.append(tmp)
                server.send_message_to_all(self.dataGen("message", 
                        f"{self.player_name[tmp]} draw {data['data']['act'][1]} card!"))
                for c in data["data"]["card"]:
                    self.player_card[tmp].append(c)
                    self.cards.remove(c)
                if data["data"]["act"] == "d4":
                    self.table_card = data["data"]["color"] + "*"
                    server.send_message_to_all(self.dataGen("turn", {
                        "turn_id":self.order[0],
                        "turn_name":self.player_name[self.order[0]],
                        "table_card":self.table_card,
                        "processed":True,
                        "cards":self.cards,
                        "num_card":num_card
                    }))
                else:
                    server.send_message_to_all(self.dataGen("turn", {
                        "turn_id":self.order[0],
                        "turn_name":self.player_name[self.order[0]],
                        "table_card":self.table_card,
                        "processed":True,
                        "cards":self.cards,
                        "num_card":num_card
                    }))
            if data["data"]["act"] == "draw_trash":
                tmp = self.order.popleft()
                self.order.append(tmp)
                self.table_card = data["data"]["card"]
                self.cards.remove(data["data"]["card"])
                server.send_message_to_all(self.dataGen("message",
                                f"{self.player_name[tmp]} draw {data['data']['card']} and trash it!"))
                if data["data"]["card"] == "wd":
                    server.send_message_to_all(self.dataGen("message",
                                f"{self.player_name[tmp]} select {data['data']['color']}!"))
                    server.send_message_to_all(self.dataGen("turn", {
                        "turn_id":self.order[0],
                        "turn_name":self.player_name[self.order[0]],
                        "table_card":self.table_card,
                        "processed":False,
                        "cards":self.cards,
                        "color":data['data']['color'],
                        "num_card":num_card
                    }))
                elif data["data"]["card"] in {"wi", "sw"}:
                    server.send_message_to_all(self.dataGen("message",
                                f"{self.player_name[tmp]} select {data['data']['color']}!"))
                    self.table_card = data["data"]["color"] + "*"
                    server.send_message_to_all(self.dataGen("turn", {
                        "turn_id":self.order[0],
                        "turn_name":self.player_name[self.order[0]],
                        "table_card":self.table_card,
                        "processed":False,
                        "cards":self.cards,
                        "color":data['data']['color'],
                        "num_card":num_card
                    }))
                else:
                    server.send_message_to_all(self.dataGen("turn", {
                        "turn_id":self.order[0],
                        "turn_name":self.player_name[self.order[0]],
                        "table_card":self.table_card,
                        "processed":False,
                        "cards":self.cards,
                        "num_card":num_card
                    }))
            if data["data"]["act"] == "trash":
                tmp = self.order.popleft()
                if data["data"]["card"][1] == "r":
                    self.rev()
                self.order.append(tmp)
                self.table_card = data["data"]["card"]
                self.player_card[tmp].remove(data["data"]["card"])
                server.send_message_to_all(self.dataGen("message",
                                f"{self.player_name[tmp]} trash {data['data']['card']}!"))
                if len(self.player_card[tmp]) <= 0:
                    server.send_message_to_all(self.dataGen("message",
                                    self.player_name[tmp] + "win!!")) 
                    exit()
                if data["data"]["card"] == "wd":
                    server.send_message_to_all(self.dataGen("message",
                                f"{self.player_name[tmp]} select {data['data']['color']}!"))
                    server.send_message_to_all(self.dataGen("turn", {
                        "turn_id":self.order[0],
                        "turn_name":self.player_name[self.order[0]],
                        "table_card":self.table_card,
                        "processed":False,
                        "cards":self.cards,
                        "color":data['data']['color'],
                        "num_card":num_card
                    }))
                elif data["data"]["card"] == "wi":
                    server.send_message_to_all(self.dataGen("message",
                                f"{self.player_name[tmp]} select {data['data']['color']}!"))
                    self.table_card = data["data"]["color"] + "*"
                    server.send_message_to_all(self.dataGen("turn", {
                        "turn_id":self.order[0],
                        "turn_name":self.player_name[self.order[0]],
                        "table_card":self.table_card,
                        "processed":False,
                        "cards":self.cards,
                        "color":data['data']['color'],
                        "num_card":num_card
                    }))
                elif data["data"]["card"] == "sw":
                    server.send_message_to_all(self.dataGen("message",
                                f"{self.player_name[tmp]} select {data['data']['color']}!"))
                    self.shuffle()
                    self.table_card = data["data"]["color"] + "*"
                    for p, cli in self.players.items():
                        server.send_message(cli, self.dataGen("shuffle", 
                                                              self.player_card[p]))
                    server.send_message_to_all(self.dataGen("turn", {
                        "turn_id":self.order[0],
                        "turn_name":self.player_name[self.order[0]],
                        "table_card":self.table_card,
                        "processed":False,
                        "cards":self.cards,
                        "color":data['data']['color'],
                        "num_card":num_card
                    }))
                else:
                    server.send_message_to_all(self.dataGen("turn", {
                        "turn_id":self.order[0],
                        "turn_name":self.player_name[self.order[0]],
                        "table_card":self.table_card,
                        "processed":False,
                        "cards":self.cards,
                        "num_card":num_card
                    }))
        
        if data["method"] == "wild":
            self.wild = data["data"]
            self.wait_recv = False
        
    def start_UNO(self, server):
        # 山札の作成
        for c in ["r", "g", "b", "y"]:
            self.cards += [f"{c}0"]
            self.cards += [f"{c}{i}" for i in range(1, 9)]
            self.cards += [f"{c}{i}" for i in range(1, 9)]
            self.cards += [f"{c}{i}" for i in ["s", "r", "d"]]
        self.cards += ["wi" for i in range(4)]
        self.cards += ["wd" for i in range(4)]
        self.cards += ["sw" for i in range(1)]
        # self.cards += ["ww" for i in range(3)]

        # 手札をプレイヤーに配る
        for p in self.players:
            self.player_card[p] = []
            for i in range(7):
                self.player_card[p].append(self.get_card(self.cards))
        
        # 順番の決定
        tmp_players = list(self.players.keys())
        while tmp_players:
            tmp = random.choice(tmp_players)
            tmp_players.remove(tmp)
            self.order.append(tmp)
        
        # 最初の場札
        self.table_card = self.get_card(self.cards)
        self.table_card = "rs"
        while True:
            if self.table_card not in ["wd", "ww", "sw"]:
                break
            self.table_card = self.get_card(self.cards)

        now_turn_name = self.player_name[self.order[0]]
        now_turn_id = self.order[0]
        for p in self.players:
            sendData = {
                "your_cards" : self.player_card[p],
                "now_turn_name" : now_turn_name,
                "now_turn_id" : now_turn_id,
                "table_card" : self.table_card,
                "processed" : False,
                "cards" : self.cards
            }
            server.send_message(self.players[p], self.dataGen("start", sendData))
        
        
        # if self.table_card[1] == "r":
        #     self.rev()
        # if self.table_card[1] == "s":
        #     self.skip()
        # if self.table_card[1] == "d":
        #     self.draw2()
        # if self.table_card == "wi":
        #     now = self.order[0]
        #     server.send_message(self.players[now], self.dataGen("wild", ""))
        #     self.wait_recv = True
        #     while self.wait_recv:
        #         time.sleep(1)
        #     color = self.wild
        #     self.table_card = f"{color}*"
        
        
    def get_card(self, cards):
        tmp = random.choice(cards)
        cards.remove(tmp)
        return tmp
    
    def rev(self):
        print("=========================================\n")
        self.order = deque(list(self.order)[::-1])
        print("order was reversed!\n")
    
    def shuffle(self):
        cards_list = []
        playercard_num = {}
        for p in self.player_card:
            playercard_num[p] = len(self.player_card[p])
            while self.player_card[p]:
                cards_list.append(self.player_card[p].pop())
        while cards_list:
            for p in self.player_card:
                if playercard_num[p] == 0:
                    continue
                self.player_card[p].append(self.get_card(cards_list))
                playercard_num[p] -= 1

    def dataGen(self, method, data):
        return json.dumps({
            "method" : method,
            "data" : data
        })

server = WebsocketServer(port = 13254, host='127.0.0.1', loglevel=logging.INFO)
uno = UNO_server()
server.set_fn_new_client(uno.new_client)
server.set_fn_message_received(uno.on_recieve)
server.run_forever()