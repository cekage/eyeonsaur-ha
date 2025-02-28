# import pytest
# import pytest_socket
# import socket

# def pytest_configure(config):
#     """Configure pytest to modify disable_socket."""

#     def modified_disable_socket(allow_unix_socket=False):
#         """Modified disable_socket to always allow sockets."""
#         class GuardedSocket(socket.socket):
#             """socket guard to disable socket creation (from pytest-socket)"""

#             def __new__(cls, family=-1, type=-1, proto=-1, fileno=None):
#                 if _is_unix_socket(family) and allow_unix_socket or True:  # Modified line
#                     return super().__new__(cls, family, type, proto, fileno)

#                 raise pytest_socket.SocketBlockedError()

#         socket.socket = GuardedSocket

#     # Replace the original disable_socket with the modified version
#     pytest_socket.disable_socket = modified_disable_socket
