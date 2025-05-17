import socket
import threading

def recv_messages(conn):
    """Luồng chỉ lo nhận và in tin nhắn từ client"""
    try:
        while True:
            data = conn.recv(1024)
            if not data:
                print("[*] Client đã ngắt kết nối")
                break
            print(f"\r[Client] {data.decode()}\n> ", end="")
    except ConnectionResetError:
        print("\n[*] Client đã ngắt kết nối bất ngờ")
    finally:
        conn.close()

def send_messages(conn):
    """Luồng chỉ lo đọc từ stdin và gửi đi"""
    try:
        while True:
            msg = input("> ")
            if msg.lower() in ("exit", "quit"):
                print("[*] Đóng kết nối và thoát")
                conn.close()
                break
            conn.sendall(msg.encode())
    except BrokenPipeError:
        pass

def main(host="0.0.0.0", port=5000):
    # TCP
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind((host, port))
    sock.listen(1)
    print(f"[*] Server lắng nghe trên {host}:{port}")
    conn, addr = sock.accept()
    print(f"[*] Client kết nối từ {addr}")

    # khởi 2 luồng send/recv
    threading.Thread(target=recv_messages, args=(conn,), daemon=True).start()
    send_messages(conn)

if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--host", default="0.0.0.0", help="Địa chỉ bind (mặc định 0.0.0.0)")
    p.add_argument("--port", type=int, default=5000, help="Port lắng nghe")
    args = p.parse_args()
    main(args.host, args.port)
