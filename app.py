import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import hashlib

#test
PASSWORD_FILE = "password.txt"
PUBLIC_KEY = "RSA-2048:ABCD1234EFGH5678"
DEFAULT_IP = "127.0.0.1"
DEFAULT_PORT = 5000

#password
def hash_password(pwd):
    return hashlib.sha256(pwd.encode()).hexdigest()

def save_password(pwd):
    with open(PASSWORD_FILE, "w") as f:
        f.write(hash_password(pwd))

def check_password(pwd):
    with open(PASSWORD_FILE, "r") as f:
        return hash_password(pwd) == f.read().strip()

def start_auth():
    def submit():
        password = entry.get()
        if not password:
            messagebox.showwarning("Thiếu", "Vui lòng nhập mật khẩu!")
            return

        if not os.path.exists(PASSWORD_FILE):
            save_password(password)
            messagebox.showinfo("Thành công", "Đăng ký thành công")
            root.destroy()
            open_main_gui()
        else:
            if check_password(password):
                messagebox.showinfo("OK", "Đăng nhập thành công")
                root.destroy()
                open_main_gui()
            else:
                messagebox.showerror("Sai", "Mật khẩu không đúng!")

    root = tk.Tk()
    root.title("Xác thực")
    root.geometry("300x150")

    tk.Label(root, text="Nhập mật khẩu:").pack(pady=10)
    entry = tk.Entry(root, show="*")
    entry.pack()
    tk.Button(root, text="OK", command=submit).pack(pady=10)

    root.mainloop()

#log
def show_log(text_widget, msg):
    text_widget.insert(tk.END, msg + '\n')
    text_widget.see(tk.END)

send_log_widget = None
send_progress_widget = None

#Send
def send_mode():
    global send_log_widget, send_progress_widget

    def select_file():
        file_path = filedialog.askopenfilename()
        if file_path:
            show_log(log, f"[Send] Đã chọn file: {file_path}")
            progress['value'] = 0
            show_log(log, "[Send] File sẵn sàng để gửi")

    win = tk.Toplevel()
    win.title("Send")

    tk.Label(win, text=f"Your IP: {DEFAULT_IP}").pack()
    tk.Label(win, text=f"Your Port: {DEFAULT_PORT}").pack()
    tk.Label(win, text=f"Public Key: {PUBLIC_KEY}").pack()

    ttk.Button(win, text="Chọn file để gửi", command=select_file).pack(pady=5)

    progress = ttk.Progressbar(win, length=300)
    progress.pack(pady=10)

    log = tk.Text(win, height=5, width=50)
    log.pack()
    show_log(log, "[Send] Ready")

    send_log_widget = log
    send_progress_widget = progress

#receive
def receive_mode():
    def connect_and_receive():
        ip = ip_entry.get()
        port = port_entry.get()
        pubkey = key_entry.get()

        progress['value'] = 0
        show_log(log, f"[Receive] Kết nối đến {ip}:{port}...")
        show_log(log, "[Receive] Đã kết nối, đang tải file...")

        for i in range(0, 101, 20):
            progress['value'] = i
            progress.update_idletasks()
            win.after(200)

            if send_log_widget and send_progress_widget:
                send_progress_widget['value'] = i
                send_progress_widget.update_idletasks()
                if i == 0:
                    show_log(send_log_widget, "[Send] Client đã kết nối")
                elif i < 100:
                    show_log(send_log_widget, "[Send] Đang gửi file...")
                else:
                    show_log(send_log_widget, "[Send] Gửi thành công")

        show_log(log, "[Receive] Tải file thành công")

    win = tk.Toplevel()
    win.title("Receive")

    tk.Label(win, text="IP:").pack()
    ip_entry = tk.Entry(win)
    ip_entry.pack()

    tk.Label(win, text="Port:").pack()
    port_entry = tk.Entry(win)
    port_entry.pack()

    tk.Label(win, text="Public Key:").pack()
    key_entry = tk.Entry(win)
    key_entry.pack()

    ttk.Button(win, text="OK", command=connect_and_receive).pack(pady=5)

    progress = ttk.Progressbar(win, length=300)
    progress.pack(pady=10)

    log = tk.Text(win, height=5, width=50)
    log.pack()
    show_log(log, "[Receive] Waiting")

#Main
def open_main_gui():
    main = tk.Tk()
    main.title("P2P File Sharing")
    main.geometry("300x200")

    tk.Label(main, text="Welcome", font=("Arial", 14)).pack(pady=10)
    tk.Button(main, text="Send", command=send_mode).pack(pady=5)
    tk.Button(main, text="Receive", command=receive_mode).pack(pady=5)

    main.mainloop()

if __name__ == "__main__":
    start_auth()
