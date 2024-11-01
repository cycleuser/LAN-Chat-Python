import socket
import select
import psutil
import errno
import sys
import threading
import os

HEADER_LENGTH = 10

class Server:
    def __init__(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        interfaces = self.list_network_interfaces()
        while True:
            try:
                interface_index = int(input("Select the network interface to use: "))
                if interface_index >= 0 and interface_index < len(interfaces):
                    selected_interface = interfaces[interface_index]
                    break
                else:
                    raise
            except:
                print("Invalid selection. Please choose a valid network interface.")
        
        ip_address = self.get_interface_ip(selected_interface)
        port = int(input("Enter the port number to bind the server: "))
        print(f"Server will bind to {ip_address}:{port}")
        
        self.server_socket.bind((ip_address, port))
        self.server_socket.listen()
        self.sockets_list = [self.server_socket]
        self.clients = {}

    def list_network_interfaces(self):
        interfaces = psutil.net_if_addrs().keys()
        print("Available network interfaces:")
        for i, interface in enumerate(interfaces):
            print(f"{i}: {interface}")
        return list(interfaces)

    def get_interface_ip(self, interface_name):
        for interface, addrs in psutil.net_if_addrs().items():
            if interface == interface_name:
                for addr in addrs:
                    if addr.family == socket.AF_INET:
                        return addr.address
        return None

    def receive_message(self, client_socket):
        try:
            message_header = client_socket.recv(10)
            if not len(message_header):
                return False
            message_length = int(message_header.decode('utf-8').strip())
            return {'header': message_header, 'data': client_socket.recv(message_length)}
        except:
            return False

    def run(self, server_ready_event):
        try:
            server_ready_event.set()  # Signal that the server is ready
            while True:
                read_sockets, _, exception_sockets = select.select(self.sockets_list, [], self.sockets_list)
                for notified_socket in read_sockets:
                    if notified_socket == self.server_socket:
                        client_socket, client_address = self.server_socket.accept()
                        user = self.receive_message(client_socket)
                        if user is False:
                            continue
                        self.sockets_list.append(client_socket)
                        self.clients[client_socket] = user
                        print('Accepted new connection from {}:{}, username: {}'.format(*client_address, user['data'].decode('utf-8')))
                    else:
                        message = self.receive_message(notified_socket)
                        if message is False:
                            print('Closed connection from: {}'.format(self.clients[notified_socket]['data'].decode('utf-8')))
                            self.sockets_list.remove(notified_socket)
                            del self.clients[notified_socket]
                            continue
                        user = self.clients[notified_socket]
                        print(f'Received message from {user["data"].decode("utf-8")}: {message["data"].decode("utf-8")}')
                        for client_socket in self.clients:
                            if client_socket != notified_socket:
                                client_socket.send(user['header'] + user['data'] + message['header'] + message['data'])
                for notified_socket in exception_sockets:
                    self.sockets_list.remove(notified_socket)
                    del self.clients[notified_socket]
        except KeyboardInterrupt:
            print("Server shutting down...")
            self.server_socket.close()

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
        try:
            while True:
                while True:
                    username_header = self.client_socket.recv(HEADER_LENGTH)
                    if not len(username_header):
                        print("Connection closed by the server")
                        return
                    username_length = int(username_header.decode('utf-8').strip())
                    username = self.client_socket.recv(username_length).decode('utf-8')
                    message_header = self.client_socket.recv(HEADER_LENGTH)
                    message_length = int(message_header.decode('utf-8').strip())
                    message = self.client_socket.recv(message_length).decode('utf-8')
                    print(f"\r{username} > {message}")

        except IOError as e:
            if e.errno != errno.EAGAIN and e.errno != errno.EWOULDBLOCK:
                print('Reading error: {}'.format(str(e)))
                return

        except Exception as e:
            print('Reading error: {}'.format(str(e)))
            return

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

def run_server(server_ready_event):
    server = Server()
    server.run(server_ready_event)

def run_client(server_ready_event):
    server_ready_event.wait()  # Wait for the server to be ready
    client = Client(ip="192.168.56.101", port=9999, username="testuser")
    client.run()

if __name__ == "__main__":
    server_ready_event = threading.Event()

    try:
        server_thread = threading.Thread(target=run_server, args=(server_ready_event,))
        client_thread = threading.Thread(target=run_client, args=(server_ready_event,))

        server_thread.start()
        client_thread.start()

        server_thread.join()
        client_thread.join()
    except KeyboardInterrupt:
        print("Shutting down...")
        sys.exit()