import socket
import errno
import sys
import threading
import os

HEADER_LENGTH = 10


class Client:
    def __init__(
        self,
        local_ip="127.0.0.1",
        server_ip="127.0.0.1",
        port=9999,
        username="Test",
        message_callback=None,
    ):
        self.local_ip = local_ip
        self.target_ip = server_ip
        self.port = port
        self.username = username
        self.callback = message_callback
        self.running = False
        self.connect_to_server()
        if self.running:
            self.send_username()
            print(
                f"Connected to server on {self.target_ip}:{self.port} with username {self.username}"
            )

    def connect_to_server(self):
        try:
            if not self.target_ip:
                self.target_ip = input("Please enter an IP: ")
            if not self.port:
                self.port = int(input("Please enter a PORT: "))
            if not self.username:
                self.username = input("Username: ")
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.connect((self.target_ip, self.port))
            self.client_socket.setblocking(False)
            self.running = True
        except Exception as e:
            print(f"Failed to connect to the server: {e}")
            self.running = False

    def send_username(self):
        username_encoded = (self.username + " " + self.local_ip).encode("utf-8")
        username_header = f"{len(username_encoded):<{HEADER_LENGTH}}".encode("utf-8")
        self.client_socket.send(username_header + username_encoded)

    def send_message(self, message):
        message_encoded = message.encode("utf-8")
        message_header = f"{len(message_encoded):<{HEADER_LENGTH}}".encode("utf-8")
        self.client_socket.send(message_header + message_encoded)
        print(f"\033[F\033[K{self.username} > {message}")

    def receive_messages(self):
        try:
            while self.running:
                try:
                    username_header = self.client_socket.recv(HEADER_LENGTH)
                    if not len(username_header):
                        print("Connection closed by the server")
                        self.running = False
                        break
                    username_length = int(username_header.decode("utf-8").strip())
                    username = self.client_socket.recv(username_length).decode("utf-8")
                    message_header = self.client_socket.recv(HEADER_LENGTH)
                    message_length = int(message_header.decode("utf-8").strip())
                    message = self.client_socket.recv(message_length).decode("utf-8")
                    
                    if self.callback:
                        # 使用回调函数处理消息，不打印
                        user = {"data": username.encode("utf-8")}
                        message_dict = {"data": message.encode("utf-8")}
                        self.callback(user, message_dict)
                    else:
                        # 如果没有回调函数，打印消息（用于命令行界面）
                        print(f"\r{username} > {message}")
                except IOError as e:
                    # 异常处理代码
                    pass
                except Exception as e:
                    # 其他异常处理
                    pass
        finally:
            self.stop()
    def start_sending_messages(self):
        threading.Thread(target=self.send_messages_loop, daemon=True).start()

    def send_messages_loop(self):
        while self.running:
            message = input()
            if message:
                self.send_message(message)

    def run(self):
        os.system("")
        if self.running:
            self.start_sending_messages()
            self.receive_messages()

    def stop(self):
        self.running = False
        try:
            self.client_socket.shutdown(socket.SHUT_RDWR)
        except:
            pass
        self.client_socket.close()



def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('114.114.114.114', 80))
        IP = s.getsockname()[0]
    except:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP

if __name__ == "__main__":



    client = Client(
                    local_ip = get_local_ip(),
                    server_ip="192.168.0.25", 
                    port=9999,
                    username="Test")
  

    client.run()