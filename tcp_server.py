import socket
import json

PORT = 8000
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
BUFSIZE = 4096

connection_num = 0

server.bind(("", PORT))

server.listen()
sock, client = server.accept()

while True:
    data = sock.recv(BUFSIZE)
    connection_num += 1
    print(connection_num)
    # data = {
    #     "method" : "hello",
    #     "data" : {
    #         "a" : "aljdkfs",
    #         "b" : "aj;lfd"
    #     }
    # }
    # sock.sendall(json.dumps(data).encode("UTF-8"))
    print(data)
    sock.sendall(b"hello")

client.close()
server.close()