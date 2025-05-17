import socket
import threading

def recv_messages(sock):
    try:
        while True:
            data = sock.recv(1024)
            if not data:
                print("[*] Server đã ngắt kết nối")
                break
            print(f"\r[Server] {data.decode()}\n> ", end="")
    except ConnectionResetError:
        print("\n[*] Server đã ngắt kết nối bất ngờ")
    finally:
        sock.close()

def send_messages(sock):
    try:
        while True:
            msg = input("> ")
            if msg.lower() in ("exit", "quit"):
                print("[*] Đóng kết nối và thoát")
                sock.close()
                break
            sock.sendall(msg.encode())
    except BrokenPipeError:
        pass

def main(server_ip, server_port):
    # TCP
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((server_ip, server_port))
    print(f"[*] Đã kết nối tới {server_ip}:{server_port}")

    threading.Thread(target=recv_messages, args=(sock,), daemon=True).start()
    send_messages(sock)

if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("server_ip", help="IP hoặc hostname của server")
    p.add_argument("server_port", type=int, help="Port của server")
    args = p.parse_args()
    main(args.server_ip, args.server_port)
