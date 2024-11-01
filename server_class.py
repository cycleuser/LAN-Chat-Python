import socket
import select
import psutil

class Server_old:
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

    def run(self):
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
                    print(f'{user["data"].decode("utf-8")}: {message["data"].decode("utf-8")}')
                    for client_socket in self.clients:
                        if client_socket != notified_socket:
                            client_socket.send(user['header'] + user['data'] + message['header'] + message['data'])
            for notified_socket in exception_sockets:
                self.sockets_list.remove(notified_socket)
                del self.clients[notified_socket]


class Server:
    def __init__(self, server_ip="127.0.0.1", port=9999, message_callback=None):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.running = False
        self.callback = message_callback

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

        # self.server_socket.bind((server_ip, port))
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
            message_length = int(message_header.decode("utf-8").strip())
            return {
                "header": message_header,
                "data": client_socket.recv(message_length),
            }
        except:
            return False

    def run(self, server_ready_event):
        self.running = True
        try:
            server_ready_event.set()  # 通知服务器已准备就绪
            while self.running:
                try:
                    read_sockets, _, exception_sockets = select.select(
                        self.sockets_list, [], self.sockets_list, 1
                    )
                except ValueError:
                    # 套接字列表为空或包含无效套接字，退出循环
                    break
    
                for notified_socket in read_sockets:
                    if notified_socket == self.server_socket:
                        try:
                            client_socket, client_address = self.server_socket.accept()
                        except OSError:
                            # 套接字已关闭，退出循环
                            break
                        user = self.receive_message(client_socket)
                        if user is False:
                            continue
                        self.sockets_list.append(client_socket)
                        self.clients[client_socket] = user
                        print(
                            "Accepted new connection from {}:{}, username: {}".format(
                                *client_address, user["data"].decode("utf-8")
                            )
                        )
                    else:
                        message = self.receive_message(notified_socket)
                        if message is False:
                            print(
                                "Closed connection from: {}".format(
                                    self.clients[notified_socket]["data"].decode("utf-8")
                                )
                            )
                            self.sockets_list.remove(notified_socket)
                            del self.clients[notified_socket]
                            continue
                        user = self.clients[notified_socket]
                        print(
                            f'{user["data"].decode("utf-8")}:\n {message["data"].decode("utf-8")}'
                        )
                        if self.callback:
                            self.callback(user, message)
                        for client_socket in self.clients:
                            if client_socket != notified_socket:
                                client_socket.send(
                                    user["header"]
                                    + user["data"]
                                    + message["header"]
                                    + message["data"]
                                )
                for notified_socket in exception_sockets:
                    self.sockets_list.remove(notified_socket)
                    del self.clients[notified_socket]
        except KeyboardInterrupt:
            print("Server shutting down...")
        finally:
            self.stop_server()
    
    def stop_server(self):
        if self.running:
            self.running = False
            try:
                self.server_socket.shutdown(socket.SHUT_RDWR)
            except:
                pass
            self.server_socket.close()
            for client_socket in self.clients.keys():
                client_socket.close()
            self.sockets_list.clear()
            self.clients.clear()


import threading

if __name__ == "__main__":
    server = Server()
    server_ready_event = threading.Event()
    server.run(server_ready_event)