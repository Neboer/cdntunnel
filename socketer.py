# 当得知用户希望连接的目的地之后，server打开一个通往目的地的socket和客户端的socket。
from socket import socket
from data_warper import get_and_decode, encode_and_upload
from concurrent.futures import ThreadPoolExecutor, Future
from threading import Thread, Lock
from queue import Queue
from typing import Union
import select


class PacketSender(Thread):
    def __init__(self, packet_thread_queue, c_or_s_socket):  # type: (Queue, socket) -> None
        super().__init__()
        self.packet_thread_queue = packet_thread_queue
        self.socket = c_or_s_socket

    def run(self) -> None:
        while True:
            download_parse_future = self.packet_thread_queue.get()  # type: Union[Future, bytes]
            data_from_opposite = b""
            if type(download_parse_future) == Future:  # 如果队列里下来的是一个future对象，那么就需要等待他完成然后获得数据。
                data_from_opposite = download_parse_future.result()
            else:  # 从队列里下来的是一个bytes对象，这个时候就把它发出去就可以了
                data_from_opposite = download_parse_future
            self.socket.send(data_from_opposite)

# 客户端数据报文格式：1字节的类型和最长999字节的数据、


# 客户端的每个包的大小均严格小于1kb。
def cdntunnel(client_socket: socket, server_socket: socket):
    executor = ThreadPoolExecutor(max_workers=3)
    packet_to_remote_server = Queue(maxsize=10)
    packet_to_local_client = Queue(maxsize=10)
    PacketSender(packet_to_remote_server, server_socket).start()
    PacketSender(packet_to_local_client, client_socket).start()
    while True:  # 主循环
        # 这里写select语句，然后决定是收到数据还是发出数据
        readable_socket, _, _ = select.select([client_socket, server_socket], [], [])
        if client_socket in readable_socket:  # 在这里选择。
            client_data = client_socket.recv(1000)
            content = client_data[1:]  # type: bytes
            data_type = client_data[0] == b'\0'  # True时，client_data是url，False时，则是短的数据，短的数据以1开头
            if data_type:
                url = content.decode('ascii')
                packet_to_remote_server.put(executor.submit(get_and_decode, url))
            else:
                # 此时content本身就是要发给服务器的原始数据，这个时候要把要发送的东西直接塞到队列里，注意顺序！
                packet_to_remote_server.put(content)
        if server_socket in readable_socket:
            server_data = server_socket.recv(1024 * 1024)  # 从服务端收1M的数据。
            if len(server_data) < 1000:  # 对于小的数据，直接发送
                packet_to_local_client.put(b'\1' + server_data)
            else:  # 较大块的数据，发送到cdn 
                packet_to_local_client.put(executor.submit(encode_and_upload, server_data))

