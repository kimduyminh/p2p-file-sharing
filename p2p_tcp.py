#!/usr/bin/env python3
import socket, threading, argparse, sys

BUFFER = 1024

def recv_loop(conn, stop_ev):
    while not stop_ev.is_set():
        try:
            data = conn.recv(BUFFER)
            if not data:
                print("\n[*] Peer đã ngắt kết nối")
                stop_ev.set()
                break
            print(f"\r[Peer] {data.decode()}\n> ", end="")
        except Exception:
            continue

def send_loop(conn, stop_ev):
    while not stop_ev.is_set():
        try:
            msg = input("> ")
        except EOFError:
            # Nếu bạn nhấn Ctrl+D, chỉ đánh dấu dừng, không sys.exit
            stop_ev.set()
            break

        if msg.lower() in ("exit", "quit"):
            stop_ev.set()
            break

        try:
            conn.sendall(msg.encode())
        except Exception:
            stop_ev.set()
            break

def simultaneous_open(local_port, peer_ip, peer_port, timeout=5):
    listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    listener.bind(("0.0.0.0", local_port))
    listener.listen(1)

    conn = None
    addr = None

    def do_accept():
        nonlocal conn, addr
        try:
            c, a = listener.accept()
            if conn is None:
                conn, addr = c, a
        except:
            pass

    threading.Thread(target=do_accept, daemon=True).start()

    # Chuẩn bị xong listener, thử connect
    outgoing = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    outgoing.settimeout(timeout)
    try:
        outgoing.connect((peer_ip, peer_port))
        if conn is None:
            conn, addr = outgoing, (peer_ip, peer_port)
        else:
            outgoing.close()
    except Exception:
        outgoing.close()

    # Chờ accept nếu cần
    import time
    start = time.time()
    while conn is None and time.time() - start < timeout:
        time.sleep(0.1)

    listener.close()
    return conn, addr

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--local-port",  type=int, required=True)
    p.add_argument("--peer-ip",      required=True)
    p.add_argument("--peer-port",    type=int, required=True)
    args = p.parse_args()

    conn, addr = simultaneous_open(args.local_port,
                                   args.peer_ip, args.peer_port)
    if not conn:
        print("[!] Không kết nối được.")
        sys.exit(1)

    print(f"[*] Kết nối thành công với {addr}")

    stop_ev = threading.Event()
    threading.Thread(target=recv_loop, args=(conn, stop_ev), daemon=True).start()
    send_loop(conn, stop_ev)

    # khi send_loop kết thúc (gõ exit hoặc EOF), ta đóng socket
    conn.close()
    print("Đã đóng kết nối, thoát chương trình.")

if __name__ == "__main__":
    main()
