#!/usr/bin/env python3
import socket
import threading
import sys
import os
import json
from tkinter import Tk
from tkinter.filedialog import askopenfilename

# --- Thêm pyngrok để mở TCP tunnel ---
from pyngrok import ngrok, conf

# Nếu bạn có ngrok auth token, có thể gán trực tiếp (không bắt buộc nếu đã set env NGROK_AUTHTOKEN)
# conf.get_default().auth_token = "YOUR_NGROK_AUTHTOKEN"
# ----------------------------------------

BUFFER = 1024
connection = None
conn_lock = threading.Lock()


def choose_file():
    root = Tk()
    root.withdraw()
    path = askopenfilename(title="Chọn file để gửi")
    root.destroy()
    return path


def send_file(conn, path):
    filesize = os.path.getsize(path)
    header = json.dumps({"filename": os.path.basename(path),
                         "filesize": filesize}).encode() + b"\n"
    conn.sendall(header)
    with open(path, "rb") as f:
        while True:
            chunk = f.read(BUFFER)
            if not chunk:
                break
            conn.sendall(chunk)
    print(f"[*] Đã gửi xong file: {os.path.basename(path)}")


def recv_loop(conn):
    header_buffer = b""
    file = None
    remaining = 0

    while True:
        try:
            data = conn.recv(BUFFER)
            if not data:
                print("\n[*] Peer đã ngắt kết nối")
                break

            if file:
                file.write(data)
                remaining -= len(data)
                if remaining <= 0:
                    file.close()
                    print(f"\n[*] Đã nhận xong file: {file.name}\n> ", end="")
                    file = None

            else:
                # Nếu là header JSON
                if header_buffer or data.startswith(b"{"):
                    header_buffer += data
                    if b"\n" in header_buffer:
                        header_line, rest = header_buffer.split(b"\n", 1)
                        info = json.loads(header_line.decode())
                        filename = info["filename"]
                        remaining = info["filesize"]
                        file = open(filename, "wb")
                        if rest:
                            file.write(rest)
                            remaining -= len(rest)
                        header_buffer = b""
                else:
                    # Bình thường: chat text
                    print(f"\r[Peer] {data.decode()}\n> ", end="")

        except Exception:
            continue

    # Khi recv_loop kết thúc, dọn dẹp kết nối
    with conn_lock:
        if connection is conn:
            conn.close()
            globals()['connection'] = None


def listener_thread(listen_port):
    global connection
    listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    listener.bind(("0.0.0.0", listen_port))
    listener.listen(1)
    print(f"[*] Đang chờ kết nối đến trên port {listen_port}...")

    while True:
        c, addr = listener.accept()
        with conn_lock:
            if connection is None:
                connection = c
                print(f"\n[*] Nhận kết nối từ {addr}\n> ", end="")
                threading.Thread(target=recv_loop, args=(c,), daemon=True).start()
            else:
                c.close()


def connect_peer(ip, port):
    global connection
    with conn_lock:
        if connection is not None:
            print("[!] Đã có kết nối, hãy ngắt trước khi kết nối mới.")
            return
    try:
        c = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        c.connect((ip, port))
        with conn_lock:
            connection = c
        print(f"[*] Đã kết nối tới {ip}:{port}\n> ", end="")
        threading.Thread(target=recv_loop, args=(c,), daemon=True).start()
    except Exception as e:
        print(f"[!] Kết nối thất bại: {e}")


def main():
    # Nhập port lắng nghe
    try:
        listen_port = int(input("Nhập port để lắng nghe: ").strip())
    except ValueError:
        print("[!] Port không hợp lệ.")
        return

    # --- Mở ngrok TCP tunnel ---
    tcp_tunnel = ngrok.connect(listen_port, "tcp")
    public_addr = tcp_tunnel.public_url  # ví dụ "tcp://3.tcp.ngrok.io:12345"
    print(f"[*] Ngrok tunnel đã sẵn sàng: {public_addr}")
    # --------------------------------

    # Start listener
    threading.Thread(target=listener_thread, args=(listen_port,), daemon=True).start()

    while True:
        cmd = input("> ").strip()
        if not cmd:
            continue
        if cmd.lower() in ("exit", "quit"):
            break

        if cmd == "/connect":
            ip = input("Nhập IP peer: ").strip()
            try:
                port = int(input("Nhập port peer: ").strip())
            except ValueError:
                print("[!] Port không hợp lệ.")
                continue
            connect_peer(ip, port)
            continue

        if cmd == "/sendfile":
            with conn_lock:
                if connection is None:
                    print("[!] Chưa có kết nối nào.")
                    continue
            mode = input("Chọn chế độ: (1) GUI, (2) Nhập đường dẫn: ").strip()
            if mode == "1":
                path = choose_file()
            else:
                path = input("Nhập đường dẫn file để gửi: ").strip()

            if not path:
                print("[!] Không có file nào được chọn.")
                continue
            if not os.path.isfile(path):
                print(f"[!] File không tồn tại: {path}")
                continue

            send_file(connection, path)
            continue

        # Chat bình thường
        with conn_lock:
            if connection is None:
                print("[!] Chưa có kết nối nào.")
            else:
                try:
                    connection.sendall(cmd.encode())
                except Exception:
                    print("[!] Lỗi gửi tin nhắn.")

    # Khi thoát, đóng kết nối nếu có
    with conn_lock:
        if connection:
            connection.close()

    # --- Dọn ngrok trước khi exit ---
    ngrok.disconnect(tcp_tunnel.public_url)
    ngrok.kill()
    # --------------------------------

    print("Đã thoát.")

if __name__ == "__main__":
    main()
