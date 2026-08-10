import json
import os
import queue
import re
import subprocess
import sys
import tempfile
import threading
import time
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, scrolledtext, ttk

from bot import BOOST_CHOICES
from config import DEVICE_IP, DEVICE_PORT
from runtime_paths import APP_DIR, FROZEN, RESOURCE_DIR


BASE_DIR = RESOURCE_DIR
SETTINGS_FILE = APP_DIR / "gui_settings.json"


class CookieRunBotGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("CookieRun Classic Bot")
        self.root.geometry("720x500")
        self.root.minsize(660, 430)
        self.root.configure(bg="#f4f6fb")
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

        self.process = None
        self.process_mode = None
        self.stop_requested = False
        self.events = queue.Queue()
        self.connection_test_running = False
        self._session_started_at = None
        self._session_last_elapsed_second = None
        self._heart_sent_count = None

        self.ip_var = tk.StringVar(value=DEVICE_IP)
        self.port_var = tk.StringVar(value=str(DEVICE_PORT))
        self.fast_start_var = tk.BooleanVar(value=False)
        self.cookie_relay_var = tk.BooleanVar(value=False)
        self.use_boost_var = tk.BooleanVar(value=False)
        self.claim_relic_rewards_var = tk.BooleanVar(value=True)
        self.max_runs_var = tk.StringVar(value="0")
        self.status_var = tk.StringVar(value="พร้อมใช้งาน")
        self.session_stats_var = tk.StringVar(
            value="รอบ 0/0 • Coins 0 (เฉลี่ย 0) • EXP 0 (เฉลี่ย 0)"
        )
        self.session_runs_var = tk.StringVar(value="0 / 0")
        self.session_coins_total_var = tk.StringVar(value="0")
        self.session_coins_average_var = tk.StringVar(value="เฉลี่ย 0 / รอบ")
        self.session_exp_total_var = tk.StringVar(value="0")
        self.session_exp_average_var = tk.StringVar(value="เฉลี่ย 0 / รอบ")
        self.session_elapsed_var = tk.StringVar(value="00:00:00")
        self.session_elapsed_detail_var = tk.StringVar(value="ยังไม่ได้เริ่ม")

        self._create_app_icon()
        self._configure_styles()
        self._build_ui()
        self._load_settings()
        self._toggle_boost()
        self.root.after(100, self._poll_events)

    def _create_app_icon(self):
        """Create a tiny CookieRun-style app icon without external image files."""
        icon = tk.PhotoImage(width=32, height=32)
        icon.put("#6c5ce7", to=(0, 0, 32, 32))
        for y in range(32):
            for x in range(32):
                distance = (x - 16) ** 2 + (y - 16) ** 2
                if distance <= 12 ** 2:
                    icon.put("#e99b35" if distance > 10 ** 2 else "#f6bd4a", (x, y))
        for dot_x, dot_y in ((11, 11), (20, 10), (14, 20), (22, 19)):
            for y in range(dot_y - 2, dot_y + 2):
                for x in range(dot_x - 2, dot_x + 2):
                    icon.put("#6c3d2d", (x, y))
        self.app_icon = icon
        self.root.iconphoto(True, icon)

    def _configure_styles(self):
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("App.TFrame", background="#f4f6fb")
        style.configure("Card.TFrame", background="#ffffff")
        style.configure("TLabel", background="#ffffff", foreground="#202336", font=("Segoe UI", 10))
        style.configure("Muted.TLabel", background="#ffffff", foreground="#81869a", font=("Segoe UI", 9))
        style.configure(
            "Count.TLabel",
            background="#f0edff",
            foreground="#6551d7",
            font=("Segoe UI Semibold", 9),
            padding=(10, 5),
        )
        style.configure(
            "TButton",
            background="#f2f3f8",
            foreground="#464b60",
            bordercolor="#f2f3f8",
            lightcolor="#f2f3f8",
            darkcolor="#f2f3f8",
            borderwidth=0,
            relief="flat",
            font=("Segoe UI Semibold", 10),
            padding=(13, 9),
        )
        style.map(
            "TButton",
            background=[("active", "#e8eaf2"), ("pressed", "#dde0e9")],
            foreground=[("disabled", "#a3a7b6")],
        )
        style.configure(
            "Accent.TButton",
            background="#6c5ce7",
            foreground="#ffffff",
            bordercolor="#6c5ce7",
            lightcolor="#6c5ce7",
            darkcolor="#6c5ce7",
            borderwidth=0,
            font=("Segoe UI Semibold", 11),
            padding=(18, 12),
        )
        style.map(
            "Accent.TButton",
            background=[("active", "#7a6bed"), ("pressed", "#5847cf"), ("disabled", "#4b4e6b")],
            foreground=[("disabled", "#9092a8")],
        )
        style.configure(
            "Danger.TButton",
            background="#2a2d49",
            foreground="#ff94ac",
            bordercolor="#2a2d49",
            lightcolor="#2a2d49",
            darkcolor="#2a2d49",
            borderwidth=0,
            font=("Segoe UI Semibold", 10),
            padding=(16, 11),
        )
        style.map("Danger.TButton", background=[("active", "#363a5a"), ("pressed", "#20233c")])
        style.configure(
            "Heart.TButton",
            background="#2e9f78",
            foreground="#ffffff",
            bordercolor="#2e9f78",
            lightcolor="#2e9f78",
            darkcolor="#2e9f78",
            borderwidth=0,
            font=("Segoe UI Semibold", 10),
            padding=(14, 10),
        )
        style.map(
            "Heart.TButton",
            background=[("active", "#38ad85"), ("pressed", "#278766"), ("disabled", "#425a58")],
            foreground=[("disabled", "#94aaa7")],
        )
        style.configure(
            "TCheckbutton",
            background="#ffffff",
            foreground="#3f4459",
            font=("Segoe UI", 10),
            padding=(4, 5),
        )
        style.map(
            "TCheckbutton",
            background=[("active", "#ffffff")],
            indicatorcolor=[("selected", "#6c5ce7"), ("!selected", "#e6e8f0")],
        )
        style.configure(
            "TEntry",
            fieldbackground="#f7f8fc",
            foreground="#272b3d",
            bordercolor="#e5e7ef",
            lightcolor="#e5e7ef",
            darkcolor="#e5e7ef",
            padding=(10, 8),
        )
        style.map("TEntry", bordercolor=[("focus", "#7b6dea")], lightcolor=[("focus", "#7b6dea")])
        style.configure(
            "TCombobox",
            fieldbackground="#f7f8fc",
            background="#f7f8fc",
            bordercolor="#e5e7ef",
            lightcolor="#e5e7ef",
            darkcolor="#e5e7ef",
            padding=(9, 7),
        )
        style.map("TCombobox", bordercolor=[("focus", "#7b6dea")], lightcolor=[("focus", "#7b6dea")])
        style.configure(
            "TSpinbox",
            fieldbackground="#2a2d49",
            foreground="#ffffff",
            arrowcolor="#b9bdd2",
            bordercolor="#383b59",
            lightcolor="#383b59",
            darkcolor="#383b59",
            padding=(8, 7),
        )
    def _build_ui(self):
        shell = tk.Frame(self.root, bg="#f4f6fb")
        shell.pack(fill="both", expand=True)

        sidebar = tk.Frame(shell, bg="#171a2e", width=190)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        brand = tk.Frame(sidebar, bg="#171a2e")
        brand.pack(fill="x", padx=16, pady=(18, 20))
        logo = tk.Label(
            brand,
            text="🍪",
            bg="#6c5ce7",
            fg="#ffffff",
            width=2,
            height=1,
            font=("Segoe UI Emoji", 20),
        )
        logo.pack(side="left")
        brand_copy = tk.Frame(brand, bg="#171a2e")
        brand_copy.pack(side="left", padx=(11, 0))
        tk.Label(
            brand_copy,
            text="COOKIEBOT",
            bg="#171a2e",
            fg="#ffffff",
            font=("Segoe UI Semibold", 13),
        ).pack(anchor="w")
        tk.Label(
            brand_copy,
            text="CLASSIC  •  v1.4.2",
            bg="#171a2e",
            fg="#797e9b",
            font=("Segoe UI Semibold", 8),
        ).pack(anchor="w", pady=(1, 0))

        tk.Label(
            sidebar,
            text="BOT MENU",
            bg="#171a2e",
            fg="#696e8b",
            font=("Segoe UI Semibold", 8),
        ).pack(anchor="w", padx=18, pady=(0, 2))

        run_panel = tk.Frame(sidebar, bg="#20233b", padx=13, pady=14)
        run_panel.pack(fill="x", padx=13, pady=(8, 10))
        tk.Label(
            run_panel,
            text="RUN CONTROL",
            bg="#20233b",
            fg="#858aa4",
            font=("Segoe UI Semibold", 8),
        ).pack(anchor="w", pady=(0, 9))
        self.start_button = ttk.Button(
            run_panel,
            text="▶   START BOT",
            style="Accent.TButton",
            command=self._start_bot,
        )
        self.start_button.pack(fill="x")
        self.stop_button = ttk.Button(
            run_panel,
            text="■   STOP",
            style="Danger.TButton",
            command=self._stop_bot,
            state="disabled",
        )
        self.stop_button.pack(fill="x", pady=(7, 12))
        self.send_hearts_button = ttk.Button(
            run_panel,
            text="♥   ส่งหัวใจ",
            style="Heart.TButton",
            command=self._send_hearts,
        )
        self.send_hearts_button.pack(fill="x", pady=(0, 12))
        repeat_row = tk.Frame(run_panel, bg="#20233b")
        repeat_row.pack(fill="x")
        tk.Label(
            repeat_row,
            text="จำนวนรอบ",
            bg="#20233b",
            fg="#b7bbcc",
            font=("Segoe UI", 9),
        ).pack(side="left")
        self.max_runs_spinbox = ttk.Spinbox(
            repeat_row,
            from_=0,
            to=999,
            width=5,
            textvariable=self.max_runs_var,
            justify="center",
        )
        self.max_runs_spinbox.pack(side="right")
        tk.Label(
            run_panel,
            text="0 = เล่นต่อเนื่องไม่จำกัด",
            bg="#20233b",
            fg="#6f748e",
            font=("Segoe UI", 8),
        ).pack(anchor="w", pady=(7, 0))

        workspace = tk.Frame(shell, bg="#f4f6fb")
        workspace.pack(side="left", fill="both", expand=True)

        topbar = tk.Frame(workspace, bg="#ffffff", height=62)
        topbar.pack(fill="x")
        topbar.pack_propagate(False)
        title_block = tk.Frame(topbar, bg="#ffffff")
        title_block.pack(side="left", padx=18, pady=8)
        tk.Label(
            title_block,
            text="CookieRun Bot",
            bg="#ffffff",
            fg="#1f2233",
            font=("Segoe UI Semibold", 17),
        ).pack(anchor="w")
        tk.Label(
            title_block,
            text="ตั้งค่าการซื้อไอเทม แล้วเริ่มบอทได้ทันที",
            bg="#ffffff",
            fg="#8a8fa2",
            font=("Segoe UI", 9),
        ).pack(anchor="w", pady=(1, 0))
        self.status_label = tk.Label(
            topbar,
            textvariable=self.status_var,
            bg="#f0f1f6",
            fg="#54596d",
            font=("Segoe UI Semibold", 9),
            padx=13,
            pady=7,
        )
        self.status_label.pack(side="right", padx=18)

        body = tk.Frame(workspace, bg="#f4f6fb", padx=12, pady=10)
        body.pack(fill="both", expand=True)
        body.columnconfigure(0, weight=1)
        body.rowconfigure(3, weight=1)

        def make_card(row, pady=(0, 10)):
            card = tk.Frame(body, bg="#ffffff", highlightbackground="#e9ebf2", highlightthickness=1)
            card.grid(row=row, column=0, sticky="nsew", pady=pady)
            return card

        def add_header(parent, icon, title, subtitle=None):
            header = tk.Frame(parent, bg="#ffffff")
            header.pack(fill="x", padx=15, pady=(11, 8))
            tk.Label(
                header,
                text=icon,
                bg="#f0edff",
                fg="#6754dc",
                width=3,
                font=("Segoe UI Symbol", 11),
                padx=2,
                pady=5,
            ).pack(side="left")
            copy = tk.Frame(header, bg="#ffffff")
            copy.pack(side="left", padx=(10, 0))
            tk.Label(copy, text=title, bg="#ffffff", fg="#25283a", font=("Segoe UI Semibold", 11)).pack(anchor="w")
            if subtitle:
                tk.Label(copy, text=subtitle, bg="#ffffff", fg="#9095a7", font=("Segoe UI", 8)).pack(anchor="w")
            return header

        connection = make_card(0)
        add_header(connection, "⌁", "การเชื่อมต่อ ADB", "LDPlayer / Android Emulator")
        connection_fields = tk.Frame(connection, bg="#ffffff")
        connection_fields.pack(fill="x", padx=15, pady=(0, 12))
        connection_fields.columnconfigure(1, weight=1)
        ttk.Label(connection_fields, text="IP / HOST", style="Muted.TLabel").grid(row=0, column=0, sticky="w", padx=(0, 8))
        self.ip_entry = ttk.Entry(connection_fields, textvariable=self.ip_var, width=22)
        self.ip_entry.grid(row=0, column=1, sticky="ew", padx=(0, 14))
        ttk.Label(connection_fields, text="PORT", style="Muted.TLabel").grid(row=0, column=2, sticky="w", padx=(0, 8))
        self.port_entry = ttk.Entry(connection_fields, textvariable=self.port_var, width=9)
        self.port_entry.grid(row=0, column=3, padx=(0, 14))
        self.test_button = ttk.Button(connection_fields, text="↻  ทดสอบ ADB", command=self._test_connection)
        self.test_button.grid(row=0, column=4)

        options = make_card(1)
        add_header(options, "✦", "ตัวเลือกในแต่ละรอบ", "ตั้งค่าการซื้อและ Boost ก่อนเริ่มเล่น")
        option_fields = tk.Frame(options, bg="#ffffff")
        option_fields.pack(fill="x", padx=14, pady=(0, 11))
        option_fields.columnconfigure(3, weight=1)
        ttk.Checkbutton(option_fields, text="⚡  Fast Start", variable=self.fast_start_var).grid(row=0, column=0, sticky="w", padx=(0, 16))
        ttk.Checkbutton(option_fields, text="Cookie Relay (ซื้อเมื่อหมด)", variable=self.cookie_relay_var).grid(row=0, column=1, sticky="w", padx=(0, 16))
        ttk.Checkbutton(
            option_fields,
            text="Random Boost",
            variable=self.use_boost_var,
            command=self._toggle_boost,
        ).grid(row=0, column=2, sticky="w", padx=(0, 9))
        self.boost_combo = ttk.Combobox(
            option_fields,
            values=[name for name, _ in BOOST_CHOICES],
            state="readonly",
            width=22,
        )
        self.boost_combo.grid(row=0, column=3, sticky="ew")
        self.boost_combo.current(0)
        ttk.Checkbutton(
            option_fields,
            text="รับรางวัล Relic อัตโนมัติ (ปิดเพื่อดองชิ้นส่วน)",
            variable=self.claim_relic_rewards_var,
        ).grid(row=1, column=0, columnspan=4, sticky="w", pady=(7, 0))

        statistics = make_card(2)
        statistics_header = add_header(
            statistics,
            "▦",
            "สถิติการเล่นรอบปัจจุบัน",
            "คำนวณจาก Coins และ EXP บนหน้าผลลัพธ์หลังตัวคูณหยุดแล้ว",
        )
        ttk.Label(statistics_header, textvariable=self.session_elapsed_var, style="Count.TLabel").pack(side="right")
        ttk.Label(
            statistics,
            textvariable=self.session_stats_var,
            style="TLabel",
            font=("Segoe UI Semibold", 11),
        ).pack(fill="x", padx=16, pady=(0, 13))

        log_frame = make_card(3, pady=(0, 0))
        log_header = add_header(log_frame, "≡", "Live Activity", "สถานะการทำงานล่าสุดของบอท")
        ttk.Button(log_header, text="ล้าง Log", command=self._clear_log).pack(side="right")
        self.log = scrolledtext.ScrolledText(
            log_frame,
            wrap="word",
            height=4,
            font=("Cascadia Mono", 9),
            bg="#171a2e",
            fg="#dfe2ee",
            insertbackground="#ffffff",
            selectbackground="#5749bd",
            relief="flat",
            padx=12,
            pady=9,
            state="disabled",
        )
        self.log.pack(fill="both", expand=True, padx=15, pady=(0, 13))
        self._append_log("READY  •  ตั้งค่าไอเทม แล้วทดสอบ ADB ก่อนเริ่ม\n")

    def _python_executable(self):
        executable = Path(sys.executable)
        if executable.name.lower() == "pythonw.exe":
            console_python = executable.with_name("python.exe")
            if console_python.exists():
                return str(console_python)
        return str(executable)

    def _validated_connection(self):
        ip = self.ip_var.get().strip()
        if not ip:
            raise ValueError("กรุณากรอก IP หรือชื่ออุปกรณ์")
        try:
            port = int(self.port_var.get().strip())
        except ValueError as exc:
            raise ValueError("Port ต้องเป็นตัวเลข") from exc
        if not 1 <= port <= 65535:
            raise ValueError("Port ต้องอยู่ระหว่าง 1 ถึง 65535")
        return ip, port

    def _base_command(self, mode):
        ip, port = self._validated_connection()
        if FROZEN:
            command = [sys.executable, mode]
        else:
            command = [self._python_executable(), "-u", str(BASE_DIR / "main.py"), mode]
        command.extend(["--device-ip", ip, "--device-port", str(port)])
        return command

    @staticmethod
    def _new_worker_log_path():
        filename = f"cookierun_bot_{os.getpid()}_{time.time_ns()}.log"
        return Path(tempfile.gettempdir()) / filename

    def _start_bot(self):
        if self.process is not None and self.process.poll() is None:
            return
        try:
            command = self._base_command("--run-bot")
        except ValueError as exc:
            messagebox.showerror("ข้อมูลไม่ถูกต้อง", str(exc), parent=self.root)
            return

        self._append_play_options(command)
        try:
            max_runs = int(self.max_runs_var.get().strip() or "0")
            if max_runs < 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("จำนวนรอบไม่ถูกต้อง", "จำนวนรอบต้องเป็นเลข 0 ขึ้นไป", parent=self.root)
            return
        command.extend(["--max-runs", str(max_runs)])
        self._launch_process(command, "bot")

    def _send_hearts(self):
        """Run the friend-heart sender as a separate, stoppable worker."""
        if self.process is not None and self.process.poll() is None:
            return
        try:
            command = self._base_command("--send-hearts")
        except ValueError as exc:
            messagebox.showerror("ข้อมูลไม่ถูกต้อง", str(exc), parent=self.root)
            return

        self._heart_sent_count = None
        self._append_log("\nส่งหัวใจ: กรุณาเปิดรายชื่อเพื่อนบนหน้าหลักไว้ก่อน\n")
        self._launch_process(command, "hearts")

    def _append_play_options(self, command):
        if self.fast_start_var.get():
            command.append("--fast-start")
        if self.cookie_relay_var.get():
            command.append("--cookie-relay")
        if self.use_boost_var.get():
            command.extend(["--boost-index", str(self.boost_combo.current() + 1)])
        if not self.claim_relic_rewards_var.get():
            command.append("--keep-relic-parts")

    def _launch_process(self, command, mode):
        self._save_settings()
        creation_flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"
        worker_log = self._new_worker_log_path() if FROZEN else None
        if worker_log is not None:
            env["COOKIEBOT_LOG_FILE"] = str(worker_log)
        try:
            self.process = subprocess.Popen(
                command,
                cwd=APP_DIR,
                stdout=subprocess.DEVNULL if FROZEN else subprocess.PIPE,
                stderr=subprocess.DEVNULL if FROZEN else subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
                bufsize=1,
                creationflags=creation_flags,
                env=env,
            )
        except OSError as exc:
            activity = "ส่งหัวใจ" if mode == "hearts" else "บอท"
            self._append_log(f"เริ่ม{activity}ไม่สำเร็จ: {exc}\n")
            self._set_status("เริ่มไม่สำเร็จ", "error")
            return

        if mode == "hearts":
            self._append_log("──────── เริ่มส่งหัวใจทีละคน ────────\n")
        else:
            self._append_log("\n──────── เริ่มการทำงาน ────────\n")
        self.process_mode = mode
        if mode == "bot":
            self._begin_bot_session()
        self.stop_requested = False
        self._set_running_controls(True)
        self._set_status("กำลังส่งหัวใจ..." if mode == "hearts" else "บอทกำลังทำงาน", "running")
        if worker_log is not None:
            reader = self._read_bot_log
            reader_args = (self.process, worker_log)
        else:
            reader = self._read_bot_output
            reader_args = (self.process,)
        threading.Thread(target=reader, args=reader_args, daemon=True).start()

    def _read_bot_output(self, process):
        if process.stdout is not None:
            for line in iter(process.stdout.readline, ""):
                self.events.put(("log", line))
            process.stdout.close()
        return_code = process.wait()
        self.events.put(("bot_exit", (process, return_code)))

    def _read_bot_log(self, process, log_path):
        stream = None
        try:
            while stream is None and process.poll() is None:
                try:
                    stream = log_path.open("r", encoding="utf-8", errors="replace")
                except FileNotFoundError:
                    time.sleep(0.05)
            if stream is not None:
                while True:
                    line = stream.readline()
                    if line:
                        self.events.put(("log", line))
                    elif process.poll() is None:
                        time.sleep(0.05)
                    else:
                        for remaining in stream.readlines():
                            self.events.put(("log", remaining))
                        break
        finally:
            if stream is not None:
                stream.close()
            try:
                log_path.unlink(missing_ok=True)
            except OSError:
                pass
        return_code = process.wait()
        self.events.put(("bot_exit", (process, return_code)))

    def _stop_bot(self):
        process = self.process
        if process is None or process.poll() is not None:
            return
        self.stop_requested = True
        self._set_status("กำลังหยุด...", "testing")
        self.stop_button.configure(state="disabled")
        activity = "การส่งหัวใจ" if self.process_mode == "hearts" else "บอท"
        self._append_log(f"กำลังส่งคำสั่งหยุด{activity}...\n")
        threading.Thread(target=self._terminate_process, args=(process,), daemon=True).start()

    def _terminate_process(self, process):
        try:
            process.terminate()
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
        except OSError:
            pass

    def _test_connection(self):
        if self.connection_test_running or (self.process is not None and self.process.poll() is None):
            return
        try:
            command = self._base_command("--check-connection")
        except ValueError as exc:
            messagebox.showerror("ข้อมูลไม่ถูกต้อง", str(exc), parent=self.root)
            return

        self.connection_test_running = True
        self.test_button.configure(state="disabled")
        self.start_button.configure(state="disabled")
        self.send_hearts_button.configure(state="disabled")
        self._set_status("กำลังทดสอบ ADB...", "testing")
        self._append_log("\nกำลังทดสอบการเชื่อมต่อ ADB...\n")
        threading.Thread(target=self._run_connection_test, args=(command,), daemon=True).start()

    def _run_connection_test(self, command):
        creation_flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"
        worker_log = self._new_worker_log_path() if FROZEN else None
        if worker_log is not None:
            env["COOKIEBOT_LOG_FILE"] = str(worker_log)
        try:
            result = subprocess.run(
                command,
                cwd=APP_DIR,
                stdout=subprocess.DEVNULL if FROZEN else subprocess.PIPE,
                stderr=subprocess.DEVNULL if FROZEN else subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=30,
                creationflags=creation_flags,
                env=env,
            )
            if worker_log is not None:
                try:
                    output = worker_log.read_text(encoding="utf-8", errors="replace")
                except OSError:
                    output = "ไม่พบ Log จากตัวบอท\n"
                finally:
                    try:
                        worker_log.unlink(missing_ok=True)
                    except OSError:
                        pass
            else:
                output = result.stdout
            self.events.put(("connection_result", (result.returncode, output)))
        except subprocess.TimeoutExpired:
            if worker_log is not None:
                try:
                    worker_log.unlink(missing_ok=True)
                except OSError:
                    pass
            self.events.put(("connection_result", (1, "หมดเวลารอการเชื่อมต่อ (30 วินาที)\n")))
        except OSError as exc:
            if worker_log is not None:
                try:
                    worker_log.unlink(missing_ok=True)
                except OSError:
                    pass
            self.events.put(("connection_result", (1, f"เรียกโปรแกรมทดสอบไม่ได้: {exc}\n")))

    def _poll_events(self):
        try:
            while True:
                event, payload = self.events.get_nowait()
                if event == "log":
                    self._append_log(payload)
                    if self.process_mode == "bot":
                        self._update_session_stats(payload)
                    elif self.process_mode == "hearts":
                        heart_match = re.search(r"\[HEARTS\]\s+sent=(\d+)", payload)
                        if heart_match:
                            self._heart_sent_count = int(heart_match.group(1))
                elif event == "bot_exit":
                    process, return_code = payload
                    if process is self.process:
                        finished_mode = self.process_mode
                        elapsed_text = self._finish_bot_session() if finished_mode == "bot" else None
                        self.process = None
                        self.process_mode = None
                        self._set_running_controls(False)
                        if self.stop_requested:
                            status = "หยุดส่งหัวใจแล้ว" if finished_mode == "hearts" else "หยุดแล้ว"
                            self._set_status(status, "idle")
                            duration_note = f" • ใช้เวลา {elapsed_text}" if elapsed_text else ""
                            activity = "หยุดส่งหัวใจแล้ว" if finished_mode == "hearts" else "บอทหยุดทำงานแล้ว"
                            self._append_log(f"──────── {activity}{duration_note} ────────\n")
                        elif return_code == 0:
                            if finished_mode == "hearts" and self._heart_sent_count is not None:
                                status = f"ส่งหัวใจแล้ว {self._heart_sent_count} คน"
                            else:
                                status = "ส่งหัวใจเสร็จแล้ว" if finished_mode == "hearts" else "หยุดแล้ว"
                            self._set_status(status, "success" if finished_mode == "hearts" else "idle")
                            duration_note = f" • ใช้เวลา {elapsed_text}" if elapsed_text else ""
                            activity = "ส่งหัวใจเสร็จแล้ว" if finished_mode == "hearts" else "บอทหยุดทำงานแล้ว"
                            self._append_log(f"──────── {activity}{duration_note} ────────\n")
                        else:
                            status = "ส่งหัวใจไม่สำเร็จ" if finished_mode == "hearts" else "บอทหยุดด้วยข้อผิดพลาด"
                            self._set_status(status, "error")
                            duration_note = f" • ใช้เวลา {elapsed_text}" if elapsed_text else ""
                            self._append_log(
                                f"──────── กระบวนการจบ (รหัส {return_code}){duration_note} ────────\n"
                            )
                        self.stop_requested = False
                elif event == "connection_result":
                    return_code, output = payload
                    self.connection_test_running = False
                    self.test_button.configure(state="normal")
                    self.start_button.configure(state="normal")
                    self.send_hearts_button.configure(state="normal")
                    self._append_log(output)
                    if return_code == 0:
                        self._set_status("เชื่อมต่อสำเร็จ", "success")
                        self._save_settings()
                    else:
                        self._set_status("เชื่อมต่อไม่สำเร็จ", "error")
        except queue.Empty:
            pass
        if self.process_mode == "bot":
            self._update_session_elapsed()
        self.root.after(100, self._poll_events)

    def _set_running_controls(self, running):
        self.start_button.configure(state="disabled" if running else "normal")
        self.send_hearts_button.configure(state="disabled" if running else "normal")
        self.stop_button.configure(state="normal" if running else "disabled")
        self.test_button.configure(state="disabled" if running else "normal")
        state = "disabled" if running else "normal"
        self.ip_entry.configure(state=state)
        self.port_entry.configure(state=state)
        self.max_runs_spinbox.configure(state=state)

    def _update_session_stats(self, line):
        match = re.search(
            r"\[STATS\]\s+attempts=(\d+)\s+completed=(\d+)\s+coins=(\d+)\s+exp=(\d+)",
            line,
        )
        if not match:
            return
        attempts, completed, coins, exp = (int(value) for value in match.groups())
        self._set_session_stats(attempts, completed, coins, exp)

    @staticmethod
    def _format_session_average(total, completed):
        if completed <= 0:
            return "0"
        average = total / completed
        if average.is_integer():
            return f"{int(average):,}"
        return f"{average:,.1f}"

    def _set_session_stats(self, attempts, completed, coins, exp):
        attempts = max(0, int(attempts))
        completed = max(0, int(completed))
        coins = max(0, int(coins))
        exp = max(0, int(exp))
        average_coins = self._format_session_average(coins, completed)
        average_exp = self._format_session_average(exp, completed)

        self.session_stats_var.set(
            f"รอบ {completed}/{attempts} • Coins {coins:,} (เฉลี่ย {average_coins}) "
            f"• EXP {exp:,} (เฉลี่ย {average_exp})"
        )
        self.session_runs_var.set(f"{completed:,} / {attempts:,}")
        self.session_coins_total_var.set(f"{coins:,}")
        self.session_coins_average_var.set(f"เฉลี่ย {average_coins} / รอบ")
        self.session_exp_total_var.set(f"{exp:,}")
        self.session_exp_average_var.set(f"เฉลี่ย {average_exp} / รอบ")

    @staticmethod
    def _format_session_elapsed(seconds):
        total_seconds = max(0, int(seconds))
        hours, remainder = divmod(total_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    def _begin_bot_session(self):
        """Reset per-session rewards and start a fresh elapsed-time clock."""
        self._set_session_stats(0, 0, 0, 0)
        self._session_started_at = time.monotonic()
        self._session_last_elapsed_second = 0
        self.session_elapsed_var.set("00:00:00")
        self.session_elapsed_detail_var.set("กำลังทำงาน")

    def _update_session_elapsed(self, force=False):
        if self._session_started_at is None:
            return self.session_elapsed_var.get()
        elapsed_seconds = max(0, int(time.monotonic() - self._session_started_at))
        if force or elapsed_seconds != self._session_last_elapsed_second:
            self._session_last_elapsed_second = elapsed_seconds
            self.session_elapsed_var.set(self._format_session_elapsed(elapsed_seconds))
        return self.session_elapsed_var.get()

    def _finish_bot_session(self):
        elapsed_text = self._update_session_elapsed(force=True)
        self._session_started_at = None
        self._session_last_elapsed_second = None
        self.session_elapsed_detail_var.set("เวลารวมหลังหยุด")
        return elapsed_text

    def _set_status(self, text, state):
        colors = {
            "idle": ("#eeebf6", "#4a455b"),
            "running": ("#dcfce7", "#187444"),
            "success": ("#dcfce7", "#187444"),
            "testing": ("#fff2cf", "#9a6417"),
            "error": ("#ffe2e8", "#b12f4b"),
        }
        bg, fg = colors.get(state, colors["idle"])
        self.status_var.set(text)
        self.status_label.configure(bg=bg, fg=fg)

    def _toggle_boost(self):
        self.boost_combo.configure(state="readonly" if self.use_boost_var.get() else "disabled")

    def _append_log(self, text):
        self.log.configure(state="normal")
        self.log.insert("end", text)
        self.log.see("end")
        self.log.configure(state="disabled")

    def _clear_log(self):
        self.log.configure(state="normal")
        self.log.delete("1.0", "end")
        self.log.configure(state="disabled")

    def _load_settings(self):
        if not SETTINGS_FILE.exists():
            return
        try:
            settings = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
            self.ip_var.set(str(settings.get("device_ip", DEVICE_IP)))
            self.port_var.set(str(settings.get("device_port", DEVICE_PORT)))
            self.fast_start_var.set(bool(settings.get("fast_start", False)))
            self.cookie_relay_var.set(bool(settings.get("cookie_relay", False)))
            self.use_boost_var.set(bool(settings.get("use_boost", False)))
            self.claim_relic_rewards_var.set(
                bool(settings.get("claim_relic_rewards", True))
            )
            self.max_runs_var.set(str(settings.get("max_runs", 0)))
            boost_index = int(settings.get("boost_index", 0))
            self.boost_combo.current(max(0, min(boost_index, len(BOOST_CHOICES) - 1)))
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            self._append_log(f"อ่านค่าที่บันทึกไว้ไม่ได้: {exc}\n")

    def _save_settings(self):
        settings = {
            "device_ip": self.ip_var.get().strip(),
            "device_port": self.port_var.get().strip(),
            "fast_start": self.fast_start_var.get(),
            "cookie_relay": self.cookie_relay_var.get(),
            "use_boost": self.use_boost_var.get(),
            "claim_relic_rewards": self.claim_relic_rewards_var.get(),
            "boost_index": max(0, self.boost_combo.current()),
            "max_runs": self.max_runs_var.get().strip() or "0",
        }
        try:
            SETTINGS_FILE.write_text(
                json.dumps(settings, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except OSError as exc:
            self._append_log(f"บันทึกค่าไม่ได้: {exc}\n")

    def _on_close(self):
        running = self.process is not None and self.process.poll() is None
        running_activity = "การส่งหัวใจ" if self.process_mode == "hearts" else "บอท"
        if running and not messagebox.askyesno(
            "ปิดโปรแกรม",
            f"{running_activity}ยังทำงานอยู่ ต้องการหยุดและปิดโปรแกรมหรือไม่?",
            parent=self.root,
        ):
            return
        self._save_settings()
        if running:
            try:
                self.process.terminate()
            except OSError:
                pass
        self.root.destroy()


def launch_gui():
    root = tk.Tk()
    CookieRunBotGUI(root)
    root.mainloop()


if __name__ == "__main__":
    launch_gui()
