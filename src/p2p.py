from threading import Thread, Lock
from time import sleep
import socket
import sys
import os
import json
from configs import conf

resources = {}  # hash to save clients and its resources
connected_clients = {}  # hash to save clients connected to server
mutex = Lock()  # semaphore to control critical section


# this is the default value for the switch statement
def service_undefined():
    print("Service undefined.")
    sys.exit(-1)


def execute_static_func(func, **kwargs):
    mutex.acquire()
    if kwargs:
        result = func(kwargs)
    else:
        result = func()
    mutex.release()
    if result:
        return result


def get_all_files():
    global resources
    result = {'files': []}
    for nested_list in list(resources.values()):
        for key_list in nested_list:
            result['files'].append(key_list)
    return result


def get_peer_from_file(params):
    for client, resources_list in resources.items():
        if params['file'] in resources_list:
            return client
    return None


def create_new_client(params):
    global resources
    global connected_clients
    resources[params['client']] = params['files']
    connected_clients[params['client']] = conf["HEARTBEAT_TIMEOUT"]


def decrease_all_clients():
    global resources
    global connected_clients
    for client in connected_clients:
        connected_clients[client] -= 1


def update_heartbeat(params):
    global connected_clients
    connected_clients[params['client']] = conf["HEARTBEAT_TIMEOUT"]


def remove_inactive_clients():
    remove_value = 0
    removed_clients = []
    global resources
    global connected_clients
    for client in connected_clients:
        client_value = connected_clients[client]
        if client_value <= remove_value:
            removed_clients.append(client)
    for client in removed_clients:
        print(f"Removing {client} due to inactivity")
        del resources[client]
        del connected_clients[client]


def create_send_peer():
    P2P(conf["SEND"]).start()


class P2P(Thread):
    def __init__(self, port, host="0.0.0.0", client=False):
        Thread.__init__(self)
        self.client = client
        self.host = host
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.server_address = (self.host, self.port)

    def run(self):
        self.select_server_or_client()

    def select_server_or_client(self):
        service = self.get_service()
        if self.client:
            service()
        else:
            try:
                self.sock.bind(self.server_address)
                while True:
                    service()
            except OSError:
                print(f"Another process is already using port {self.server_address[1]}.")
                sys.exit(-5)

    # since python doesn't have a switch case statement, this is a way to implement it
    def get_service(self):
        if self.client:
            return {
                conf["SIGN_UP"]: self.client_sign_up,
                conf["QUERY"]: self.client_query,
                conf["HEARTBEAT"]: self.client_heartbeat,
                conf["RETRIEVE"]: self.client_retrieve
            }.get(self.port, service_undefined)
        else:
            return {
                conf["SIGN_UP"]: self.server_sign_up,
                conf["QUERY"]: self.server_query,
                conf["HEARTBEAT"]: self.server_heartbeat,
                conf["RETRIEVE"]: self.server_retrieve,
                conf["SEND"]: self.peer_send_file
            }.get(self.port, service_undefined)

    # generic method which contains all necessary exceptions to execute client functions
    def execute_client_func(self, func, arg=None):
        try:
            self.sock.settimeout(conf["CLIENT_TIMEOUT"])
            func(arg) if arg else func()
        except FileNotFoundError as e:
            print(f"[!] This folder doesn't exist: {e}")
            self.client_sign_up()
        except TypeError as e:
            print(f"[!] Need to specify file: {e}")
            self.client_retrieve()
        except Exception as e:
            print(f"[!] {e}")
            sys.exit(-4)
        finally:
            self.sock.close()

    def sign_up(self, folder):
        files = os.listdir(folder)
        data = {'files': files}
        self.sock.sendto(json.dumps(data).encode(), self.server_address)
        print('Waiting server response.')
        data, server = self.sock.recvfrom(conf["BUFFERSIZE"])
        data = data.decode()
        print(f"Received: {data}")
        create_send_peer()

    def query(self):
        self.sock.sendto(b"query", self.server_address)
        print("Waiting files from server.")
        data = self.sock.recv(conf["BUFFERSIZE"])
        data = json.loads(data.decode())
        files = data['files']
        print(
            "These are the available files: "
            f"{', '.join([str(x) for x in files])}")

    def heartbeat(self):
        while True:
            self.sock.sendto(b"heartbeat", self.server_address)
            sleep(conf["HEARTBEAT_TIME"])

    def retrieve(self, file):
        data = {'file': file}
        self.sock.sendto(
            json.dumps(data).encode(), self.server_address)

        print("[-] Waiting for peer IP.")
        peer_ip, server = self.sock.recvfrom(conf["BUFFERSIZE"])
        peer_ip = json.loads(peer_ip.decode())
        peer_ip = peer_ip['client']

        print(f"[-] Connecting to peer {peer_ip}")
        self.peer_retrieve_file(peer_ip, data)

    def client_sign_up(self):
        folder = input("Type Folder to share files: ")
        self.execute_client_func(self.sign_up, folder)

    def client_query(self):
        self.execute_client_func(self.query)

    def client_heartbeat(self):
        self.execute_client_func(self.heartbeat)

    def client_retrieve(self):
        file = input("File to retrieve: ")
        self.execute_client_func(self.retrieve, file)

    def server_sign_up(self):
        data, address = self.sock.recvfrom(conf["BUFFERSIZE"])
        client_ip = address[0]
        data = json.loads(data.decode())
        if data:
            files = data['files']
            print(f"Client {client_ip} connected and sent "
                f"{len(files)} files.")
            execute_static_func(
                create_new_client, client=client_ip, files=files)
            self.sock.sendto(b"Connected", address)

    def server_query(self):
        data, address = self.sock.recvfrom(conf["BUFFERSIZE"])
        client_ip = address[0]
        print(f"Sending {client_ip} a list of files.")
        files = execute_static_func(get_all_files)
        self.sock.sendto(json.dumps(files).encode(), address)

    def server_heartbeat(self):
        try:
            # timeout is the same as heartbeat time, it will timeout always
            tolerant_heartbeat = conf["HEARTBEAT_TIME"] + conf["HEARTBEAT_TOLERANCE"]  # noqa
            self.sock.settimeout(tolerant_heartbeat)
            data, address = self.sock.recvfrom(conf["BUFFERSIZE"])
            client_ip = address[0]
            execute_static_func(update_heartbeat, client=client_ip)
        except socket.timeout:
            execute_static_func(decrease_all_clients)
            execute_static_func(remove_inactive_clients)
            self.server_heartbeat()

    def server_retrieve(self):
        data, address = self.sock.recvfrom(conf["BUFFERSIZE"])
        client_ip = address[0]
        file = json.loads(data.decode())
        if file:
            file = file['file']
            print(f"Client {client_ip} wants file {file}")
            peer_ip = execute_static_func(get_peer_from_file, file=file)
            if peer_ip:
                data = {'client': peer_ip}
                self.sock.sendto(json.dumps(data).encode(), address)
            else:
                self.sock.sendto(b"not found", address)

    def peer_send_file(self):
        try:
            self.sock.settimeout(conf["HEARTBEAT_TIME"])
            file, address = self.sock.recvfrom(conf["BUFFERSIZE"])
            file = json.loads(file.decode())
            file = file['file']
            client_ip = address[0]
            opened_file = open(f"files/{file}", "rb")
            data = opened_file.read(conf["BUFFERSIZE"])
            print(f"Sending {file} to {client_ip}")
            while data:
                if self.sock.sendto(data, address):
                    data = opened_file.read(conf["BUFFERSIZE"])
            print("[*] File sent")
            opened_file.close()
        except socket.timeout:
            self.peer_send_file()

    def peer_retrieve_file(self, peer_ip, file):
        peer_address = (peer_ip, conf["SEND"])
        self.sock.sendto(json.dumps(file).encode(), peer_address)
        file = file['file']
        data, address = self.sock.recvfrom(conf["BUFFERSIZE"])
        print(f"Retrieving file {file}")
        created_file = open(f'{file}', 'wb')
        try:
            while data:
                created_file.write(data)
                self.sock.settimeout(2)
                data, address = self.sock.recvfrom(conf["BUFFERSIZE"])
        except socket.timeout:
            created_file.close()
            print("File Downloaded")
