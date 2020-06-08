from socket import socket
from struct import unpack, pack


# 数据格式：版本号1，数据类型1，数据长度1，数据体（最长256）
# 规定：datatype为0时，数据表示即将发送的完整数据，datatype为1,表示数据为地址。
class CintroMessage:
    def __init__(self, data_type, data):
        self.data_type = data_type
        self.data_length = len(data)
        self.data = data

    @staticmethod
    def receive_from_socket(rec_socket: socket):
        try:
            header = rec_socket.recv(3)
        except ConnectionError:
            return None
        if len(header) == 0:
            return None
        _, data_type, data_length = unpack('!BBB', header)
        data = b''
        while len(data) < data_length:
            data += rec_socket.recv(data_length - len(data))
        return CintroMessage(data_type, data)

    def send_to_socket(self, target_socket: socket):
        target_socket.send(self.to_binary())

    def to_binary(self):
        return pack('!BBB', 0, self.data_type, self.data_length) + self.data
