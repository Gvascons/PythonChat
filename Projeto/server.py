import pickle
import socket
import sys
from datetime import datetime
from threading import Thread


class Peer:
    def __init__(self, connection, address, name):
        self.connection = connection
        self.address = address
        self.name = name


class PayloadMounter:
    @classmethod
    def _get_message_time(cls):
        return datetime.now().strftime("%H:%M %d/%m/%Y")

    @classmethod
    def mount_server_message_payload(cls, message):
        return {
            "type": "server",
            "time": cls._get_message_time(),
            "message": message,
        }

    @classmethod
    def mount_text_message_payload(cls, message, peer):
        return {
            "type": "text",
            "time": cls._get_message_time(),
            "ip": peer.address[0],
            "port": peer.address[1],
            "name": peer.name,
            "message": message
        }

    @classmethod
    def mount_error_message_payload(cls, message):
        return {
            "type": "error",
            "time": cls._get_message_time(),
            "message": message,
        }


class PayloadRunner:
    def __init__(self, server, peer, payload):
        self.server = server
        self.peer = peer
        self.payload = payload
        command_function = getattr(self, f"_run_{payload['command']}")
        command_function()

    def _run_bye(self):
        self.server.remove_connection(self.peer)

    def _run_list(self):
        message = self.server.get_connected_peers_message()
        send_payload = PayloadMounter.mount_server_message_payload(message)
        self.server.send_payload(self.peer.connection, send_payload)

    def _run_send(self):
        if self.payload["flags"] == ["-all"]:
            self._run_send_all()
        elif self.payload["flags"] == ["-user"]:
            self._run_send_user()

    def _run_send_all(self):
        text = " ".join(self.payload["args"])
        send_payload = PayloadMounter.mount_text_message_payload(text, self.peer)
        self.server.log(send_payload)
        self.server.broadcast(send_payload)

    def _run_send_user(self):
        receiver_name = self.payload["args"][0]
        text = " ".join(self.payload["args"][1:])
        receiver = self.server._peers[receiver_name]
        if not receiver:
            send_payload = PayloadMounter.mount_server_message_payload("Peer isn't connected.")
        else:
            send_payload = PayloadMounter.mount_text_message_payload(text, self.peer)
        self.server.log(send_payload)
        self.server.send_payload(receiver.connection, send_payload)


class Server:
    def __init__(self, ip_address, port, max_clients=256):
        self.ip_address = ip_address
        self.port = port
        self._max_clients = max_clients
        self._peers = dict()
        self._setup_server_socket()

    def _setup_server_socket(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.ip_address, self.port))
        self.server_socket.listen(self._max_clients)

    def start(self):
        self.log(f"Starting server {self.ip_address}:{self.port}")
        while True:
            connection, address = self.server_socket.accept()
            name_received = connection.recv(256).decode()
            if self.check_name(name_received, connection):
                continue
            peer = Peer(connection, address, name_received)
            self.broadcast_user_connection(peer)
            self._peers[name_received] = peer
            Thread(target=self.handle_client, args=(peer,)).start()
        self.stop(connection, address)

    def check_name(self, name_received, connection):
        if name_received in self._peers.keys():
            message = "Name already in use, choose another one."
            send_payload = PayloadMounter.mount_error_message_payload(message)
            self.send_payload(connection, send_payload)
            return True

    def stop(self, connection, address):
        connection.close()
        address.close()

    def handle_client(self, peer):
        welcome_message = self.get_connected_peers_message()
        send_payload = PayloadMounter.mount_server_message_payload(welcome_message)
        self.send_payload(peer.connection, send_payload)

        while True:
            try:
                payload = pickle.loads(peer.connection.recv(2048))
                if payload and self.check_payload(payload):
                    PayloadRunner(self, peer, payload)
                elif payload:
                    message = "Invalid command"
                    send_payload = PayloadMounter.mount_server_message_payload(message)
                    self.send_payload(peer.connection, send_payload)
                else:
                    self.remove_connection(peer)
            except:
                continue

    def check_payload(self, payload):
        flag_map = {"bye": [], "list": [], "send": ["-all", "-user"]}
        if payload["command"] not in flag_map.keys():
            return False
        if not payload["flags"]:
            return True
        return bool(set(payload["flags"]) & set(flag_map[payload["command"]]))

    def broadcast(self, payload):
        for name, peer in self._peers.items():
            try:
                self.send_payload(peer.connection, payload)
            except:
                peer.connection.close()
                self.remove_connection(peer)

    def remove_connection(self, peer):
        if peer in self._peers.values():
            del self._peers[peer.name]
            self.broadcast_user_disconnection(peer)

    def broadcast_user_disconnection(self, peer):
        message = f"{peer.name} has disconnected"
        payload = PayloadMounter.mount_server_message_payload(message)
        self.log(message)
        self.broadcast(payload)

    def broadcast_user_connection(self, peer):
        message = f"{peer.name} has connected"
        payload = PayloadMounter.mount_server_message_payload(message)
        self.log(message)
        self.broadcast(payload)

    def send_payload(self, connection, payload):
        connection.send(pickle.dumps(payload))

    def get_connected_peers_message(self):
        return f"Connected peers: {', '.join(name for name in self._peers.keys())}"

    def log(self, message):
        now = datetime.now().strftime("%H:%M %d/%m/%Y")
        print(f"{now}: {str(message)}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Insert IP and PORT")
        exit()

    ip_address = str(sys.argv[1])
    port = int(sys.argv[2])

    server = Server(ip_address, port)
    server.start()
