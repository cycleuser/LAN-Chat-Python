import socket
import errno
import sys
import threading
import os

HEADER_LENGTH = 10

class Client:
    def __init__(self, ip=None, port=None, username=None):
        self.ip = ip
        self.port = port
        self.username = username
        self.connect_to_server()
        self.send_username()
        print(f"Connected to server on {self.ip}:{self.port} with username {self.username}")

    def connect_to_server(self):
        while True:
            try:
                if not self.ip:
                    self.ip = input("Please enter an IP: ")
                if not self.port:
                    self.port = int(input("Please enter a PORT: "))
                if not self.username:
                    self.username = input("Username: ")
                self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.client_socket.connect((self.ip, self.port))
                self.client_socket.setblocking(False)
                break
            except:
                print("Please try again. Server not found!")

    def send_username(self):
        username_encoded = self.username.encode('utf-8')
        username_header = f"{len(username_encoded):<{HEADER_LENGTH}}".encode('utf-8')
        self.client_socket.send(username_header + username_encoded)

    def send_message(self, message):
        message_encoded = message.encode('utf-8')
        message_header = f"{len(message_encoded):<{HEADER_LENGTH}}".encode('utf-8')
        self.client_socket.send(message_header + message_encoded)
        print(f"\033[F\033[K{self.username} > {message}")

    def receive_messages(self):
        while True:
            try:
                while True:
                    username_header = self.client_socket.recv(HEADER_LENGTH)
                    if not len(username_header):
                        print("Connection closed by the server")
                        sys.exit()
                    username_length = int(username_header.decode('utf-8').strip())
                    username = self.client_socket.recv(username_length).decode('utf-8')
                    message_header = self.client_socket.recv(HEADER_LENGTH)
                    message_length = int(message_header.decode('utf-8').strip())
                    message = self.client_socket.recv(message_length).decode('utf-8')
                    print(f"\r{username} > {message}")

            except IOError as e:
                if e.errno != errno.EAGAIN and e.errno != errno.EWOULDBLOCK:
                    print('Reading error: {}'.format(str(e)))
                    sys.exit()
                continue

            except Exception as e:
                print('Reading error: {}'.format(str(e)))
                sys.exit()

    def start_sending_messages(self):
        threading.Thread(target=self.send_messages_loop).start()

    def send_messages_loop(self):
        while True:
            message = input()
            if message:
                self.send_message(message)

    def run(self):
        # Do not delete. For some reason makes the ANSI Escape codes work
        os.system("")
        self.start_sending_messages()
        self.receive_messages()

if __name__ == "__main__":
    client = Client(ip="192.168.56.101", port=9999, username="testuser")
    client.run()