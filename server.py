import socket
import select
import psutil

HEADER_LENGTH = 10

def list_network_interfaces():
    interfaces = psutil.net_if_addrs().keys()
    print("Available network interfaces:")
    for i, interface in enumerate(interfaces):
        print(f"{i}: {interface}")
    return list(interfaces)

def get_interface_ip(interface_name):
    for interface, addrs in psutil.net_if_addrs().items():
        if interface == interface_name:
            for addr in addrs:
                if addr.family == socket.AF_INET:
                    return addr.address
    return None

interfaces = list_network_interfaces()
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

IP = get_interface_ip(selected_interface)
if not IP:
    print(f"Could not get IP address for interface {selected_interface}")
    exit(1)

while True:
    try:
        PORT = int(input("Please enter a PORT: "))
        if PORT <= 65535 and PORT >= 0:
            break
        else:
            raise
    except:
        print("Invalid PORT. Please choose a port between 0 and 65535")

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

server_socket.bind((IP, PORT))
server_socket.listen()

sockets_list = [server_socket]
clients = {}

print(f"Server is listening for connections on {IP}:{PORT}...")

def receive_message(client_socket):
    try:
        message_header = client_socket.recv(HEADER_LENGTH)
        if not len(message_header):
            return False
        message_length = int(message_header.decode('utf-8').strip())
        return {'header': message_header, 'data': client_socket.recv(message_length)}
    except:
        return False

while True:
    read_sockets, _, exception_sockets = select.select(sockets_list, [], sockets_list)
    for notified_socket in read_sockets:
        if notified_socket == server_socket:
            client_socket, client_address = server_socket.accept()
            user = receive_message(client_socket)
            if user is False:
                continue
            sockets_list.append(client_socket)
            clients[client_socket] = user
            print('Accepted new connection from {}:{}, username: {}'.format(*client_address, user['data'].decode('utf-8')))
        else:
            message = receive_message(notified_socket)
            if message is False:
                print('Closed connection from: {}'.format(clients[notified_socket]['data'].decode('utf-8')))
                sockets_list.remove(notified_socket)
                del clients[notified_socket]
                continue
            user = clients[notified_socket]
            print(f'Received message from {user["data"].decode("utf-8")}: {message["data"].decode("utf-8")}')
            for client_socket in clients:
                if client_socket != notified_socket:
                    client_socket.send(user['header'] + user['data'] + message['header'] + message['data'])
    for notified_socket in exception_sockets:
        sockets_list.remove(notified_socket)
        del clients[notified_socket]