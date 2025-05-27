import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import glob
import socket
import json
import threading
import hashlib
import ecc_keygen
import ecc_signing_and_verify
import file_handling
from pyngrok import ngrok

# Constants
DEFAULT_IP = "127.0.0.1"
DEFAULT_PORT = 5000
BUFFER_SIZE = 1024

# Key management
def hash_password(pwd):
    return hashlib.sha256(pwd.encode()).hexdigest()

def create_keys_pair(pwd):
    ecc_keygen.ecc_keygen(pwd)

def load_keys_pair(pwd):
    global private_key, public_key
    key_mgr = ecc_keygen.ecc_keygen(pwd)
    private_key, public_key = key_mgr.load_key(pwd)

# Auth window
def start_auth():
    def submit():
        pwd = entry.get().strip()
        if not pwd:
            messagebox.showwarning("Thiếu", "Vui lòng nhập mật khẩu!")
            return
        if not os.path.exists("private_key.pem"):
            create_keys_pair(pwd)
            messagebox.showinfo("Thành công", "Đăng ký thành công")
        try:
            load_keys_pair(pwd)
            messagebox.showinfo("OK", "Đăng nhập thành công")
            root.destroy()
            open_main_gui()
        except Exception:
            messagebox.showerror("Sai", "Mật khẩu không đúng!")

    root = tk.Tk()
    root.title("Xác thực")
    root.geometry("300x150")
    tk.Label(root, text="Nhập mật khẩu:").pack(pady=10)
    entry = tk.Entry(root, show="*")
    entry.pack()
    tk.Button(root, text="OK", command=submit).pack(pady=10)
    root.mainloop()

# Helper log
def show_log(widget, msg):
    widget.insert(tk.END, msg + "\n")
    widget.see(tk.END)

# Send window
def send_mode():
    signer = ecc_signing_and_verify.ecc_signing_and_verify(
        private_key=private_key,
        public_key=public_key,
        public_key_sender=None
    )
    handler = file_handling.file_handling(signer)
    selected_file = {'path': None}

    def choose_file():
        path = filedialog.askopenfilename()
        if path:
            selected_file['path'] = path
            show_log(log, f"[Send] File đã chọn: {path}")
        else:
            show_log(log, "[Send] Chưa chọn file nào.")

    def send_parts():
        if not selected_file['path']:
            messagebox.showerror("Lỗi", "Chưa chọn file để gửi!")
            return
        # Split file
        handler.split_file(selected_file['path'])
        parts = sorted(glob.glob(f"{os.path.basename(selected_file['path'])}.part*"))
        # if not parts:
        #     messagebox.showerror("Lỗi", "Không tách được file, kiểm tra lại đường dẫn!")
        #     return
        show_log(log, f"[Send] Tách thành {len(parts)} phần.")
        # Bind IP/Port
        ip = ip_entry.get().strip() or DEFAULT_IP
        try:
            port = int(port_entry.get().strip() or DEFAULT_PORT)
        except ValueError:
            messagebox.showerror("Lỗi", "Port không hợp lệ!")
            return
        # Prompt file transfer start
        show_log(log, "[Send] Khởi tạo tunnel và listener...")
        tunnel = ngrok.connect(port, "tcp")
        show_log(log, f"[Send] Ngrok URL: {tunnel.public_url}")
        srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            srv.bind((ip, port))
        except Exception as e:
            messagebox.showerror("Lỗi", f"Bind thất bại: {e}")
            ngrok.disconnect(tunnel.public_url)
            return
        srv.listen(1)
        show_log(log, f"[Send] Đang chờ kết nối tại {ip}:{port}...")

        def worker():
            try:
                conn, addr = srv.accept()
                show_log(log, f"[Send] Đã kết nối từ {addr}")
                for p in parts:
                    size = os.path.getsize(p)
                    hdr = json.dumps({"filename": os.path.basename(p), "filesize": size}).encode() + b"\n"
                    conn.sendall(hdr)
                    with open(p, "rb") as f:
                        while True:
                            chunk = f.read(BUFFER_SIZE)
                            if not chunk: break
                            conn.sendall(chunk)
                    show_log(log, f"[Send] Gửi xong {os.path.basename(p)}")
                conn.close()
                show_log(log, "[Send] Hoàn tất gửi tất cả parts.")
            except Exception as e:
                show_log(log, f"[Send] Lỗi trong quá trình gửi: {e}")
            finally:
                srv.close()
                ngrok.disconnect(tunnel.public_url)
                show_log(log, "[Send] Đóng kết nối và tunnel.")

        threading.Thread(target=worker, daemon=True).start()

    win = tk.Toplevel()
    win.title("Send")
    win.geometry("400x350")
    tk.Label(win, text="Bind IP:").pack()
    ip_entry = tk.Entry(win); ip_entry.insert(0, DEFAULT_IP); ip_entry.pack()
    tk.Label(win, text="Bind Port:").pack()
    port_entry = tk.Entry(win); port_entry.insert(0, str(DEFAULT_PORT)); port_entry.pack()
    ttk.Button(win, text="Chọn file", command=choose_file).pack(pady=5)
    ttk.Button(win, text="Gửi file", command=send_parts).pack(pady=5)
    log = tk.Text(win, height=12); log.pack(fill=tk.BOTH, expand=True)
    show_log(log, "[Send] Sẵn sàng.")

# Receive window
def receive_mode():
    signer = ecc_signing_and_verify.ecc_signing_and_verify(
        private_key=private_key,
        public_key=public_key,
        public_key_sender=None
    )
    handler = file_handling.file_handling(signer)
    save_dir = {'path': None}

    def choose_save_dir():
        d = filedialog.askdirectory(title="Chọn thư mục lưu file nhận")
        if d:
            save_dir['path'] = d
            show_log(log_r, f"[Recv] Lưu vào: {d}")
        else:
            show_log(log_r, "[Recv] Chưa chọn thư mục lưu.")

    def receive_parts():
        if not save_dir['path']:
            messagebox.showerror("Lỗi", "Chưa chọn thư mục lưu!")
            return
        addr = addr_entry.get().strip()
        if addr.startswith("tcp://"): addr = addr[6:]
        try:
            host, prt = addr.split(":"); port = int(prt)
        except:
            messagebox.showerror("Lỗi", "Địa chỉ không hợp lệ!")
            return
        show_log(log_r, f"[Recv] Kết nối tới {host}:{port}...")
        conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            conn.connect((host, port))
        except Exception as e:
            messagebox.showerror("Lỗi", f"Kết nối thất bại: {e}")
            return
        show_log(log_r, "[Recv] Đã kết nối, bắt đầu nhận...")
        # change cwd to save dir
        os.makedirs(save_dir['path'], exist_ok=True)
        os.chdir(save_dir['path'])
        while True:
            hdr = b""
            while b"\n" not in hdr:
                d = conn.recv(1)
                if not d: break
                hdr += d
            if not hdr: break
            info = json.loads(hdr.decode().strip())
            fname, remain = info["filename"], info["filesize"]
            with open(fname, "wb") as f:
                while remain>0:
                    data = conn.recv(min(BUFFER_SIZE, remain))
                    if not data: break
                    f.write(data)
                    remain -= len(data)
            show_log(log_r, f"[Recv] Nhận xong {fname}")
        conn.close()
        # merge parts
        handler.merge_chunks()
        show_log(log_r, "[Recv] Đã ghép file gốc và kết thúc.")

    win = tk.Toplevel()
    win.title("Receive")
    win.geometry("400x300")
    ttk.Button(win, text="Chọn thư mục lưu", command=choose_save_dir).pack(pady=5)
    tk.Label(win, text="Ngrok TCP URL:").pack(pady=5)
    addr_entry = tk.Entry(win, width=40); addr_entry.pack()
    ttk.Button(win, text="Nhận file", command=receive_parts).pack(pady=5)
    log_r = tk.Text(win, height=12); log_r.pack(fill=tk.BOTH, expand=True)
    show_log(log_r, "[Recv] Chờ thao tác...")

# Main

def open_main_gui():
    root = tk.Tk()
    root.title("P2P File Sharing")
    root.geometry("300x200")
    tk.Label(root, text="Welcome", font=("Arial", 14)).pack(pady=10)
    ttk.Button(root, text="Send", command=send_mode).pack(pady=5)
    ttk.Button(root, text="Receive", command=receive_mode).pack(pady=5)
    root.mainloop()

if __name__ == "__main__":
    start_auth()