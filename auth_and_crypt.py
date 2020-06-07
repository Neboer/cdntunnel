from socket import socket, inet_ntoa
import struct


class AddressTypeError(BaseException):
    pass


def auth_socket(income_socket: socket):
    auth_data = income_socket.recv(4)
    if auth_data != b'\1\2\3\4':
        income_socket.close()


def get_conn_dest(income_socket: socket):
    # address-type	dst.addr dst.port三个部分
    address_type = struct.unpack("!B", income_socket.recv(1))[0]
    if address_type == 1:  # ipv4
        address = inet_ntoa(income_socket.recv(4))
    elif address_type == 4:  # ipv6
        address = inet_ntoa(income_socket.recv(16))
    elif address_type == 3:  # domain
        domain_length = ord(income_socket.recv(1))
        address = income_socket.recv(domain_length).decode('ascii')
    else:
        income_socket.close()
        raise AddressTypeError
    port = struct.unpack('!H', income_socket.recv(2))[0]
    return address, port
