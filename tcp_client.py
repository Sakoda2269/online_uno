import socket
import json

HOST = "127.0.0.1"
PORT = 8000
BUFSIZE = 4096

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

client.connect((HOST, PORT))

while True:
    act = input()
    if act=="hello":
        client.sendall(b"hello")
    if act == "exit":
        break
    data = client.recv(BUFSIZE)
    print(data)
# print(json.loads(data.decode("UTF-8")))

client.close()
