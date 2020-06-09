import socketserver
from client.socks5_server import subnegotiation, BUFSIZE, VER, ATYP_IPV4
from socketer import cdntunnel
import socket

remote_addr, remote_port = "localhost", 8887


class Socks5server(socketserver.BaseRequestHandler):
    def handle(self):
        print('connection', flush=True)
        cintro_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            cintro_server.connect((remote_addr, remote_port))
            cintro_server.send(b'\1\2\3\4')
        except socket.error:
            self.request.send(b"\1")
            print("error connect to remote server", flush=True)
            self.request.close()
            return
        self.request: socket.socket
        if subnegotiation(self.request):
            connection_request = self.request.recv(BUFSIZE)
            cintro_server.send(connection_request[3:])
            remote_result = cintro_server.recv(1)  # 关键的一位，判断连接是否成功。
            reply = VER + remote_result + b'\x00' + ATYP_IPV4 + bytes(6)
            self.request.send(reply)  # 已经发送了远端的结果，然后再判断是否断开连接
            if remote_result != b'\0':  # 连接失败
                self.request.close()
                return
            else:  # 连接成功
                print("remote connected!", flush=True)
                cdntunnel(cintro_server, self.request)
                return


if __name__ == "__main__":
    HOST, PORT = "localhost", 9999

    # Create the server, binding to localhost on port 9999
    with socketserver.ThreadingTCPServer((HOST, PORT), Socks5server) as server:
        # Activate the server; this will keep running until you
        # interrupt the program with Ctrl-C
        server.serve_forever()
