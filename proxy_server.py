import socketserver
from auth_and_crypt import auth_socket, get_conn_dest, AddressTypeError
from socketer import cdntunnel
import socket
import struct


class MyTCPHandler(socketserver.BaseRequestHandler):
    def handle(self):
        auth_socket(self.request)
        try:
            addr, port = get_conn_dest(self.request)
        except struct.error:
            self.request.close()
            return
        except AddressTypeError:
            return
        remote = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            remote.connect((addr, port))
        except TimeoutError:
            self.request.send(b'\1')  # 连接失败
            self.request.close()
            return
        else:
            self.request.send(b'\0')  # 连接成功，建立cdn信道，开始连接！
        cdntunnel(self.request, remote)  # cdntunnel退出之后，handle()过程自然也就结束了。


if __name__ == "__main__":
    HOST, PORT = "localhost", 8887

    # Create the server, binding to localhost on port 9999
    with socketserver.TCPServer((HOST, PORT), MyTCPHandler) as server:
        # Activate the server; this will keep running until you
        # interrupt the program with Ctrl-C
        server.serve_forever()
