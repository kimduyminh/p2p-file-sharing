#!/usr/bin/env python3
import platform
import socket
import threading
import os
import json
import urllib
import zipfile
from tkinter import Tk, Button, simpledialog, filedialog
from pyngrok import ngrok, conf

# Uncomment and set your ngrok auth token if needed
# conf.get_default().auth_token = "YOUR_NGROK_AUTH_TOKEN"
conf.get_default().auth_token = "2X5BA7ayiL0lJZEGuOANriJn0kk_2UevpLCLrYRbTi1ToAXmP"
BUFFER = 1024
NGROK_TOKEN = "2X5BA7ayiL0lJZEGuOANriJn0kk_2UevpLCLrYRbTi1ToAXmP"
NGROK_DIR = "tools"
NGROK_FILENAME = "ngrok.exe" if platform.system() == "Windows" else "ngrok"
NGROK_PATH = os.path.join(NGROK_DIR, NGROK_FILENAME)
# ==========================

def ngrok_exists():
    return os.path.exists(NGROK_PATH)

def download_ngrok():
    print("[↓] Downloading ngrok...")
    system = platform.system()

    if system == "Windows":
        url = "https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-stable-windows-amd64.zip"
    elif system == "Linux":
        url = "https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-stable-linux-amd64.zip"
    elif system == "Darwin":
        url = "https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-stable-darwin-amd64.zip"
    else:
        raise Exception("Unsupported OS")

    os.makedirs(NGROK_DIR, exist_ok=True)
    zip_path = os.path.join(NGROK_DIR, "ngrok.zip")
    urllib.request.urlretrieve(url, zip_path)

    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(NGROK_DIR)
    os.remove(zip_path)

    os.chmod(NGROK_PATH, 0o755)
    print("[✓] ngrok downloaded and ready!")

def choose_file():
    path = filedialog.askopenfilename(title="Chọn file để gửi")
    return path


def send_file(conn, path):
    filesize = os.path.getsize(path)
    header = json.dumps({"filename": os.path.basename(path), "filesize": filesize}).encode() + b"\n"
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
        data = conn.recv(BUFFER)
        if not data:
            break
        if file:
            file.write(data)
            remaining -= len(data)
            if remaining <= 0:
                file.close()
                print(f"[*] Đã nhận xong file: {file.name}")
                break
        else:
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
    conn.close()


def start_server_and_send(path, port, tunnel):
    listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    listener.bind(("0.0.0.0", port))
    listener.listen(1)
    print(f"[*] Đang chờ kết nối đến trên port {port}...")
    conn, addr = listener.accept()
    print(f"[*] Nhận kết nối từ {addr}")
    send_file(conn, path)
    conn.close()
    listener.close()
    ngrok.disconnect(tunnel.public_url)
    ngrok.kill()
    print("[*] Hoàn tất gửi file và đóng server.")


def send_button_clicked():
    path = choose_file()
    if not path:
        print("[!] Không có file được chọn.")
        return
    port = simpledialog.askinteger("Port", "Nhập port để lắng nghe:", minvalue=1, maxvalue=65535)
    if not port:
        print("[!] Port không hợp lệ.")
        return
    tunnel = ngrok.connect(port, "tcp")
    print(f"[*] Ngrok tunnel đã sẵn sàng: {tunnel.public_url}")
    threading.Thread(target=start_server_and_send, args=(path, port, tunnel), daemon=True).start()


def receive_button_clicked():
    addr = simpledialog.askstring("Kết nối", "Nhập địa chỉ ngrok (tcp://host:port):")
    if not addr:
        print("[!] Địa chỉ không hợp lệ.")
        return
    if addr.startswith("tcp://"):
        addr = addr[6:]
    try:
        host, port_str = addr.split(":")
        port = int(port_str)
    except ValueError:
        print("[!] Địa chỉ không hợp lệ.")
        return
    conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        conn.connect((host, port))
        print(f"[*] Đã kết nối tới {host}:{port}, đang nhận file...")
        threading.Thread(target=recv_loop, args=(conn,), daemon=True).start()
    except Exception as e:
        print(f"[!] Kết nối thất bại: {e}")


def main():
    root = Tk()
    root.title("Peer-to-Peer File Transfer")
    root.geometry("300x150")
    Button(root, text="Gửi file", command=send_button_clicked).pack(pady=10)
    Button(root, text="Nhận file", command=receive_button_clicked).pack(pady=10)
    root.mainloop()

if __name__ == "__main__":
    main()
