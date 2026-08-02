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
from tkinter import messagebox, scrolledtext, simpledialog, ttk

from bot import BOOST_CHOICES
from config import DEVICE_IP, DEVICE_PORT
from macro import PROFILE_DIR, list_profiles, profile_summary, update_profile_metadata
from runtime_paths import APP_DIR, FROZEN, RESOURCE_DIR


BASE_DIR = RESOURCE_DIR
SETTINGS_FILE = APP_DIR / "gui_settings.json"


class CookieRunBotGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("CookieRun Classic Bot")
        self.root.geometry("1160x800")
        self.root.minsize(980, 760)
        self.root.configure(bg="#f4f6fb")
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

        self.process = None
        self.process_mode = None
        self.record_target = None
        self.stop_requested = False
        self.events = queue.Queue()
        self.connection_test_running = False
        self._last_profile_refresh = 0.0

        self.ip_var = tk.StringVar(value=DEVICE_IP)
        self.port_var = tk.StringVar(value=str(DEVICE_PORT))
        self.fast_start_var = tk.BooleanVar(value=False)
        self.cookie_relay_var = tk.BooleanVar(value=False)
        self.use_boost_var = tk.BooleanVar(value=False)
        self.replay_count_var = tk.StringVar(value="0")
        self.status_var = tk.StringVar(value="พร้อมใช้งาน")
        self.profile_count_var = tk.StringVar(value="ยังไม่มีโปรไฟล์")
        self.session_stats_var = tk.StringVar(
            value="รอบ 0/0 • Coins 0 (เฉลี่ย 0) • EXP 0 (เฉลี่ย 0)"
        )
        self.session_runs_var = tk.StringVar(value="0 / 0")
        self.session_coins_total_var = tk.StringVar(value="0")
        self.session_coins_average_var = tk.StringVar(value="เฉลี่ย 0 / รอบ")
        self.session_exp_total_var = tk.StringVar(value="0")
        self.session_exp_average_var = tk.StringVar(value="เฉลี่ย 0 / รอบ")

        self._create_app_icon()
        self._configure_styles()
        self._build_ui()
        self._load_settings()
        self._toggle_boost()
        self._refresh_profiles()
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
            "Record.TButton",
            background="#ff5f87",
            foreground="#ffffff",
            bordercolor="#ff5f87",
            lightcolor="#ff5f87",
            darkcolor="#ff5f87",
            borderwidth=0,
            padding=(15, 10),
        )
        style.map(
            "Record.TButton",
            background=[("active", "#ff7699"), ("pressed", "#e84d73"), ("disabled", "#d8aab6")],
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
        style.configure(
            "Profiles.Treeview",
            background="#ffffff",
            fieldbackground="#ffffff",
            foreground="#34384c",
            bordercolor="#edf0f5",
            borderwidth=0,
            relief="flat",
            font=("Segoe UI", 10),
            rowheight=34,
        )
        style.map(
            "Profiles.Treeview",
            background=[("selected", "#eeeaff")],
            foreground=[("selected", "#5643c1")],
        )
        style.configure(
            "Profiles.Treeview.Heading",
            background="#f7f8fc",
            foreground="#747a90",
            bordercolor="#edf0f5",
            font=("Segoe UI Semibold", 9),
            padding=(9, 8),
        )
        style.map("Profiles.Treeview.Heading", background=[("active", "#f0edff")])

    def _build_ui(self):
        shell = tk.Frame(self.root, bg="#f4f6fb")
        shell.pack(fill="both", expand=True)

        sidebar = tk.Frame(shell, bg="#171a2e", width=226)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        brand = tk.Frame(sidebar, bg="#171a2e")
        brand.pack(fill="x", padx=20, pady=(22, 26))
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
            text="CLASSIC  •  v2",
            bg="#171a2e",
            fg="#797e9b",
            font=("Segoe UI Semibold", 8),
        ).pack(anchor="w", pady=(1, 0))

        tk.Label(
            sidebar,
            text="QUICK START",
            bg="#171a2e",
            fg="#696e8b",
            font=("Segoe UI Semibold", 8),
        ).pack(anchor="w", padx=22, pady=(0, 9))
        for number, icon, title, note in (
            ("01", "⌁", "เชื่อมต่อ ADB", "ตรวจหา Emulator"),
            ("02", "●", "อัดการเล่น", "สร้างโปรไฟล์"),
            ("03", "▶", "เริ่มบอท", "สุ่มเล่นอัตโนมัติ"),
        ):
            step = tk.Frame(sidebar, bg="#171a2e")
            step.pack(fill="x", padx=18, pady=3)
            tk.Label(
                step,
                text=icon,
                bg="#252941",
                fg="#9c8fff",
                width=3,
                height=1,
                font=("Segoe UI Symbol", 12),
            ).pack(side="left", ipady=5)
            copy = tk.Frame(step, bg="#171a2e")
            copy.pack(side="left", padx=(10, 0))
            tk.Label(copy, text=title, bg="#171a2e", fg="#e7e8f1", font=("Segoe UI Semibold", 9)).pack(anchor="w")
            tk.Label(copy, text=note, bg="#171a2e", fg="#747993", font=("Segoe UI", 8)).pack(anchor="w")
            tk.Label(step, text=number, bg="#171a2e", fg="#4d526e", font=("Segoe UI Semibold", 8)).pack(side="right")

        run_panel = tk.Frame(sidebar, bg="#20233b", padx=13, pady=14)
        run_panel.pack(fill="x", padx=16, pady=(24, 10))
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
        repeat_row = tk.Frame(run_panel, bg="#20233b")
        repeat_row.pack(fill="x")
        tk.Label(
            repeat_row,
            text="จำนวนรอบ",
            bg="#20233b",
            fg="#b7bbcc",
            font=("Segoe UI", 9),
        ).pack(side="left")
        self.replay_count_spinbox = ttk.Spinbox(
            repeat_row,
            from_=0,
            to=999,
            width=5,
            textvariable=self.replay_count_var,
            justify="center",
        )
        self.replay_count_spinbox.pack(side="right")
        tk.Label(
            run_panel,
            text="0 = เล่นต่อเนื่องไม่จำกัด",
            bg="#20233b",
            fg="#6f748e",
            font=("Segoe UI", 8),
        ).pack(anchor="w", pady=(7, 0))

        tk.Label(
            sidebar,
            text="W  กระโดด     S  สไลด์",
            bg="#171a2e",
            fg="#686d88",
            font=("Segoe UI Semibold", 8),
        ).pack(side="bottom", pady=18)

        workspace = tk.Frame(shell, bg="#f4f6fb")
        workspace.pack(side="left", fill="both", expand=True)

        topbar = tk.Frame(workspace, bg="#ffffff", height=74)
        topbar.pack(fill="x")
        topbar.pack_propagate(False)
        title_block = tk.Frame(topbar, bg="#ffffff")
        title_block.pack(side="left", padx=22, pady=13)
        tk.Label(
            title_block,
            text="Automation Studio",
            bg="#ffffff",
            fg="#1f2233",
            font=("Segoe UI Semibold", 17),
        ).pack(anchor="w")
        tk.Label(
            title_block,
            text="จัดการการเชื่อมต่อ โปรไฟล์ และการเล่นอัตโนมัติในหน้าจอเดียว",
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
        self.status_label.pack(side="right", padx=22)

        body = tk.Frame(workspace, bg="#f4f6fb", padx=18, pady=14)
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

        recordings = make_card(2)
        profile_header = add_header(recordings, "▣", "โปรไฟล์การเล่น", "บอทจะสุ่มหนึ่งโปรไฟล์ในแต่ละรอบ")
        ttk.Label(profile_header, textvariable=self.session_stats_var, style="Muted.TLabel").pack(side="right")
        ttk.Label(profile_header, textvariable=self.profile_count_var, style="Count.TLabel").pack(side="right", padx=(0, 10))
        profile_content = tk.Frame(recordings, bg="#ffffff")
        profile_content.pack(fill="both", expand=True, padx=15, pady=(0, 8))
        profile_content.columnconfigure(0, weight=1)
        profile_content.rowconfigure(0, weight=1)
        profile_table = ttk.Frame(profile_content, style="Card.TFrame")
        profile_table.grid(row=0, column=0, rowspan=3, sticky="nsew", padx=(0, 12))
        profile_table.columnconfigure(0, weight=1)
        profile_table.rowconfigure(0, weight=1)
        self.profile_list = ttk.Treeview(
            profile_table,
            columns=("name", "duration", "actions", "coins", "exp"),
            show="headings",
            height=3,
            selectmode="browse",
            style="Profiles.Treeview",
        )
        self.profile_list.heading("name", text="ชื่อโปรไฟล์", anchor="w")
        self.profile_list.heading("duration", text="เวลา", anchor="center")
        self.profile_list.heading("actions", text="แอ็กชัน", anchor="center")
        self.profile_list.heading("coins", text="Coins / รอบ", anchor="e")
        self.profile_list.heading("exp", text="EXP / รอบ", anchor="e")
        self.profile_list.column("name", width=240, minwidth=150, stretch=True, anchor="w")
        self.profile_list.column("duration", width=75, minwidth=65, stretch=False, anchor="center")
        self.profile_list.column("actions", width=75, minwidth=65, stretch=False, anchor="center")
        self.profile_list.column("coins", width=95, minwidth=80, stretch=False, anchor="e")
        self.profile_list.column("exp", width=85, minwidth=75, stretch=False, anchor="e")
        profile_scrollbar = ttk.Scrollbar(profile_table, orient="vertical", command=self.profile_list.yview)
        self.profile_list.configure(yscrollcommand=profile_scrollbar.set)
        self.profile_list.grid(row=0, column=0, sticky="nsew")
        profile_scrollbar.grid(row=0, column=1, sticky="ns")
        self.profile_list.bind("<Double-1>", lambda _event: self._edit_selected_profile())
        self.record_button = ttk.Button(
            profile_content,
            text="●  อัดรอบใหม่",
            style="Record.TButton",
            command=self._record_run,
        )
        self.record_button.grid(row=0, column=1, sticky="new")
        self.edit_profile_button = ttk.Button(
            profile_content,
            text="✎  แก้รายละเอียด",
            command=self._edit_selected_profile,
        )
        self.edit_profile_button.grid(row=1, column=1, sticky="new", pady=(6, 0))
        self.delete_profile_button = ttk.Button(
            profile_content,
            text="×  ลบโปรไฟล์",
            command=self._delete_selected_profile,
        )
        self.delete_profile_button.grid(row=2, column=1, sticky="new", pady=(6, 0))
        tk.Label(
            recordings,
            text="ดับเบิลคลิกที่โปรไฟล์เพื่อแก้ไข  •  แนะนำให้มี 2–3 โปรไฟล์เพื่อความหลากหลาย",
            bg="#ffffff",
            fg="#979bad",
            font=("Segoe UI", 8),
        ).pack(anchor="w", padx=15, pady=(0, 9))

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
        self._append_log("READY  •  เช็ก ADB แล้วอัดโปรไฟล์แรกได้เลย\n")

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
            max_runs = int(self.replay_count_var.get().strip() or "0")
            if max_runs < 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("จำนวนรอบไม่ถูกต้อง", "จำนวนรอบต้องเป็นเลข 0 ขึ้นไป", parent=self.root)
            return
        command.extend(["--max-runs", str(max_runs)])
        profiles = list_profiles()
        if not profiles and not messagebox.askyesno(
            "ยังไม่มีโปรไฟล์",
            "ยังไม่ได้อัดการเล่น บอทจะจัดการเฉพาะเมนูและรางวัล ต้องการเริ่มต่อหรือไม่?",
            parent=self.root,
        ):
            return
        for profile in profiles:
            command.extend(["--replay-profile", str(profile)])
        self._launch_process(command, "bot")

    def _record_run(self):
        if self.process is not None and self.process.poll() is None:
            return
        try:
            command = self._base_command("--run-bot")
        except ValueError as exc:
            messagebox.showerror("ข้อมูลไม่ถูกต้อง", str(exc), parent=self.root)
            return
        profile_name = simpledialog.askstring(
            "ตั้งชื่อโปรไฟล์",
            "ชื่อโปรไฟล์การเล่น:",
            initialvalue=f"Run {len(list_profiles()) + 1}",
            parent=self.root,
        )
        if profile_name is None:
            return
        profile_name = profile_name.strip() or f"Run {len(list_profiles()) + 1}"
        PROFILE_DIR.mkdir(exist_ok=True)
        safe_name = re.sub(r"[^\w\- ]+", "_", profile_name, flags=re.UNICODE).strip() or "run"
        profile_path = PROFILE_DIR / f"{time.strftime('%Y%m%d_%H%M%S')}_{safe_name}.json"
        self.record_target = profile_path
        self._append_play_options(command)
        command.extend(["--record-profile", str(profile_path), "--profile-name", profile_name])
        self._append_log(
            "\nเริ่มโหมดอัด: รอให้บอทซื้อของและเข้า GAME_START "
            "จากนั้นเล่นเองจนจบรอบ\n"
        )
        self._launch_process(command, "record")

    def _append_play_options(self, command):
        if self.fast_start_var.get():
            command.append("--fast-start")
        if self.cookie_relay_var.get():
            command.append("--cookie-relay")
        if self.use_boost_var.get():
            command.extend(["--boost-index", str(self.boost_combo.current() + 1)])

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
            self._append_log(f"เริ่มบอทไม่สำเร็จ: {exc}\n")
            self._set_status("เริ่มไม่สำเร็จ", "error")
            return

        self._append_log("\n──────── เริ่มการทำงาน ────────\n")
        self.process_mode = mode
        if mode == "bot":
            self._set_session_stats(0, 0, 0, 0)
        self.stop_requested = False
        self._set_running_controls(True)
        self._set_status("กำลังอัดการเล่น" if mode == "record" else "บอทกำลังทำงาน", "running")
        if worker_log is not None:
            reader = self._read_bot_log
            reader_args = (self.process, worker_log)
        else:
            reader = self._read_bot_output
            reader_args = (self.process,)
        threading.Thread(target=reader, args=reader_args, daemon=True).start()

    def _refresh_profiles(self):
        selected_path = self._selected_profile_path()
        self.profiles = list_profiles()
        profile_count = len(self.profiles)
        self.profile_count_var.set(
            "ยังไม่มีโปรไฟล์" if profile_count == 0 else f"{profile_count} โปรไฟล์พร้อมสุ่ม"
        )
        self.profile_list.delete(*self.profile_list.get_children())
        self.profile_items = {}
        for index, path in enumerate(self.profiles, 1):
            item_id = f"profile-{index}"
            try:
                summary = profile_summary(path)
                duration = int(round(summary["duration_seconds"]))
                minutes, seconds = divmod(duration, 60)
                values = (
                    f"{index}.  {summary['name']}",
                    f"{minutes:02d}:{seconds:02d}",
                    f"{summary['action_count']:,}",
                    f"{summary['coins']:,}",
                    f"{summary['exp']:,}",
                )
            except (OSError, ValueError, json.JSONDecodeError):
                values = (f"{index}.  {path.name}", "—", "—", "—", "—")
            self.profile_items[item_id] = path
            self.profile_list.insert("", "end", iid=item_id, values=values)
            if selected_path == path:
                self.profile_list.selection_set(item_id)
                self.profile_list.focus(item_id)

    def _selected_profile_path(self):
        selection = self.profile_list.selection()
        if not selection:
            return None
        return getattr(self, "profile_items", {}).get(selection[0])

    def _edit_selected_profile(self):
        path = self._selected_profile_path()
        if path is None:
            messagebox.showinfo("เลือกโปรไฟล์", "กรุณาเลือกโปรไฟล์ที่ต้องการแก้ไข", parent=self.root)
            return
        try:
            summary = profile_summary(path)
            name = simpledialog.askstring(
                "ชื่อโปรไฟล์",
                "ตั้งชื่อโปรไฟล์:",
                initialvalue=summary["name"],
                parent=self.root,
            )
            if name is None:
                return
            coins = simpledialog.askinteger(
                "Coins ต่อรอบ",
                "จำนวน Coins ที่ได้เมื่อเล่นโปรไฟล์นี้จบหนึ่งรอบ:",
                initialvalue=summary["coins"],
                minvalue=0,
                parent=self.root,
            )
            if coins is None:
                return
            exp = simpledialog.askinteger(
                "EXP ต่อรอบ",
                "จำนวน EXP ที่ได้เมื่อเล่นโปรไฟล์นี้จบหนึ่งรอบ:",
                initialvalue=summary["exp"],
                minvalue=0,
                parent=self.root,
            )
            if exp is None:
                return
            update_profile_metadata(path, name, coins, exp)
            self._refresh_profiles()
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            messagebox.showerror("บันทึกรายละเอียดไม่สำเร็จ", str(exc), parent=self.root)

    def _delete_selected_profile(self):
        path = self._selected_profile_path()
        if path is None:
            messagebox.showinfo("เลือกโปรไฟล์", "กรุณาเลือกโปรไฟล์ที่ต้องการลบ", parent=self.root)
            return
        if not messagebox.askyesno(
            "ลบโปรไฟล์",
            f"ต้องการลบ {path.name} หรือไม่?",
            parent=self.root,
        ):
            return
        try:
            path.unlink()
            self._refresh_profiles()
        except OSError as exc:
            messagebox.showerror("ลบไม่สำเร็จ", str(exc), parent=self.root)

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
        self._append_log("กำลังส่งคำสั่งหยุดบอท...\n")
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
        self.record_button.configure(state="disabled")
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
                    self._update_session_stats(payload)
                    if "[PROFILE_REWARDS_UPDATED]" in payload:
                        self._refresh_profiles()
                elif event == "bot_exit":
                    process, return_code = payload
                    if process is self.process:
                        finished_mode = self.process_mode
                        self.process = None
                        self.process_mode = None
                        self._set_running_controls(False)
                        self._refresh_profiles()
                        if self.stop_requested or return_code == 0:
                            if finished_mode == "record" and not self.stop_requested:
                                if self.record_target is not None and self.record_target.exists():
                                    self._set_status("บันทึกโปรไฟล์แล้ว", "success")
                                    self._append_log("──────── บันทึกการเล่นเสร็จแล้ว ────────\n")
                                else:
                                    self._set_status("ไม่พบจังหวะการเล่น", "error")
                                    self._append_log("ไม่พบ touch event จึงไม่ได้สร้างโปรไฟล์\n")
                            else:
                                self._set_status("หยุดแล้ว", "idle")
                                self._append_log("──────── บอทหยุดทำงานแล้ว ────────\n")
                        else:
                            self._set_status("บอทหยุดด้วยข้อผิดพลาด", "error")
                            self._append_log(f"──────── กระบวนการจบ (รหัส {return_code}) ────────\n")
                        self.stop_requested = False
                        self.record_target = None
                elif event == "connection_result":
                    return_code, output = payload
                    self.connection_test_running = False
                    self.test_button.configure(state="normal")
                    self.start_button.configure(state="normal")
                    self.record_button.configure(state="normal")
                    self._append_log(output)
                    if return_code == 0:
                        self._set_status("เชื่อมต่อสำเร็จ", "success")
                        self._save_settings()
                    else:
                        self._set_status("เชื่อมต่อไม่สำเร็จ", "error")
        except queue.Empty:
            pass
        if self.process_mode == "record" and time.monotonic() - self._last_profile_refresh >= 1.0:
            self._refresh_profiles()
            self._last_profile_refresh = time.monotonic()
        self.root.after(100, self._poll_events)

    def _set_running_controls(self, running):
        self.start_button.configure(state="disabled" if running else "normal")
        self.stop_button.configure(state="normal" if running else "disabled")
        self.test_button.configure(state="disabled" if running else "normal")
        self.record_button.configure(state="disabled" if running else "normal")
        self.edit_profile_button.configure(state="disabled" if running else "normal")
        self.delete_profile_button.configure(state="disabled" if running else "normal")
        state = "disabled" if running else "normal"
        self.ip_entry.configure(state=state)
        self.port_entry.configure(state=state)
        self.replay_count_spinbox.configure(state=state)

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
            self.replay_count_var.set(str(settings.get("replay_count", 0)))
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
            "boost_index": max(0, self.boost_combo.current()),
            "replay_count": self.replay_count_var.get().strip() or "0",
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
        if running and not messagebox.askyesno(
            "ปิดโปรแกรม",
            "บอทยังทำงานอยู่ ต้องการหยุดบอทและปิดโปรแกรมหรือไม่?",
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
