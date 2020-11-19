import pickle
import select
import socket
import sys
from datetime import datetime


class PayloadReceiver:
    def __init__(self, server):
        self.server = server

    def receive_payload(self):
        raw_message = self.server.recv(2048)
        payload = pickle.loads(raw_message)
        method = getattr(self, f"_render_{payload['type']}_message_payload")
        return method(payload)

    def _render_server_message_payload(self, payload):
        final = f"{payload['message']}"
        print(final)

    def _render_error_message_payload(self, payload):
        final = f"{payload['message']}"
        print(final)
        exit()

    def _render_text_message_payload(self, payload):
        message_time = payload["time"]
        peer_ip = payload["ip"]
        peer_port = payload["port"]
        peer_name = payload["name"]
        message = payload["message"]
        final = f"{message_time} {peer_ip}:{peer_port}/~{peer_name}: {message}"
        print(final)


class PayloadBuilder:
    def __init__(self, message):
        self._message_array = message.split()
        self._payload = dict()

    @property
    def payload(self):
        return self._payload

    def build_send_time(self):
        self._payload["send_time"] = datetime.now().strftime("%H:%M %d/%m/%Y")
        return self._payload["send_time"]

    def build_command(self):
        self._payload["command"] = self._message_array[0]
        return self._payload["command"]

    def build_flags(self):
        self._payload["flags"] = [w for w in self._message_array[1:] if w.startswith("-")]
        return self._payload["flags"]

    def build_args(self):
        flags = self.build_flags()
        self._payload["args"] = [w for w in self._message_array[1:] if w not in flags]
        return self._payload["args"]


class Client:
    def __init__(self, server_ip, server_port, name):
        self.server_ip = server_ip
        self.server_port = server_port
        self.name = name
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.receiver = PayloadReceiver(self.server)

    def start(self):
        self.server.connect((self.server_ip, self.server_port))
        self.server.send(self.name.encode())
        self.show_welcome_message()

        while True:
            sockets_list = [sys.stdin, self.server]
            read_sockets, write_sockets, error_sockets = select.select(sockets_list, [], [])

            for sock in read_sockets:
                if sock == self.server:
                    self.receiver.receive_payload()
                else:
                    message = input()
                    if not message:
                        continue
                    payload = self.build_payload(message)
                    self.server.send(pickle.dumps(payload))
                    self.process_payload(payload)
        self.server.close()

    def show_welcome_message(self):
        print("Welcome to the group chat!")
        print("You can use the following commands:")
        print("\tlist -> list all connected users on the chat")
        print("\tsend -all <message> -> send a message to all users")
        print("\tsend -user <username> <message> -> send a message to a specific user")
        print("\tbye -> disconnect from the chat")

    def build_payload(self, message):
        builder = PayloadBuilder(message)
        builder.build_send_time()
        builder.build_command()
        builder.build_flags()
        builder.build_args()
        return builder.payload

    def process_payload(self, payload):
        if payload["command"] == "bye":
            exit()


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Insert IP, PORT and NAME")
        exit()

    ip_address = str(sys.argv[1])
    port = int(sys.argv[2])
    name = str(sys.argv[3])

    client = Client(ip_address, port, name)
    client.start()
