import sys
import os
import json
import asyncio
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from pathlib import Path
from PIL import Image, ImageDraw
import pystray
from social_p2p import Peer, DEFAULT_PORT

TRANSLATIONS = {
    'en': {
        'Username:': 'Username:',
        'Port:': 'Port:',
        'Bootstrap (ip:port):': 'Bootstrap (ip:port):',
        'Start': 'Start',
        'Search user:': 'Search user:',
        'Lookup': 'Lookup',
        'New Post:': 'New Post:',
        'Publish': 'Publish',
        'Your Posts:': 'Your Posts:',
        'Message:': 'Message:',
        'Send': 'Send',
        'Inbox:': 'Inbox:',
    },
    'es': {
        'Username:': 'Usuario:',
        'Port:': 'Puerto:',
        'Bootstrap (ip:port):': 'Nodo inicial (ip:puerto):',
        'Start': 'Comenzar',
        'Search user:': 'Buscar usuario:',
        'Lookup': 'Buscar',
        'New Post:': 'Nueva publicación:',
        'Publish': 'Publicar',
        'Your Posts:': 'Tus publicaciones:',
        'Message:': 'Mensaje:',
        'Send': 'Enviar',
        'Inbox:': 'Bandeja de entrada:',
    },
}

DEFAULT_DATA_DIR = Path.home() / '.p2psocial'
CONFIG_FILE = 'config.json'


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('P2P Social')
        self.geometry('600x400')
        style = ttk.Style(self)
        try:
            if sys.platform == 'win32':
                style.theme_use('vista')
            else:
                style.theme_use('clam')
        except tk.TclError:
            pass  # fallback to default theme

        self.peer = None
        self.tray = None
        self.protocol('WM_DELETE_WINDOW', self.on_close)

        self.config_data = {}
        self.data_dir = DEFAULT_DATA_DIR
        self.minimize_to_tray = False
        self.lang = 'en'
        self.load_or_setup()

    def t(self, text: str) -> str:
        return TRANSLATIONS.get(self.lang, TRANSLATIONS['en']).get(text, text)

    # -------- Configuration management ---------
    def load_or_setup(self):
        cfg_path = self.data_dir / CONFIG_FILE
        if cfg_path.exists():
            try:
                self.config_data = json.load(open(cfg_path, 'r', encoding='utf-8'))
                self.minimize_to_tray = self.config_data.get('minimize_to_tray', False)
                self.data_dir = Path(self.config_data.get('data_dir', self.data_dir))
                self.lang = self.config_data.get('lang', 'en')
            except Exception:
                self.config_data = {}
        else:
            self.first_time_setup()
            self.save_config()

        username = self.config_data.get('username')
        if username and (self.data_dir / f"{username}_profile.json").exists():
            self.username_var = tk.StringVar(value=username)
            self.port_var = tk.IntVar(value=self.config_data.get('port', DEFAULT_PORT))
            self.bootstrap_var = tk.StringVar(value=self.config_data.get('bootstrap', ''))
            self.start_peer(auto=True)
        else:
            self.create_connect_frame()

    def first_time_setup(self):
        if messagebox.askyesno('Setup', f'Change default data location ({self.data_dir})?'):
            new_dir = filedialog.askdirectory(title='Select data folder')
            if new_dir:
                self.data_dir = Path(new_dir)
        self.minimize_to_tray = messagebox.askyesno('Setup', 'Allow program to run in background when window is closed?')
        if messagebox.askyesno('Language', 'Use Spanish interface?'):
            self.lang = 'es'

    def save_config(self):
        cfg_path = self.data_dir / CONFIG_FILE
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.config_data['lang'] = self.lang
        with open(cfg_path, 'w', encoding='utf-8') as f:
            json.dump(self.config_data, f)

    def create_connect_frame(self):
        frame = ttk.Frame(self)
        frame.pack(fill='both', expand=True, padx=10, pady=10)
        self.connect_frame = frame

        ttk.Label(frame, text=self.t('Username:')).grid(row=0, column=0, sticky='w')
        self.username_var = tk.StringVar()
        ttk.Entry(frame, textvariable=self.username_var).grid(row=0, column=1)

        ttk.Label(frame, text=self.t('Port:')).grid(row=1, column=0, sticky='w')
        self.port_var = tk.IntVar(value=DEFAULT_PORT)
        ttk.Entry(frame, textvariable=self.port_var).grid(row=1, column=1)

        ttk.Label(frame, text=self.t('Bootstrap (ip:port):')).grid(row=2, column=0, sticky='w')
        self.bootstrap_var = tk.StringVar()
        ttk.Entry(frame, textvariable=self.bootstrap_var).grid(row=2, column=1)

        ttk.Button(frame, text=self.t('Start'), command=self.start_peer).grid(row=3, column=0, columnspan=2, pady=10)

    def create_main_frame(self):
        frame = ttk.Frame(self)
        frame.pack(fill='both', expand=True, padx=10, pady=10)
        self.main_frame = frame

        self.search_var = tk.StringVar()
        ttk.Label(frame, text=self.t('Search user:')).grid(row=0, column=0, sticky='w')
        ttk.Entry(frame, textvariable=self.search_var).grid(row=0, column=1, sticky='ew')
        ttk.Button(frame, text=self.t('Lookup'), command=self.lookup_user).grid(row=0, column=2, padx=5)
        frame.columnconfigure(1, weight=1)

        self.profile_text = tk.Text(frame, height=6, state='disabled')
        self.profile_text.grid(row=1, column=0, columnspan=3, pady=5, sticky='nsew')
        frame.rowconfigure(1, weight=1)

        ttk.Label(frame, text=self.t('New Post:')).grid(row=2, column=0, sticky='w')
        self.post_var = tk.StringVar()
        ttk.Entry(frame, textvariable=self.post_var).grid(row=2, column=1, sticky='ew')
        ttk.Button(frame, text=self.t('Publish'), command=self.publish_post).grid(row=2, column=2, padx=5)

        ttk.Label(frame, text=self.t('Your Posts:')).grid(row=3, column=0, sticky='nw')
        self.post_box = tk.Text(frame, height=5, state='disabled')
        self.post_box.grid(row=3, column=1, columnspan=2, sticky='nsew')
        frame.rowconfigure(3, weight=1)

        ttk.Label(frame, text=self.t('Message:')).grid(row=4, column=0, sticky='w')
        self.msg_var = tk.StringVar()
        ttk.Entry(frame, textvariable=self.msg_var).grid(row=4, column=1, sticky='ew')
        ttk.Button(frame, text=self.t('Send'), command=self.send_message).grid(row=4, column=2, padx=5)

        ttk.Label(frame, text=self.t('Inbox:')).grid(row=5, column=0, sticky='nw')
        self.inbox = tk.Text(frame, state='disabled')
        self.inbox.grid(row=5, column=1, columnspan=2, sticky='nsew')
        frame.rowconfigure(5, weight=1)

    def start_peer(self, auto=False):
        username = self.username_var.get().strip()
        if not username:
            messagebox.showerror('Error', 'Username required')
            return
        port = self.port_var.get()
        bootstrap = self.bootstrap_var.get().strip() or None
        profile_path = self.data_dir / f"{username}_profile.json"
        self.peer = Peer(username, port=port, profile_path=profile_path)
        try:
            asyncio.run(self.peer.start(bootstrap))
        except Exception as exc:
            messagebox.showerror('Error', f'Could not start peer: {exc}')
            return
        self.config_data['username'] = username
        self.config_data['port'] = port
        self.config_data['bootstrap'] = bootstrap or ''
        self.config_data['data_dir'] = str(self.data_dir)
        self.config_data['minimize_to_tray'] = self.minimize_to_tray
        self.save_config()
        if not auto:
            self.connect_frame.destroy()
        self.create_main_frame()
        self.after(5000, self.check_messages)
        self.after(5000, self.refresh_posts)

    def lookup_user(self):
        user = self.search_var.get().strip()
        if not user:
            return
        try:
            profile, addr = asyncio.run(self.peer.lookup_user(user))
        except Exception as exc:
            messagebox.showerror('Error', str(exc))
            return
        self.profile_text.configure(state='normal')
        self.profile_text.delete('1.0', 'end')
        if profile:
            self.profile_text.insert('end', f'Profile for {user}\n{profile}\nAddress: {addr}')
        else:
            self.profile_text.insert('end', 'User not found')
        self.profile_text.configure(state='disabled')

    def send_message(self):
        msg = self.msg_var.get().strip()
        to_user = self.search_var.get().strip()
        if not msg or not to_user:
            return
        try:
            asyncio.run(self.peer.send_message(to_user, msg))
            messagebox.showinfo('Info', 'Message queued')
            self.msg_var.set('')
        except Exception as exc:
            messagebox.showerror('Error', str(exc))

    def publish_post(self):
        text = self.post_var.get().strip()
        if not text:
            return
        try:
            asyncio.run(self.peer.add_post(text))
            self.post_var.set('')
            self.refresh_posts()
        except Exception as exc:
            messagebox.showerror('Error', str(exc))

    def check_messages(self):
        try:
            msgs = asyncio.run(self.peer.fetch_messages())
            if msgs:
                self.inbox.configure(state='normal')
                for m in msgs:
                    self.inbox.insert('end', f"From {m['from']}: {m['msg']}\n")
                self.inbox.configure(state='disabled')
                self.inbox.see('end')
        except Exception:
            pass
        self.after(5000, self.check_messages)

    def refresh_posts(self):
        try:
            posts = asyncio.run(self.peer.fetch_posts(self.peer.username))
            self.post_box.configure(state='normal')
            self.post_box.delete('1.0', 'end')
            for p in posts:
                self.post_box.insert('end', f"{p.timestamp}: {p.text} ({p.likes} likes)\n")
            self.post_box.configure(state='disabled')
        except Exception:
            pass
        self.after(5000, self.refresh_posts)

    # ------------- System tray handling -------------
    def create_tray_icon(self):
        size = 64
        image = Image.new('RGB', (size, size), 'white')
        d = ImageDraw.Draw(image)
        d.rectangle((0, 0, size, size), fill='white')
        d.text((size//4, size//4), 'P2P', fill='black')
        menu = pystray.Menu(pystray.MenuItem('Open', self.show_window),
                            pystray.MenuItem('Quit', self.quit_app))
        self.tray = pystray.Icon('p2p-social', image, 'P2P Social', menu)

    def on_close(self):
        if self.minimize_to_tray:
            if not self.tray:
                self.create_tray_icon()
                self.withdraw()
                self.tray.run_detached()
            else:
                self.withdraw()
        else:
            self.quit_app()

    def show_window(self, *args):
        self.deiconify()
        if self.tray:
            self.tray.stop()
            self.tray = None

    def quit_app(self, *args):
        if self.tray:
            self.tray.stop()
            self.tray = None
        self.destroy()


def main():
    app = App()
    app.mainloop()


if __name__ == '__main__':
    main()
