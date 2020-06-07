# 当得知用户希望连接的目的地之后，server打开一个通往目的地的socket和客户端的socket。
from socket import socket
from data_warper import get_and_decode, encode_and_upload
from concurrent.futures import ThreadPoolExecutor, Future
from threading import Thread, Lock
from queue import Queue
from typing import Union
from cintro.message import CintroMessage
from select import select
from time import sleep


class PacketSender(Thread):
    is_closed = False

    def __init__(self, packet_thread_queue, c_or_s_socket):  # type: (Queue, socket) -> None
        super().__init__()
        self.packet_thread_queue = packet_thread_queue
        self.socket = c_or_s_socket

    def run(self) -> None:
        while not self.is_closed:  # 我被主线程关闭了！
            download_parse_future = self.packet_thread_queue.get()  # type: Union[Future, bytes]
            data_from_opposite = b""
            if type(download_parse_future) == Future:  # 如果队列里下来的是一个future对象，那么就需要等待他完成然后获得数据。
                data_from_opposite = download_parse_future.result()
            else:  # 从队列里下来的是一个bytes对象，这个时候就把它发出去就可以了
                data_from_opposite = download_parse_future
            try:
                self.socket.send(data_from_opposite)
            except ConnectionAbortedError:  # 远端已经关闭了这个连接，那么，cdntunnel也应该结束自己的工作了，此时应该通知tunnel线程退出。
                return
        self.socket.close()  # 明确关闭自身的socket
        return  # 从容的退出战场。

    def close(self):
        # 主线程调用close()方法，子线程从run()的状态中退出。
        self.is_closed = True


def enc_upd_warper(data):
    url = encode_and_upload(data)
    return CintroMessage(1, url.encode('ascii')).to_binary()


# 客户端的每个包的大小均严格小于1kb。
def cdntunnel(cintro_socket: socket,
              freedom_socket: socket):  # freedom_socket就指的是来自远端等的正常数据，cintro_socket指的是需要以cintro协议通信的一方。
    executor = ThreadPoolExecutor(max_workers=3)
    packet_to_remote_server = Queue(maxsize=10)
    packet_to_local_client = Queue(maxsize=10)
    freedom_sender = PacketSender(packet_to_remote_server, freedom_socket)
    cintro_sender = PacketSender(packet_to_local_client, cintro_socket)
    freedom_sender.start()
    cintro_sender.start()
    while True:  # 主循环
        # 这里写select语句，然后决定是收到数据还是发出数据
        if not freedom_sender.is_alive() or not cintro_sender.is_alive():
            if freedom_sender.is_alive():
                freedom_sender.close()
                return
            else:
                cintro_socket.close()
                return
        readable_socket, _, _ = select([cintro_socket, freedom_socket], [], [])
        if cintro_socket in readable_socket:  # 客户端发来数据，看来好时代要到来力！
            client_data = CintroMessage.receive_from_socket(cintro_socket)
            if client_data.data_type == 1:  # 收到的是下载的地址。
                url = client_data.data.decode('ascii')
                packet_to_remote_server.put(executor.submit(get_and_decode, url))  # 将这个解码任务交到队列中
            else:
                # 此时content本身就是要发给服务器的原始数据，这个时候要把要发送的东西直接塞到队列里，注意顺序！
                packet_to_remote_server.put(client_data.data)
        if freedom_socket in readable_socket:
            sleep(0.02)  # 这个是一个高度可定制的功能。服务器在等待足够长的时间之后，再从远端拿取数据，目的是强行扩充缓冲的buffer大小。
            # 为了保证数据传输的顺序不混乱，这里并不引入异步功能。其实在这一点时间里，是可以继续收取客户端传来的数据的。关于多线程优化的问题，
            # 会在未来的版本里继续进行优化，适配更多线程。这个延迟也可以由客户端来决定。比如说如果客户端正在下载，那么他就会希望这个延时大一些，
            # 如果客户端正在浏览网页，他就希望这个延迟小一些。因为ssl握手的过程中也会传输中体积大小的数据，因此这里有待于进一步讨论。
            # 值得一提的是，这两个client和remote的数据传输过程似乎可以直接多线程队列化，也就是说，来临连接的时候可以直接提交线程进行处理，
            # 同时释放GIL锁，让全局有更多的时间去select()。
            server_data = freedom_socket.recv(1000000)  # 从服务端收最大1M的数据，这个地方存疑：
            # ！！ 如何保证从服务端接收到足够多且有必要的量的数据？这个数据量如果太小，会极大的浪费带宽，这个可谓是“性能瓶颈”。而且针对底层这里应该
            # 做出更多优化！
            if len(server_data) < 256:  # 对于小的数据，直接发送
                packet_to_local_client.put(CintroMessage(0, server_data).to_binary())
            else:  # 较大块的数据，发送到cdn
                packet_to_local_client.put(executor.submit(enc_upd_warper, server_data))
