from functools import partial
from datetime import datetime

import customtkinter as ctk
from PIL import Image, ImageDraw, ImageTk

from bot import BOOST_CHOICES
from gui import CookieRunBotGUI
from macro import list_profiles, profile_summary


BG = "#F4F5FA"
CARD = "#FFFFFF"
SIDEBAR = "#15172A"
SIDEBAR_CARD = "#20233A"
TEXT = "#242638"
MUTED = "#858A9E"
PURPLE = "#6C5CE7"
PURPLE_HOVER = "#7A6BED"
PURPLE_SOFT = "#F0EDFF"
PINK = "#FF5C86"
PINK_HOVER = "#ED4A75"
BORDER = "#E9EAF1"


class BoostOptionMenu(ctk.CTkOptionMenu):
    """CTk option menu with the ttk Combobox current() API used by the bot GUI."""

    def __init__(self, *args, values=None, **kwargs):
        self._boost_values = list(values or [])
        super().__init__(*args, values=self._boost_values, **kwargs)

    def current(self, index=None):
        if index is None:
            try:
                return self._boost_values.index(self.get())
            except ValueError:
                return 0
        if self._boost_values:
            safe_index = max(0, min(int(index), len(self._boost_values) - 1))
            self.set(self._boost_values[safe_index])


class ModernCookieRunBotGUI(CookieRunBotGUI):
    def _configure_styles(self):
        ctk.set_appearance_mode("Light")
        ctk.set_default_color_theme("blue")
        self.root.geometry("1380x900")
        self.root.minsize(1180, 820)
        self.root.configure(fg_color=BG)

    @staticmethod
    def _draw_icon(name, color, size=64, background=None):
        image = Image.new("RGBA", (size, size), background or (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        scale = size / 64
        width = max(3, int(5 * scale))

        def p(value):
            return int(value * scale)

        if name == "cookie":
            draw.ellipse((p(9), p(9), p(55), p(55)), fill="#F7B94C", outline="#E59A34", width=width)
            for x, y, radius in ((23, 22, 4), (40, 18, 3), (34, 38, 4), (20, 43, 3), (47, 34, 3)):
                draw.ellipse((p(x - radius), p(y - radius), p(x + radius), p(y + radius)), fill="#754334")
        elif name == "play":
            draw.polygon(((p(21), p(13)), (p(52), p(32)), (p(21), p(51))), fill=color)
        elif name == "stop":
            draw.rounded_rectangle((p(17), p(17), p(47), p(47)), radius=p(5), fill=color)
        elif name == "record":
            draw.ellipse((p(14), p(14), p(50), p(50)), fill=color)
            draw.ellipse((p(23), p(23), p(41), p(41)), fill="#FFFFFF")
        elif name == "refresh":
            draw.arc((p(12), p(12), p(52), p(52)), 35, 300, fill=color, width=width)
            draw.polygon(((p(46), p(9)), (p(55), p(22)), (p(40), p(23))), fill=color)
        elif name == "edit":
            draw.line((p(16), p(47), p(45), p(18)), fill=color, width=p(8))
            draw.polygon(((p(12), p(52)), (p(18), p(38)), (p(27), p(47))), fill=color)
            draw.line((p(40), p(14), p(49), p(23)), fill=color, width=p(8))
        elif name == "trash":
            draw.rounded_rectangle((p(18), p(20), p(46), p(52)), radius=p(4), outline=color, width=width)
            draw.line((p(14), p(16), p(50), p(16)), fill=color, width=width)
            draw.line((p(25), p(10), p(39), p(10)), fill=color, width=width)
        elif name == "plug":
            draw.line((p(20), p(12), p(20), p(24)), fill=color, width=width)
            draw.line((p(44), p(12), p(44), p(24)), fill=color, width=width)
            draw.rounded_rectangle((p(14), p(21), p(50), p(39)), radius=p(6), outline=color, width=width)
            draw.line((p(32), p(39), p(32), p(54)), fill=color, width=width)
        elif name == "sparkle":
            draw.polygon(((p(32), p(7)), (p(38), p(25)), (p(56), p(32)), (p(38), p(39)),
                          (p(32), p(57)), (p(26), p(39)), (p(8), p(32)), (p(26), p(25))), fill=color)
        elif name == "profiles":
            draw.rounded_rectangle((p(10), p(15), p(47), p(48)), radius=p(5), outline=color, width=width)
            draw.rounded_rectangle((p(19), p(8), p(54), p(41)), radius=p(5), outline=color, width=width)
            draw.line((p(18), p(27), p(39), p(27)), fill=color, width=width)
            draw.line((p(18), p(37), p(34), p(37)), fill=color, width=width)
        elif name == "activity":
            draw.rounded_rectangle((p(10), p(10), p(54), p(54)), radius=p(8), outline=color, width=width)
            draw.line((p(17), p(25), p(47), p(25)), fill=color, width=width)
            draw.line((p(17), p(34), p(41), p(34)), fill=color, width=width)
            draw.line((p(17), p(43), p(45), p(43)), fill=color, width=width)
        elif name == "check":
            draw.line((p(13), p(34), p(26), p(47), p(52), p(17)), fill=color, width=p(7), joint="curve")
        elif name == "clock":
            draw.ellipse((p(10), p(10), p(54), p(54)), outline=color, width=width)
            draw.line((p(32), p(19), p(32), p(34), p(43), p(40)), fill=color, width=width)
        elif name == "coin":
            draw.ellipse((p(9), p(9), p(55), p(55)), fill="#FFF0B8", outline=color, width=width)
            draw.ellipse((p(18), p(18), p(46), p(46)), outline=color, width=max(2, width - 1))
        elif name == "xp":
            draw.polygon(
                ((p(32), p(7)), (p(39), p(23)), (p(57), p(25)), (p(43), p(37)),
                 (p(47), p(55)), (p(32), p(46)), (p(17), p(55)), (p(21), p(37)),
                 (p(7), p(25)), (p(25), p(23))),
                fill=color,
            )
        elif name == "tap":
            draw.ellipse((p(23), p(9), p(41), p(27)), outline=color, width=width)
            draw.line((p(32), p(18), p(32), p(48)), fill=color, width=p(7))
            draw.line((p(32), p(34), p(47), p(43)), fill=color, width=p(7))
        elif name == "calendar":
            draw.rounded_rectangle((p(10), p(14), p(54), p(54)), radius=p(7), outline=color, width=width)
            draw.line((p(10), p(27), p(54), p(27)), fill=color, width=width)
            draw.line((p(21), p(8), p(21), p(20)), fill=color, width=width)
            draw.line((p(43), p(8), p(43), p(20)), fill=color, width=width)
        return image

    def _create_app_icon(self):
        self.icons = {}
        icon_specs = {
            "cookie": ("cookie", "#FFFFFF", 30),
            "play": ("play", "#FFFFFF", 18),
            "stop": ("stop", "#FF8BA6", 16),
            "record": ("record", "#FFFFFF", 17),
            "refresh": ("refresh", "#5D6277", 16),
            "edit": ("edit", "#6252CC", 16),
            "trash": ("trash", "#D84D6E", 16),
            "plug": ("plug", PURPLE, 18),
            "sparkle": ("sparkle", "#F2A93B", 18),
            "profiles": ("profiles", PINK, 18),
            "activity": ("activity", "#4EA4C8", 18),
            "check": ("check", "#FFFFFF", 14),
            "clock": ("clock", "#6C5CE7", 16),
            "coin": ("coin", "#E3A11D", 16),
            "xp": ("xp", "#F15F86", 16),
            "tap": ("tap", "#2E9F78", 16),
            "calendar": ("calendar", "#7B8197", 15),
        }
        for key, (shape, color, display_size) in icon_specs.items():
            source = self._draw_icon(shape, color)
            self.icons[key] = ctk.CTkImage(light_image=source, dark_image=source, size=(display_size, display_size))

        app_source = Image.new("RGBA", (64, 64), PURPLE)
        cookie = self._draw_icon("cookie", "#FFFFFF", 64)
        app_source.alpha_composite(cookie)
        self.app_icon = ImageTk.PhotoImage(app_source.resize((32, 32), Image.Resampling.LANCZOS))
        self.root.iconphoto(True, self.app_icon)

    @staticmethod
    def _font(size, weight="normal"):
        # CustomTkinter font sizes are pixels. Keep body text at least 12 px so
        # Thai glyphs stay comfortable to read on high-resolution displays.
        readable_size = max(14, round(size * 1.3))
        return ctk.CTkFont(family="Segoe UI", size=readable_size, weight=weight)

    def _section_header(self, parent, icon_key, title, subtitle):
        header = ctk.CTkFrame(parent, fg_color="transparent", height=46)
        header.pack(fill="x", padx=16, pady=(13, 8))
        icon_box = ctk.CTkFrame(header, width=38, height=38, corner_radius=11, fg_color=PURPLE_SOFT)
        icon_box.pack(side="left")
        icon_box.pack_propagate(False)
        ctk.CTkLabel(icon_box, text="", image=self.icons[icon_key]).place(relx=0.5, rely=0.5, anchor="center")
        copy = ctk.CTkFrame(header, fg_color="transparent")
        copy.pack(side="left", padx=(10, 0))
        ctk.CTkLabel(copy, text=title, text_color=TEXT, font=self._font(14, "bold"), anchor="w").pack(anchor="w")
        ctk.CTkLabel(copy, text=subtitle, text_color=MUTED, font=self._font(10), anchor="w").pack(anchor="w")
        return header

    def _card(self, parent, row, pady=(0, 10)):
        card = ctk.CTkFrame(
            parent,
            corner_radius=16,
            fg_color=CARD,
            border_width=1,
            border_color=BORDER,
        )
        card.grid(row=row, column=0, sticky="nsew", pady=pady)
        return card

    def _build_ui(self):
        self.root.grid_columnconfigure(1, weight=1)
        self.root.grid_rowconfigure(0, weight=1)

        sidebar = ctk.CTkFrame(self.root, width=238, corner_radius=0, fg_color=SIDEBAR)
        sidebar.grid(row=0, column=0, sticky="nsew")
        sidebar.grid_propagate(False)
        sidebar.grid_rowconfigure(6, weight=1)

        brand = ctk.CTkFrame(sidebar, fg_color="transparent")
        brand.grid(row=0, column=0, sticky="ew", padx=20, pady=(22, 28))
        cookie_box = ctk.CTkFrame(brand, width=50, height=50, corner_radius=16, fg_color=PURPLE)
        cookie_box.pack(side="left")
        cookie_box.pack_propagate(False)
        ctk.CTkLabel(cookie_box, text="", image=self.icons["cookie"]).place(relx=0.5, rely=0.5, anchor="center")
        brand_copy = ctk.CTkFrame(brand, fg_color="transparent")
        brand_copy.pack(side="left", padx=(12, 0))
        ctk.CTkLabel(brand_copy, text="COOKIEBOT", text_color="#FFFFFF", font=self._font(16, "bold")).pack(anchor="w")
        ctk.CTkLabel(brand_copy, text="CLASSIC AUTOMATION", text_color="#747992", font=self._font(9, "bold")).pack(anchor="w")

        ctk.CTkLabel(sidebar, text="QUICK START", text_color="#666B84", font=self._font(10, "bold"), anchor="w").grid(
            row=1, column=0, sticky="ew", padx=22, pady=(0, 8)
        )
        steps = ctk.CTkFrame(sidebar, fg_color="transparent")
        steps.grid(row=2, column=0, sticky="ew", padx=15)
        for index, (number, title, note) in enumerate((
            ("01", "เชื่อมต่อ ADB", "ตรวจหา Emulator"),
            ("02", "อัดการเล่น", "สร้างโปรไฟล์ใหม่"),
            ("03", "เริ่มบอท", "เล่นซ้ำอัตโนมัติ"),
        )):
            step = ctk.CTkFrame(steps, height=53, corner_radius=12, fg_color="#1C1F35")
            step.pack(fill="x", pady=4)
            step.pack_propagate(False)
            ctk.CTkLabel(
                step,
                text=number,
                width=34,
                height=30,
                corner_radius=9,
                fg_color="#292D49",
                text_color="#9B90EF",
                font=self._font(10, "bold"),
            ).pack(side="left", padx=(10, 9))
            copy = ctk.CTkFrame(step, fg_color="transparent")
            copy.pack(side="left")
            ctk.CTkLabel(copy, text=title, text_color="#EEF0F8", font=self._font(11, "bold"), anchor="w").pack(anchor="w")
            ctk.CTkLabel(copy, text=note, text_color="#777C95", font=self._font(9), anchor="w").pack(anchor="w")

        run_panel = ctk.CTkFrame(sidebar, corner_radius=16, fg_color=SIDEBAR_CARD)
        run_panel.grid(row=3, column=0, sticky="ew", padx=15, pady=(24, 0))
        ctk.CTkLabel(run_panel, text="RUN CONTROL", text_color="#858AA2", font=self._font(10, "bold"), anchor="w").pack(
            fill="x", padx=14, pady=(14, 9)
        )
        self.start_button = ctk.CTkButton(
            run_panel,
            height=45,
            corner_radius=12,
            text="START BOT",
            image=self.icons["play"],
            fg_color=PURPLE,
            hover_color=PURPLE_HOVER,
            font=self._font(12, "bold"),
            command=self._start_bot,
        )
        self.start_button.pack(fill="x", padx=12)
        self.stop_button = ctk.CTkButton(
            run_panel,
            height=39,
            corner_radius=11,
            text="STOP",
            image=self.icons["stop"],
            fg_color="#292C47",
            hover_color="#343852",
            text_color="#FF91A9",
            font=self._font(11, "bold"),
            command=self._stop_bot,
            state="disabled",
        )
        self.stop_button.pack(fill="x", padx=12, pady=(7, 12))
        repeat = ctk.CTkFrame(run_panel, fg_color="transparent")
        repeat.pack(fill="x", padx=13)
        ctk.CTkLabel(repeat, text="จำนวนรอบ", text_color="#C1C4D3", font=self._font(10)).pack(side="left")
        self.replay_count_spinbox = ctk.CTkEntry(
            repeat,
            width=62,
            height=34,
            corner_radius=10,
            border_width=1,
            border_color="#3B3F5C",
            fg_color="#292C47",
            text_color="#FFFFFF",
            justify="center",
            textvariable=self.replay_count_var,
        )
        self.replay_count_spinbox.pack(side="right")
        ctk.CTkLabel(run_panel, text="0 = เล่นไม่จำกัด", text_color="#737891", font=self._font(9), anchor="w").pack(
            fill="x", padx=14, pady=(7, 14)
        )

        shortcut = ctk.CTkFrame(sidebar, corner_radius=12, fg_color="#1B1E33")
        shortcut.grid(row=5, column=0, sticky="sew", padx=15, pady=(12, 17))
        ctk.CTkLabel(shortcut, text="W", width=30, height=28, corner_radius=8, fg_color="#2A2D48", text_color="#FFFFFF", font=self._font(10, "bold")).pack(side="left", padx=(10, 6), pady=10)
        ctk.CTkLabel(shortcut, text="กระโดด", text_color="#8B90A8", font=self._font(9)).pack(side="left")
        ctk.CTkLabel(shortcut, text="S", width=30, height=28, corner_radius=8, fg_color="#2A2D48", text_color="#FFFFFF", font=self._font(10, "bold")).pack(side="left", padx=(12, 6), pady=10)
        ctk.CTkLabel(shortcut, text="สไลด์", text_color="#8B90A8", font=self._font(9)).pack(side="left")

        workspace = ctk.CTkFrame(self.root, corner_radius=0, fg_color=BG)
        workspace.grid(row=0, column=1, sticky="nsew")
        workspace.grid_columnconfigure(0, weight=1)
        workspace.grid_rowconfigure(1, weight=1)

        topbar = ctk.CTkFrame(workspace, height=74, corner_radius=0, fg_color=CARD)
        topbar.grid(row=0, column=0, sticky="ew")
        topbar.grid_propagate(False)
        title_copy = ctk.CTkFrame(topbar, fg_color="transparent")
        title_copy.pack(side="left", padx=21, pady=12)
        ctk.CTkLabel(title_copy, text="Automation Studio", text_color=TEXT, font=self._font(20, "bold"), anchor="w").pack(anchor="w")
        ctk.CTkLabel(
            title_copy,
            text="จัดการบอท Record และ Replay ในหน้าจอเดียว",
            text_color=MUTED,
            font=self._font(10),
            anchor="w",
        ).pack(anchor="w")
        self.status_label = ctk.CTkLabel(
            topbar,
            textvariable=self.status_var,
            height=32,
            corner_radius=10,
            fg_color="#EFF0F5",
            text_color="#555A6E",
            font=self._font(10, "bold"),
            padx=13,
        )
        self.status_label.pack(side="right", padx=20)

        body = ctk.CTkFrame(workspace, fg_color="transparent")
        body.grid(row=1, column=0, sticky="nsew", padx=17, pady=13)
        body.grid_columnconfigure(0, weight=1)
        body.grid_rowconfigure(1, weight=1, minsize=330)
        body.grid_rowconfigure(2, weight=0, minsize=155)

        settings_row = ctk.CTkFrame(body, fg_color="transparent")
        settings_row.grid(row=0, column=0, sticky="nsew", pady=(0, 10))
        settings_row.grid_columnconfigure(0, weight=1, uniform="settings")
        settings_row.grid_columnconfigure(1, weight=1, uniform="settings")

        connection = ctk.CTkFrame(
            settings_row, corner_radius=16, fg_color=CARD, border_width=1, border_color=BORDER,
        )
        connection.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        self._section_header(connection, "plug", "การเชื่อมต่อ ADB", "LDPlayer / Android Emulator")
        fields = ctk.CTkFrame(connection, fg_color="transparent")
        fields.pack(fill="x", padx=16, pady=(0, 13))
        fields.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(fields, text="IP / HOST", text_color=MUTED, font=self._font(9, "bold")).grid(row=0, column=0, padx=(0, 8))
        self.ip_entry = ctk.CTkEntry(
            fields, height=36, corner_radius=10, border_width=1, border_color=BORDER,
            fg_color="#F8F8FC", text_color=TEXT, textvariable=self.ip_var,
        )
        self.ip_entry.grid(row=0, column=1, sticky="ew", padx=(0, 13))
        ctk.CTkLabel(fields, text="PORT", text_color=MUTED, font=self._font(9, "bold")).grid(row=0, column=2, padx=(0, 8))
        self.port_entry = ctk.CTkEntry(
            fields, width=82, height=36, corner_radius=10, border_width=1, border_color=BORDER,
            fg_color="#F8F8FC", text_color=TEXT, textvariable=self.port_var,
        )
        self.port_entry.grid(row=0, column=3, padx=(0, 13))
        self.test_button = ctk.CTkButton(
            fields,
            width=130,
            height=36,
            corner_radius=10,
            text="ทดสอบ ADB",
            image=self.icons["refresh"],
            fg_color="#F0F1F6",
            hover_color="#E6E7EF",
            text_color="#555A6E",
            font=self._font(10, "bold"),
            command=self._test_connection,
        )
        self.test_button.grid(row=0, column=4)

        options = ctk.CTkFrame(
            settings_row, corner_radius=16, fg_color=CARD, border_width=1, border_color=BORDER,
        )
        options.grid(row=0, column=1, sticky="nsew", padx=(5, 0))
        self._section_header(options, "sparkle", "ตัวเลือกในแต่ละรอบ", "ซื้อเฉพาะรายการที่เปิดใช้งาน")
        option_row = ctk.CTkFrame(options, fg_color="transparent")
        option_row.pack(fill="x", padx=16, pady=(0, 13))
        option_row.grid_columnconfigure((0, 1, 2), weight=1)
        switch_args = dict(
            height=28,
            switch_width=40,
            switch_height=21,
            progress_color=PURPLE,
            button_color="#FFFFFF",
            button_hover_color="#FFFFFF",
            text_color="#464A5E",
            font=self._font(10),
        )
        ctk.CTkSwitch(option_row, text="Fast Start", variable=self.fast_start_var, **switch_args).grid(row=0, column=0, sticky="w", padx=(0, 8))
        ctk.CTkSwitch(option_row, text="Cookie Relay", variable=self.cookie_relay_var, **switch_args).grid(row=0, column=1, sticky="w", padx=(0, 8))
        ctk.CTkSwitch(
            option_row,
            text="Random Boost",
            variable=self.use_boost_var,
            command=self._toggle_boost,
            **switch_args,
        ).grid(row=0, column=2, sticky="w")
        self.boost_combo = BoostOptionMenu(
            option_row,
            height=36,
            corner_radius=10,
            values=[name for name, _ in BOOST_CHOICES],
            fg_color="#F4F2FF",
            button_color="#E8E4FF",
            button_hover_color="#DED8FF",
            text_color="#5649B7",
            dropdown_fg_color="#FFFFFF",
            dropdown_hover_color="#F0EDFF",
            dropdown_text_color=TEXT,
            font=self._font(10),
            dropdown_font=self._font(10),
        )
        self.boost_combo.grid(row=1, column=0, columnspan=3, sticky="ew", pady=(9, 0))
        self.boost_combo.current(0)

        profiles = self._card(body, 1)
        profile_header = self._section_header(profiles, "profiles", "โปรไฟล์การเล่น", "เลือกเพื่อแก้ไข หรือลบโปรไฟล์")
        self.profile_count_label = ctk.CTkLabel(
            profile_header,
            textvariable=self.profile_count_var,
            height=28,
            corner_radius=9,
            fg_color=PURPLE_SOFT,
            text_color="#5D4BC3",
            font=self._font(9, "bold"),
            padx=10,
        )
        self.profile_count_label.pack(side="right")

        session_summary = ctk.CTkFrame(profiles, fg_color="transparent")
        session_summary.pack(fill="x", padx=16, pady=(0, 9))
        session_summary.grid_columnconfigure((0, 1, 2), weight=1, uniform="session_summary")
        self._session_summary_tile(
            session_summary,
            0,
            "check",
            "รอบที่เล่นสำเร็จ",
            self.session_runs_var,
            detail_text="สำเร็จ / เริ่มทั้งหมด",
            accent=("#E9F8F0", "#23815C"),
        )
        self._session_summary_tile(
            session_summary,
            1,
            "coin",
            "Coins ทั้งหมด",
            self.session_coins_total_var,
            detail_var=self.session_coins_average_var,
            accent=("#FFF5D8", "#B27A05"),
        )
        self._session_summary_tile(
            session_summary,
            2,
            "xp",
            "EXP ทั้งหมด",
            self.session_exp_total_var,
            detail_var=self.session_exp_average_var,
            accent=("#FFEAF0", "#C74268"),
        )

        self.profile_scroll = ctk.CTkScrollableFrame(
            profiles,
            height=218,
            corner_radius=14,
            fg_color="#F7F8FC",
            scrollbar_button_color="#D9DCE7",
            scrollbar_button_hover_color="#C9CDD9",
        )
        self.profile_scroll.pack(fill="both", expand=True, padx=16, pady=(0, 6))
        self.profile_scroll.grid_columnconfigure((0, 1), weight=1, uniform="profile_cards")
        self.selected_profile_path = None
        self.profile_rows = {}

        profile_actions = ctk.CTkFrame(profiles, fg_color="transparent")
        profile_actions.pack(fill="x", padx=16, pady=(3, 13))
        self.record_button = ctk.CTkButton(
            profile_actions,
            width=145,
            height=36,
            corner_radius=10,
            text="อัดรอบใหม่",
            image=self.icons["record"],
            fg_color=PINK,
            hover_color=PINK_HOVER,
            font=self._font(10, "bold"),
            command=self._record_run,
        )
        self.record_button.pack(side="left")
        self.edit_profile_button = ctk.CTkButton(
            profile_actions,
            width=130,
            height=36,
            corner_radius=10,
            text="แก้รายละเอียด",
            image=self.icons["edit"],
            fg_color=PURPLE_SOFT,
            hover_color="#E4DFFF",
            text_color="#5D4BC3",
            font=self._font(10, "bold"),
            command=self._edit_selected_profile,
        )
        self.edit_profile_button.pack(side="left", padx=7)
        self.delete_profile_button = ctk.CTkButton(
            profile_actions,
            width=120,
            height=36,
            corner_radius=10,
            text="ลบโปรไฟล์",
            image=self.icons["trash"],
            fg_color="#FFF0F3",
            hover_color="#FFE3E9",
            text_color="#C84563",
            font=self._font(10, "bold"),
            command=self._delete_selected_profile,
        )
        self.delete_profile_button.pack(side="left")
        ctk.CTkLabel(
            profile_actions,
            text="แนะนำ 2–3 โปรไฟล์เพื่อให้แต่ละรอบไม่เหมือนกัน",
            text_color="#969BAD",
            font=self._font(9),
        ).pack(side="right")

        log_card = self._card(body, 2, pady=(0, 0))
        log_header = self._section_header(log_card, "activity", "Live Activity", "ดูสถานะการทำงานแบบเรียลไทม์")
        ctk.CTkButton(
            log_header,
            width=82,
            height=30,
            corner_radius=9,
            text="ล้าง Log",
            fg_color="#F1F2F6",
            hover_color="#E7E8EF",
            text_color="#64697D",
            font=self._font(9, "bold"),
            command=self._clear_log,
        ).pack(side="right")
        self.log = ctk.CTkTextbox(
            log_card,
            height=82,
            corner_radius=12,
            border_width=0,
            fg_color="#171A2E",
            text_color="#E0E3EF",
            scrollbar_button_color="#383C58",
            scrollbar_button_hover_color="#4A4F6D",
            font=ctk.CTkFont(family="Cascadia Mono", size=13),
        )
        self.log.pack(fill="both", expand=True, padx=16, pady=(0, 14))
        self.log.configure(state="disabled")
        self._append_log("READY  •  เช็ก ADB แล้วอัดโปรไฟล์แรกได้เลย\n")

    def _select_profile(self, path):
        self.selected_profile_path = path
        self._refresh_profiles()

    @staticmethod
    def _format_profile_date(value):
        if not value:
            return "ไม่พบวันที่บันทึก"
        try:
            parsed = datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
            return parsed.strftime("%d/%m/%Y  •  %H:%M น.")
        except ValueError:
            return str(value)

    @staticmethod
    def _format_profile_duration(seconds):
        total = max(0, int(round(seconds)))
        hours, remainder = divmod(total, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours:d}:{minutes:02d}:{seconds:02d}" if hours else f"{minutes:02d}:{seconds:02d}"

    def _profile_metric(self, parent, column, icon, label, value, accent, selected):
        tile = ctk.CTkFrame(
            parent,
            height=58,
            corner_radius=11,
            fg_color="#FFFFFF" if selected else "#F8F9FC",
            border_width=1,
            border_color="#E6E1FF" if selected else "#ECEEF4",
        )
        tile.grid(row=0, column=column, sticky="nsew", padx=(0 if column == 0 else 3, 3 if column < 3 else 0))
        tile.grid_propagate(False)
        icon_box = ctk.CTkFrame(tile, width=30, height=30, corner_radius=9, fg_color=accent[0])
        icon_box.pack(side="left", padx=(9, 7), pady=13)
        icon_box.pack_propagate(False)
        ctk.CTkLabel(icon_box, text="", image=self.icons[icon]).place(relx=0.5, rely=0.5, anchor="center")
        copy = ctk.CTkFrame(tile, fg_color="transparent")
        copy.pack(side="left", fill="y", pady=(8, 6))
        ctk.CTkLabel(copy, text=label, text_color=MUTED, font=self._font(8, "bold"), anchor="w").pack(anchor="w")
        ctk.CTkLabel(copy, text=value, text_color=accent[1], font=self._font(12, "bold"), anchor="w").pack(anchor="w")
        return tile

    def _session_summary_tile(
        self,
        parent,
        column,
        icon,
        title,
        value_var,
        detail_var=None,
        detail_text="",
        accent=(PURPLE_SOFT, PURPLE),
    ):
        tile = ctk.CTkFrame(
            parent,
            height=78,
            corner_radius=13,
            fg_color="#FAFAFD",
            border_width=1,
            border_color=BORDER,
        )
        tile.grid(
            row=0,
            column=column,
            sticky="nsew",
            padx=(0 if column == 0 else 4, 0 if column == 2 else 4),
        )
        tile.grid_propagate(False)
        icon_box = ctk.CTkFrame(tile, width=40, height=40, corner_radius=11, fg_color=accent[0])
        icon_box.pack(side="left", padx=(13, 10), pady=18)
        icon_box.pack_propagate(False)
        ctk.CTkLabel(icon_box, text="", image=self.icons[icon]).place(relx=0.5, rely=0.5, anchor="center")
        copy = ctk.CTkFrame(tile, fg_color="transparent")
        copy.pack(side="left", fill="y", pady=(8, 6))
        ctk.CTkLabel(copy, text=title, text_color=MUTED, font=self._font(9, "bold"), anchor="w").pack(anchor="w")
        ctk.CTkLabel(copy, textvariable=value_var, text_color=accent[1], font=self._font(15, "bold"), anchor="w").pack(anchor="w")
        detail_options = {"textvariable": detail_var} if detail_var is not None else {"text": detail_text}
        ctk.CTkLabel(
            copy,
            text_color="#969BAD",
            font=self._font(8),
            anchor="w",
            **detail_options,
        ).pack(anchor="w")
        return tile

    def _bind_profile_card(self, widget, path):
        """Make every non-button surface on a profile card selectable."""
        if isinstance(widget, ctk.CTkButton):
            return
        widget.bind("<Button-1>", lambda _event, selected=path: self._select_profile(selected))
        for child in widget.winfo_children():
            self._bind_profile_card(child, path)

    def _refresh_profiles(self):
        previous = self.selected_profile_path
        self.profiles = list_profiles()
        if previous not in self.profiles:
            self.selected_profile_path = self.profiles[0] if self.profiles else None
        profile_count = len(self.profiles)
        self.profile_count_var.set("ยังไม่มีโปรไฟล์" if profile_count == 0 else f"{profile_count} โปรไฟล์พร้อมใช้")

        for child in self.profile_scroll.winfo_children():
            child.destroy()
        self.profile_rows = {}

        if not self.profiles:
            empty = ctk.CTkFrame(self.profile_scroll, height=130, corner_radius=14, fg_color="#FFFFFF", border_width=1, border_color=BORDER)
            empty.grid(row=0, column=0, columnspan=2, sticky="ew", padx=4, pady=4)
            empty.grid_propagate(False)
            icon_box = ctk.CTkFrame(empty, width=46, height=46, corner_radius=14, fg_color=PURPLE_SOFT)
            icon_box.place(relx=0.5, rely=0.36, anchor="center")
            ctk.CTkLabel(icon_box, text="", image=self.icons["profiles"]).place(relx=0.5, rely=0.5, anchor="center")
            ctk.CTkLabel(
                empty,
                text="ยังไม่มีโปรไฟล์ — กด ‘อัดรอบใหม่’ เพื่อบันทึกการเล่นครั้งแรก",
                text_color="#9297AA",
                font=self._font(10),
            ).place(relx=0.5, rely=0.73, anchor="center")
            return

        for index, path in enumerate(self.profiles, 1):
            selected = path == self.selected_profile_path
            try:
                summary = profile_summary(path)
                name = summary["name"]
                recorded_at = self._format_profile_date(summary["created_at"])
                duration = self._format_profile_duration(summary["duration_seconds"])
                action_count = f"{summary['action_count']:,}"
                coins = f"{summary['coins']:,}"
                exp = f"{summary['exp']:,}"
                jump_count = summary["jump_count"]
                slide_count = summary["slide_count"]
                pause_count = summary["pause_count"]
                continue_count = summary["continue_count"]
                quit_count = summary["quit_count"]
                touch_count = summary["touch_count"]
                keyboard_count = summary["keyboard_count"]
                resolution = summary["resolution"]
                resolution_text = "×".join(str(part) for part in resolution[:2])
                file_size = f"{max(1, round(path.stat().st_size / 1024)):,} KB"
            except (OSError, ValueError):
                name = path.stem
                recorded_at = "อ่านรายละเอียดโปรไฟล์ไม่ได้"
                duration = action_count = coins = exp = "—"
                jump_count = slide_count = pause_count = continue_count = quit_count = 0
                touch_count = keyboard_count = 0
                resolution_text = "—"
                file_size = "—"

            card_row, card_column = divmod(index - 1, 2)
            card = ctk.CTkFrame(
                self.profile_scroll,
                height=206,
                corner_radius=15,
                fg_color="#F4F1FF" if selected else "#FFFFFF",
                border_width=2 if selected else 1,
                border_color=PURPLE if selected else BORDER,
            )
            card.grid(
                row=card_row,
                column=card_column,
                columnspan=2 if len(self.profiles) == 1 else 1,
                sticky="nsew",
                padx=(4, 5) if card_column == 0 else (5, 4),
                pady=5,
            )
            card.grid_propagate(False)

            heading = ctk.CTkFrame(card, height=49, fg_color="transparent")
            heading.pack(fill="x", padx=12, pady=(10, 4))
            heading.pack_propagate(False)
            selector = ctk.CTkButton(
                heading,
                width=36,
                height=36,
                corner_radius=11,
                text="✓" if selected else f"{index:02d}",
                fg_color=PURPLE if selected else "#F1F2F7",
                hover_color=PURPLE_HOVER if selected else "#E6E8F0",
                text_color="#FFFFFF" if selected else "#74798E",
                font=self._font(10, "bold"),
                command=partial(self._select_profile, path),
            )
            selector.pack(side="left", padx=(0, 9), pady=6)
            title_button = ctk.CTkButton(
                heading,
                height=45,
                corner_radius=9,
                text=f"{name}\n{recorded_at}",
                anchor="w",
                fg_color="transparent",
                hover_color="#E8E3FF" if selected else "#F6F7FA",
                text_color=TEXT,
                font=self._font(11, "bold"),
                command=partial(self._select_profile, path),
            )
            title_button.pack(side="left", fill="x", expand=True)
            ctk.CTkLabel(
                heading,
                text="กำลังใช้" if selected else "พร้อมสุ่ม",
                height=25,
                corner_radius=8,
                fg_color="#E4DEFF" if selected else "#EDF7F2",
                text_color="#5A48C5" if selected else "#27805C",
                font=self._font(8, "bold"),
                padx=8,
            ).pack(side="right", padx=(8, 0))

            metrics = ctk.CTkFrame(card, fg_color="transparent")
            metrics.pack(fill="x", padx=12, pady=(1, 7))
            metrics.grid_columnconfigure((0, 1, 2, 3), weight=1, uniform="metric")
            self._profile_metric(metrics, 0, "clock", "ระยะเวลา", duration, ("#F0EDFF", "#5D4BC3"), selected)
            self._profile_metric(metrics, 1, "tap", "อินพุต", action_count, ("#E8F7F1", "#237C5B"), selected)
            self._profile_metric(metrics, 2, "coin", "COINS", coins, ("#FFF6D9", "#B27A05"), selected)
            self._profile_metric(metrics, 3, "xp", "EXP", exp, ("#FFEAF0", "#C74268"), selected)

            details = ctk.CTkFrame(card, height=59, corner_radius=10, fg_color="#FFFFFF" if selected else "#FAFAFC")
            details.pack(fill="x", padx=12, pady=(0, 10))
            details.pack_propagate(False)
            detail_copy = ctk.CTkFrame(details, fg_color="transparent")
            detail_copy.pack(side="left", fill="y", padx=10, pady=7)
            ctk.CTkLabel(
                detail_copy,
                text=f"W  กระโดด {jump_count:,}   •   S  สไลด์ {slide_count:,}",
                text_color="#555A70",
                font=self._font(8, "bold"),
                anchor="w",
            ).pack(anchor="w")
            ctk.CTkLabel(
                detail_copy,
                text=f"Pause {pause_count:,}   •   Continue {continue_count:,}   •   Quit {quit_count:,}",
                text_color="#8B90A2",
                font=self._font(8),
                anchor="w",
            ).pack(anchor="w")
            ctk.CTkLabel(
                details,
                text=(
                    f"Touch {touch_count:,}  •  Key {keyboard_count:,}  •  {resolution_text}\n"
                    f"{path.name}  •  {file_size}"
                ),
                text_color="#989CAE",
                font=self._font(8),
                anchor="e",
            ).pack(side="right", padx=10)
            self.profile_rows[path] = card
            self._bind_profile_card(card, path)

    def _selected_profile_path(self):
        return self.selected_profile_path

    def _set_status(self, text, state):
        colors = {
            "idle": ("#EFF0F5", "#555A6E"),
            "running": ("#DCF8E8", "#187044"),
            "success": ("#DCF8E8", "#187044"),
            "testing": ("#FFF2D2", "#946012"),
            "error": ("#FFE5EA", "#B02D4A"),
        }
        background, foreground = colors.get(state, colors["idle"])
        self.status_var.set(text)
        self.status_label.configure(fg_color=background, text_color=foreground)

    def _toggle_boost(self):
        self.boost_combo.configure(state="normal" if self.use_boost_var.get() else "disabled")


def launch_gui():
    root = ctk.CTk(fg_color=BG)
    ModernCookieRunBotGUI(root)
    root.mainloop()


if __name__ == "__main__":
    launch_gui()
