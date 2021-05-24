import os
import socket
import select
from json import loads, dumps
import pickle
from datetime import datetime
import requests

try:
    from kivy import Logger
except (ImportError, ModuleNotFoundError):
    try:
        requests.get("https://google.com", timeout=3)
    except (requests.ConnectionError, requests.Timeout):
        print("Turn On Your Internet Connection to install kivy or install it with <pip> to bypass this message")
        exit()
    try:
        from pip import main

        print("[INFO] [Kivy Logger Not Found] Preparing to install kivy")
        main(["install", "kivy"])
    except (ImportError, ModuleNotFoundError):
        from os import system

        print("[INFO] [Kivy Logger Not Found] Preparing to install kivy")
        system("pip install kivy")
from threading import Thread

# --------Binary File Checker----------#
text_chars = bytearray({7, 8, 9, 10, 12, 13, 27} | set(range(0x20, 0x100)) - {0x7f})
is_binary = lambda byte: bool(byte.translate(None, text_chars))
# --------Binary File Checker----------#


class KivyLiveServer:
    def __init__(self, **kwargs):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind(("0.0.0.0", 6051))
        self.server_socket.listen()
        self.socket_list = [self.server_socket]
        self.client = {}
        self.HEADER_LENGTH = 64

    def update_code_file(self, code_message, client_socket):
        # write code
        file = code_message["data"]["file"]
        try:
            os.makedirs(os.path.split(file)[0])
        except (FileExistsError, FileNotFoundError) as e:
            Logger.debug(f"{e} : Ignore this")
        if file != "main.py":
            with open(file, "wb" if type(code_message["data"]["code"]) == bytes else "w") as f:
                f.write(code_message["data"]["code"])
        else:
            with open("liveappmain.py", "wb" if type(code_message["data"]["code"]) == bytes else "w") as f:
                f.write(code_message["data"]["code"])

        Logger.info(f"File Update: {file} was updated by {code_message['address']}")

        # write log
        with open("user.log", "a+") as f:
            f.write(f"{code_message['address']}: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
        self.broadcast_new_code(code_message, client_socket)

    def broadcast_new_code(self, code_message, client_socket):
        for clients in self.client:
            if self.client[clients] == client_socket:
                continue
            self.client[clients].send(
                f"{len(pickle.dumps(code_message)):<{self.HEADER_LENGTH}}".encode("utf-8")
            )
            self.client[clients].send(pickle.dumps(code_message))

    def recv_conn(self):
        read_socket, _, exception_sockets = select.select(self.socket_list, [], self.socket_list)
        for notified_socket in read_socket:
            if notified_socket == self.server_socket:
                client_socket, client_address = self.server_socket.accept()
                Logger.info(f"NEW CONNECTION: [IP]: {client_address[0]}, [PORT]{client_address[1]}")
                self.socket_list.append(client_socket)
                self.client.update({f"{client_address[0]}:{client_address[1]}": client_socket})
                Thread(target=self.recv_msg, args=(client_socket, client_address)).start()

    def recv_msg(self, client_socket, address):
        file_dir = {}
        for folder, _, file in os.walk("."):
            if (not file) or folder.startswith("./.") or folder == "__pycache__":
                continue
            for i in file:
                if i in ("main.py", "user.log"):
                    continue
                binary = is_binary(open(os.path.join(folder, i), "rb").read(1024))
                with open(os.path.join(folder, i), "rb" if binary else "r") as f:
                    if i == "liveappmain.py":
                        i = "main.py"
                    file_dir.update({os.path.join(folder, i): f.read()})
        data = pickle.dumps(file_dir)
        client_socket.send(f"{len(data):<{self.HEADER_LENGTH}}".encode())
        client_socket.send(data)
        while True:
            try:
                message_header = client_socket.recv(self.HEADER_LENGTH)
                if not len(message_header):
                    Logger.info(f"CONNECTION CLOSED: {address[0]}:{address[1]}")
                    self.socket_list.remove(client_socket)
                    self.client.pop(f"{address[0]}:{address[1]}")
                    client_socket.close()
                    break
                message_length = int(message_header.decode("utf-8"))
                code_message = {"address": f"{address[0]}:{address[1]}",
                                "data": pickle.loads(client_socket.recv(message_length))}
                self.update_code_file(code_message, client_socket)
            except:
                Logger.info(f"CONNECTION CLOSED: {address[0]}:{address[1]}")
                self.socket_list.remove(client_socket)
                self.client.pop(f"{address[0]}:{address[1]}")
                client_socket.close()
                break


if __name__ == "__main__":
    server = KivyLiveServer()
    while True:
        server.recv_conn()
