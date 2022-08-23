import contextlib
import os
import socket
import select
import pickle
from datetime import datetime
from os.path import exists, join
from sys import argv

from kivy import Logger
from multiprocessing import Process

# --------Binary File Checker----------#

text_chars = bytearray({7, 8, 9, 10, 12, 13, 27} | set(range(0x20, 0x100)) - {0x7f})
is_binary = lambda byte: bool(byte.translate(None, text_chars))

# --------Binary File Checker----------#

try:
    folder_path = argv[1]
except IndexError:
    folder_path = None
try:
    ip = argv[2]
except IndexError:
    ip = None
try:
    _port = argv[3]
except IndexError:
    _port = None


class KivyLiveServer:
    def __init__(self, gui=None, ip_address=ip or "0.0.0.0", port=_port or 5567, write_location=folder_path or "live"):
        if not exists(write_location):
            os.mkdir(write_location)
        if not gui:
            print(f"writing to: {write_location}")
        self.gui = gui
        self.write_location = write_location
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            self.server_socket.bind((ip_address, port))
        except OverflowError as e:
            try:
                gui.stop_server(error=str(e).upper().replace("BIND()", "PORT NUMBER TOO LONG"))
            except AttributeError as exc:
                raise OverflowError(str(e)) from exc
        except OSError as e:
            try:
                gui.stop_server(error=f"PORT NUMBER {port} IS ALREADY IN USE")
            except AttributeError as exc:
                raise OSError(str(e)) from exc
        if not gui:
            print(
                f"{datetime.now().strftime('%d/%m/%Y %H:%M:%S')} : "
                f"server running on {self.server_socket.getsockname()}"
            )
        else:
            gui.log_black_box(
                f"{datetime.now().strftime('%d/%m/%Y %H:%M:%S')} : "
                f"server running on {self.server_socket.getsockname()}"
            )
        self.server_socket.listen()
        self.socket_list = [self.server_socket]
        self.client = {}
        self.client_process = []
        self.HEADER_LENGTH = 64
        if gui:
            self.run_server()

    def update_code_file(self, code_message, client_socket):
        # write code
        file = code_message["data"]["file"]
        try:
            os.makedirs(join(self.write_location, os.path.split(file)[0]))
        except (FileExistsError, FileNotFoundError) as e:
            Logger.debug(f"{str(e)} : Ignore this")
        if file != "main.py":
            with open(join(self.write_location, file), "wb") as f:
                f.write(code_message["data"]["code"])
        else:
            with open(join(self.write_location, "liveappmain.py"), "wb") as f:
                f.write(code_message["data"]["code"])

        Logger.info(f"File Update: {file} was updated by {code_message['address']}")

        # write log
        with open("user.log", "a+") as f:
            f.write(f"[{code_message['address']}: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}] Wrote "
                    f"{code_message['data']['file']}\n")
        self.broadcast_new_code(code_message, client_socket)

    def broadcast_new_code(self, code_message, client_socket):
        for clients in self.socket_list:
            if clients == client_socket:
                continue
            clients.send(
                f"{len(pickle.dumps(code_message)):<{self.HEADER_LENGTH}}".encode("utf-8")
            )
            self.client[clients].send(pickle.dumps(code_message))

    def recv_conn(self):
        read_socket, _, exception_sockets = select.select(self.socket_list, [], self.socket_list)
        if self.gui.kill_server_thread:
            self.clean_all()
            return
        for notified_socket in read_socket:
            if notified_socket == self.server_socket:
                client_socket, client_address = self.server_socket.accept()
                Logger.info(f"NEW CONNECTION: [IP]: {client_address[0]}, [PORT]{client_address[1]}")
                with contextlib.suppress(AttributeError):
                    self.gui.log_black_box(f"NEW CONNECTION: [IP]: {client_address[0]}, [PORT]{client_address[1]}")
                self.socket_list.append(client_socket)
                # client_socket.close()
                self.client.update({f"{client_address[0]}:{client_address[1]}": client_socket})
                new_process = Process(target=self.recv_msg, args=(client_socket, client_address))
                new_process.start()
                self.client_process.append(new_process)

    def recv_msg(self, client_socket, address):
        file_dir = {}
        for folder, sub_folder, files in os.walk(self.write_location):
            if (not files) or "__pycache__" in folder:
                continue
            if sub_folder in ("tools", "plyer"):
                continue
            for filename in files:
                if filename in ("main.py", "user.log", "server.py", "toast.py", "hover_behavior.py"):
                    continue
                with open(os.path.join(folder, filename), "rb") as f:
                    filename = "main.py" if filename == "liveappmain.py" else filename
                    file_dir[os.path.join(folder, filename)] = f.read()
        data = pickle.dumps(file_dir)
        client_socket.send(f"{len(data):<{self.HEADER_LENGTH}}".encode("utf-8") + data)
        while True:
            try:
                message_header = client_socket.recv(self.HEADER_LENGTH)
                if not len(message_header):
                    self.clean(client_socket, address)
                    break
                message_length = int(message_header.decode("utf-8"))
                code_message = {"address": f"{address[0]}:{address[1]}",
                                "data": pickle.loads(client_socket.recv(message_length))}
                self.update_code_file(code_message, client_socket)
            except Exception:
                self.clean(client_socket, address)
                break

    def clean(self, client_socket, address, process: Process = None):
        Logger.info(f"CONNECTION CLOSED: {address[0]}:{address[1]}")
        self.socket_list.remove(client_socket)
        try:
            self.client.pop(f"{address[0]}:{address[1]}")
        except KeyError:
            self.client.pop(address)
        client_socket.close()
        if process:
            process.terminate()
            process.kill()
            process.join()

    def clean_all(self):
        with contextlib.suppress(ValueError):
            clients = list(self.client.items())
            for client, process in zip(clients, self.client_process):
                self.clean(client[1], client[0], process)

    def run_server(self):
        while not self.gui.kill_server_thread:
            self.recv_conn()


if __name__ == "__main__":
    KivyLiveServer().run_server()
