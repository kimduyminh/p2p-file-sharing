import tkinter as tk
from tkinter import messagebox
import os
import hashlib
from main_gui import open_main_gui  # Gọi sang GUI chính sau xác thực

PASSWORD_FILE = "password.txt"

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
            messagebox.showinfo("Thành công", "Tạo mật khẩu mới!")
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
