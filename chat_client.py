import socket, threading, sys

def receive(sock):
    while True:
        try:
            msg = sock.recv(1024).decode()
            if not msg: break
            print(f"\n{msg}\n> ", end="")
        except: break

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect((sys.argv[1] if len(sys.argv) > 1 else '10.0.0.1', 6666))
threading.Thread(target=receive, args=(sock,), daemon=True).start()

try:
    while True:
        msg = input("> ")
        if msg == "/quit": break
        sock.send(msg.encode())
finally:
    sock.close()
