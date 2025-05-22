import tkinter as tk
from tkinter import ttk

def show_log(text_widget, msg):
    text_widget.insert(tk.END, msg + '\n')
    text_widget.see(tk.END)

def send_mode():
    win = tk.Toplevel()
    win.title("Send")
    tk.Label(win, text="Your IP: 127.0.0.1").pack()
    tk.Label(win, text="Your Port: 5000").pack()
    tk.Label(win, text="Public Key: ...").pack()

    progress = ttk.Progressbar(win, length=300)
    progress.pack(pady=10)

    log = tk.Text(win, height=5, width=50)
    log.pack()
    show_log(log, "[Send] Ready")

def receive_mode():
    win = tk.Toplevel()
    win.title("Receive")

    tk.Label(win, text="IP:").pack()
    tk.Entry(win).pack()
    tk.Label(win, text="Port:").pack()
    tk.Entry(win).pack()
    tk.Label(win, text="Public Key:").pack()
    tk.Entry(win).pack()

    progress = ttk.Progressbar(win, length=300)
    progress.pack(pady=10)

    log = tk.Text(win, height=5, width=50)
    log.pack()
    show_log(log, "[Receive] Waiting")

def open_main_gui():
    main = tk.Tk()
    main.title("P2P File Sharing")
    main.geometry("300x200")

    tk.Label(main, text="Welcome", font=("Arial", 14)).pack(pady=10)
    tk.Button(main, text="Send", command=send_mode).pack(pady=5)
    tk.Button(main, text="Receive", command=receive_mode).pack(pady=5)

    main.mainloop()
