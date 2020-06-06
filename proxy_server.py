import socketserver
from auth_and_crypt import auth_socket, get_conn_dest, AddressTypeError
from socketer import cdntunnel
import socket


class MyTCPHandler(socketserver.BaseRequestHandler):
    #           o  REP    Reply field:
    #              o  X'00' succeeded
    #              o  X'01' general SOCKS server failure
    #              o  X'02' connection not allowed by ruleset
    #              o  X'03' Network unreachable
    #              o  X'04' Host unreachable
    #              o  X'05' Connection refused
    #              o  X'06' TTL expired
    #              o  X'07' Command not supported
    #              o  X'08' Address type not supported
    #              o  X'09' to X'FF' unassigned
    def handle(self):
        auth_socket(self.request)
        try:
            addr, port = get_conn_dest(self.request)
        except AddressTypeError:
            return
        remote = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            remote.connect((addr, port))
        except:
            remote.send(b'\1')  # 连接失败
            self.request.close()
            return
        else:
            remote.send(b'\0')  # 连接成功，建立cdn信道，开始连接！
        cdntunnel(self.request, remote)


if __name__ == "__main__":
    HOST, PORT = "localhost", 9999

    # Create the server, binding to localhost on port 9999
    with socketserver.TCPServer((HOST, PORT), MyTCPHandler) as server:
        # Activate the server; this will keep running until you
        # interrupt the program with Ctrl-C
        server.serve_forever()
