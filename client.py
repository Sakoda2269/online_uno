import websocket
import time
import json
import threading
from sortedcollections import SortedList
import random
import msvcrt
import sys

kind_od_cards = set()
for c in {"r", "g", "b", "y"}:
    kind_od_cards |= {f"{c}{i}" for i in range(10)}
    kind_od_cards |= {f"{c}{s}" for s in {"d", "s", "r"}}
kind_od_cards.add("wi")
kind_od_cards.add("wd")
kind_od_cards.add("sw")

class UNO_client:

    myid = ""
    myname = ""
    is_host = False

    waiting_player = True
    my_cards = SortedList()
    now_turn = ""
    is_myturn = False
    start_thred = threading.Thread()
    table_card = ""
    card_processed = False
    cards = []
    num_card = {}

    global kind_od_cards

    def on_message(self, ws, message):
        data = json.loads(message)
        if data["method"] == "join":
            self.myid = data["data"][0]
            self.is_host = data["data"][1]
            self.myname = input("input your name >> ")
            ws.send(self.dataGen("join", self.myname))
        
        if data["method"] == "start":
            self.start_thred = threading.Thread(target=self.start_UNO, args=(data,))
            self.start_thred.start()
        
        if data["method"] == "shuffle":
            print("手札がシャッフルされました！")
            self.my_cards = SortedList(data["data"])
            print(*self.my_cards)

        if data["method"] == "turn":
            if self.uno_thread != None:
                if self.uno_thread.is_alive():
                    self.uno_thread.join()
            if data["data"]["turn_id"] == self.myid:
                self.is_myturn = True
            else:
                self.is_myturn = False
            self.now_turn = data["data"]["turn_name"]
            self.table_card = data["data"]["table_card"]
            self.card_processed = data["data"]["processed"]
            self.cards = data["data"]["cards"]
            self.num_card = data["data"]["num_card"]
            self.UNO_turn(ws, data)
        
        if data["method"] == "wild":
            print("最初のカードはワイルドでした！")
            color = self.wild_color()
            ws.send(self.dataGen("wild", color))

        if data["method"] == "message":
            print("\n=================\n")
            print(data["data"])
            print("\n=================")
        pass

    def on_error(self, ws, error):
        print(error)

    def on_close(self, ws, close_status_code, close_msg):
        print("### 切断しました ###")

    def on_open(self, ws):
        self.uno_thread = threading.Thread(target=self.UNO, args=(ws,))
        self.uno_thread.start()
        pass

    def UNO(self, ws):
        self.wait_player(ws)
        self.start_thred.join()
        self.UNO_turn(ws)
    
    def UNO_turn(self, ws, data={}):
        if self.is_myturn:
            print("あなたのターンです！")
            print(f"場のカードは {self.table_card} です！")
            print("あなたのカード")
            print(*list(map(lambda x: x.rjust(3), self.my_cards)))
            if self.card_processed == False:
                if self.table_card[1] == "s":
                    ws.send(self.dataGen("turn", {"act":"skip", "card":""}))
                    print("あなたのターンはスキップされました！")
                    return
                elif self.table_card[0] != "w" and self.table_card[1] == "d":
                    print("あなたはカードを2枚引きました！")
                    draws = []
                    for i in range(2):
                        new_card = self.get_card()
                        draws.append(new_card)
                        self.my_cards.add(new_card)
                        print(f"引いたカードは{new_card}です!")
                    ws.send(self.dataGen("turn", {"act":"d2", "card":draws}))
                    return
                elif self.table_card == "wd":
                    print("あなたはカードを4枚引きました！")
                    draws = []
                    color = data["data"]["color"]
                    for i in range(4):
                        new_card = self.get_card()
                        draws.append(new_card)
                        self.my_cards.add(new_card)
                        print(f"引いたカードは {new_card}です!")
                    ws.send(self.dataGen("turn", {"act":"d4", "card":draws, "color":color}))
                    return
                elif self.table_card == "wi":
                    color = self.wild_color()
                    self.table_card = color + "*"
                    print(f"場のカードは{self.table_card}です")
                    print("あなたのカード")
                    print(*list(map(lambda x: x.rjust(3), self.my_cards)))
                    

                
            print(*[str(i).rjust(3) for i in range(len(self.my_cards))])
            select = input("出すカードの番号を選ぶか、-1でカードを1枚引くか、ほかのcommandを入力してください。helpを入力するとほかのcommand一覧を表示します。\n>> ").split()
            while True:
                select_num = select[0]
                try:
                    card_num = int(select_num)
                except Exception:
                    self.command(select)
                    select = input("出すカードの番号を選ぶか、-1でカードを1枚引くか、ほかのcommandを入力してください。helpを入力するとほかのcommand一覧を表示します。\n>> ").split()
                    continue
                if card_num >= len(self.my_cards):
                    select = input("出すカードの番号を選ぶか、-1でカードを1枚引くか、ほかのcommandを入力してください。helpを入力するとほかのcommand一覧を表示します。\n>> ").split()
                    continue
                elif card_num <= -2:
                    select = input("出すカードの番号を選ぶか、-1でカードを1枚引くか、ほかのcommandを入力してください。helpを入力するとほかのcommand一覧を表示します。\n>> ").split()
                    continue
                elif card_num == -1:
                    new_card = self.get_card()
                    print(f"あなたが引いたカードは {new_card}でした!")
                    if self.card_validation(new_card):
                        self.my_cards.add(new_card)
                        ws.send(self.dataGen("turn", {"act":"d1", "card":[new_card]}))
                        return
                    else:
                        print("このカードは出すことができます!")
                        act = input("出しますか?(y/n)\n>> ")
                        while act not in {"y", "n"}:
                            act = input("出しますか?(y/n)\n>> ")
                        if act == "n":
                            ws.send(self.dataGen("turn", {"act":"d1", "card":[new_card]}))
                            self.my_cards.add(new_card)
                            return
                        else:
                            if new_card in {"wi", "sw", "wd"}:
                                color = self.wild_color()
                                ws.send(self.dataGen("turn", {"act":"draw_trash", "card":new_card, "color":color}))
                            else:
                                ws.send(self.dataGen("turn", {"act":"draw_trash", "card":new_card}))
                            return
                else:
                    select_card = self.my_cards[card_num]
                    if self.card_validation(select_card):
                        print(f"{select_card}は出すことができません!")
                        select = input("出すカードの番号を選ぶか、-1でカードを1枚引くか、ほかのcommandを入力してください。helpを入力するとほかのcommand一覧を表示します。\n>> ").split()
                        continue
                    self.my_cards.remove(select_card)
                    if select_card not in {"wi", "ww", "sw", "wd"}:
                        ws.send(self.dataGen("turn", {"act":"trash", "card":select_card}))
                    elif select != "ww":
                        color = self.wild_color()
                        ws.send(self.dataGen("turn", {"act":"trash", "card":select_card, "color":color}))
                    return

        else:
            print(f"{self.now_turn}のターンです! ")
            print("コマンド入力ができます。helpでコマンド一覧を表示します。")
            self.wait_thread = threading.Thread(target=self.wait_turn)
            self.wait_thread.start()

    def wait_player(self, ws):
        started = False
        while self.waiting_player:
            if self.is_host and not started:
                act = input()
                if act == "start":
                    started = True
                    ws.send(self.dataGen("start", ""))
            else:
                time.sleep(1)
    
    def start_UNO(self, data):
        self.waiting_player = False
        self.my_cards = SortedList(data["data"]["your_cards"])
        self.now_turn = data["data"]["now_turn_name"]
        self.is_myturn = data["data"]["now_turn_id"] == self.myid
        self.table_card = data["data"]["table_card"]
        self.card_processed = data["data"]["processed"]
        self.cards = data["data"]["cards"]
        print("\n=================\n")
        print("game start!")
        print("\n=================\n")
        print(f"場のカードは{self.table_card}です!")
        print("\n=================\n")
        print("あなたのカード")
        print(*self.my_cards, sep=" ")
        print("\n=================")
    
    def wild_color(self):
        color = input("好きな色を指定してください。(r, g, b, y) >> ")
        while color not in {"r", "g", "b", "y"}:
            color = input("好きな色を指定してください。(r, g, b, y) >> ")
        return color
    
    def get_card(self):
        tmp = random.choice(self.cards)
        self.cards.remove(tmp)
        return tmp
    
    def command(self, com):
        if com[0] == "help":
            print("=========================================", flush=True)
            print("enemy : プレイヤーのカードの枚数一覧を表示します", flush=True)
            print("card [card_name]: 指定したカードの効果を表示します", flush=True)
            print("mycard : あなたの手札を表示します", flush=True)
            print("now : 場のカードを表示します")
            print("exit:ゲームを終了します")
            print("=========================================", flush=True)
        elif com[0] == "enemy":
            for p in self.num_card:
                print(p + ":" + str(self.num_card[p]), flush=True)
        elif com[0] == "mycard":
            print(*list(map(lambda x: x.rjust(3), self.my_cards)), flush=True)
            print(*[str(i).rjust(3) for i in range(len(self.my_cards))], flush=True)
        elif com[0] == "now":
            print(f"場のカードは{self.table_card}です。")
        elif com[0] == "exit":
            act = input("本当に終了しますか？(y/n)\n>>")
            while act not in {"y", "n"}:
                act = input("本当に終了しますか？(y/n)\n>>")
            if act == "y":
                exit()
        elif com[0] == "card":
            try:
                card = com[1]
                if card in kind_od_cards:
                    colors = {"r":"赤", "g":"緑", "b":"青", "y":"黄"}
                    if card[0] in colors:
                        color = colors[card[0]]
                        if card[1] == "s":
                            print(f"{card} は{color}のスキップです。次のプレイヤーは行動できず、その次のプレイヤーのターンになります。", flush=True)
                        elif card[1] == "d":
                            print(f"{card} は{color}のドロー2です。次のプレイヤーは行動できずカードを2枚引き、その次のプレイヤーのターンになります。", flush=True)
                        elif card[1] == "r":
                            print(f"{card} は{color}のリバースです。順番が逆になります。", flush=True)
                        elif card[1] == "*":
                            print(f"{card} はワイルドでプレイヤーが決めた色です。{color}であれば手札のカードを場に出すことができます。", flush=True)
                        else:
                            print(f"{card} は{color} の {card[1]} です。", flush=True)
                    else:
                        if card == "wi":
                            print("wi はワイルドです。場にどんなカードがあっても出せます。好きな色を指定できます。", flush=True)
                        elif card == "wd":
                            print("wd はワイルドドロー4です。場にどんなカードがあっても出せます。好きな色を指定できます。次のプレイヤーは行動できずカードを4枚引き、その次のプレイヤーのターンになります。", flush=True)
                        elif card == "sw":
                            print("sw はシャッフルワイルドです。場にどんなカードがあっても出せます。好きな色を指定できます。すべてのプレイヤーの手札を集め、シャッフルし配りなおします。手札の枚数は変わりません。", flush=True)
                else:
                    print("そんなカードはありません!", flush=True)
            except Exception:
                print("カードの名前を入力してください！")
        pass
    
    def card_validation(self, card):
    #カードが出せないならTrue
        return card not in {"wi", "wd", "ww", "sw"} and card[0] != self.table_card[0] and card[1] != self.table_card[1]
    
    def wait_turn(self):
        tmp = ""
        while not self.is_myturn:
            if msvcrt.kbhit():
                input_tmp = msvcrt.getch()
                str_tmp = input_tmp.decode("UTF=8")
                print(str_tmp, end="", flush=True)
                if input_tmp == b'\r':
                    print()
                    self.command(tmp.split())
                    tmp = ""
                elif input_tmp == b"\x08":
                    tmp = tmp[:-1]
                    sys.stdout.write("\033[2K\033[G")
                    sys.stdout.flush()
                    print(tmp, end="", flush=True)
                else:
                    tmp += str_tmp

    
    def dataGen(self, method, data):
        return json.dumps({
            "method" : method,
            "id" : self.myid,
            "data" : data
        })

if __name__ == "__main__":
    websocket.enableTrace(False)
    uno = UNO_client()
    ws = websocket.WebSocketApp("ws://127.0.0.1:13254",
                                on_open=uno.on_open,
                                on_message=uno.on_message,
                                on_error=uno.on_error,
                                on_close=uno.on_close)

    ws.run_forever()