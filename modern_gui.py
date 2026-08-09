import customtkinter as ctk
from PIL import Image, ImageDraw, ImageTk

from bot import BOOST_CHOICES
from gui import CookieRunBotGUI


BG = "#F4F5FA"
CARD = "#FFFFFF"
SIDEBAR = "#15172A"
SIDEBAR_CARD = "#20233A"
TEXT = "#242638"
MUTED = "#858A9E"
PURPLE = "#6C5CE7"
PURPLE_HOVER = "#7A6BED"
PURPLE_SOFT = "#F0EDFF"
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
    @staticmethod
    def _layout_for_screen(screen_width, screen_height, window_scaling=1.0):
        """Return a window/layout plan that always fits inside the current display."""
        screen_width = max(1, int(screen_width))
        screen_height = max(1, int(screen_height))
        try:
            window_scaling = max(0.5, float(window_scaling))
        except (TypeError, ValueError):
            window_scaling = 1.0

        # CTk scales geometry width/height, while Tk reports the physical
        # display size. Calculate in CTk's logical units to avoid a second
        # 125–150% enlargement on high-DPI Windows laptops.
        logical_screen_width = max(1, int(screen_width / window_scaling))
        logical_screen_height = max(1, int(screen_height / window_scaling))
        # Keep the controller deliberately small so it can sit beside LDPlayer
        # even on a laptop display. The main pane scrolls when space is tight.
        window_width = min(
            logical_screen_width,
            max(600, min(720, logical_screen_width - 24)),
        )
        window_height = min(
            logical_screen_height,
            max(420, min(500, logical_screen_height - 80)),
        )
        compact = True
        sidebar_width = 180 if window_width >= 700 else 168
        sidebar_scrollbar_width = 16
        content_width = max(1, window_width - sidebar_width - sidebar_scrollbar_width)
        scaled_window_width = round(window_width * window_scaling)
        scaled_window_height = round(window_height * window_scaling)
        lower_chrome_allowance = round(80 * window_scaling)
        centered_y = max(0, (screen_height - scaled_window_height) // 2)
        safe_bottom_y = max(0, screen_height - scaled_window_height - lower_chrome_allowance)
        return {
            "width": window_width,
            "height": window_height,
            # CTk does not scale the position part of a geometry string.
            "x": max(0, (screen_width - scaled_window_width) // 2),
            # Cap vertical centering so the title bar and taskbar never cover
            # the lower controls on a short display.
            "y": min(centered_y, safe_bottom_y),
            "window_scaling": window_scaling,
            "compact": compact,
            "sidebar_width": sidebar_width,
            "sidebar_outer_width": sidebar_width + sidebar_scrollbar_width,
            "content_width": content_width,
            "narrow_controls": content_width < 500,
            "boost_combo_row": 3 if content_width < 500 else 1,
            "stack_settings": True,
            "summary_columns": 2,
        }

    def _configure_styles(self):
        ctk.set_appearance_mode("Light")
        ctk.set_default_color_theme("blue")
        get_window_scaling = getattr(self.root, "_get_window_scaling", None)
        window_scaling = get_window_scaling() if callable(get_window_scaling) else 1.0
        self.layout = self._layout_for_screen(
            self.root.winfo_screenwidth(),
            self.root.winfo_screenheight(),
            window_scaling,
        )
        self.compact_layout = self.layout["compact"]
        self.sidebar_width = self.layout["sidebar_width"]
        self.summary_columns = self.layout["summary_columns"]
        self.narrow_controls = self.layout["narrow_controls"]
        self.root.geometry(
            f'{self.layout["width"]}x{self.layout["height"]}'
            f'+{self.layout["x"]}+{self.layout["y"]}'
        )
        minimum_width = min(660, self.layout["width"])
        minimum_height = min(430, self.layout["height"])
        self.root.minsize(minimum_width, minimum_height)
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
        elif name == "refresh":
            draw.arc((p(12), p(12), p(52), p(52)), 35, 300, fill=color, width=width)
            draw.polygon(((p(46), p(9)), (p(55), p(22)), (p(40), p(23))), fill=color)
        elif name == "plug":
            draw.line((p(20), p(12), p(20), p(24)), fill=color, width=width)
            draw.line((p(44), p(12), p(44), p(24)), fill=color, width=width)
            draw.rounded_rectangle((p(14), p(21), p(50), p(39)), radius=p(6), outline=color, width=width)
            draw.line((p(32), p(39), p(32), p(54)), fill=color, width=width)
        elif name == "sparkle":
            draw.polygon(((p(32), p(7)), (p(38), p(25)), (p(56), p(32)), (p(38), p(39)),
                          (p(32), p(57)), (p(26), p(39)), (p(8), p(32)), (p(26), p(25))), fill=color)
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
            "refresh": ("refresh", "#5D6277", 16),
            "plug": ("plug", PURPLE, 18),
            "sparkle": ("sparkle", "#F2A93B", 18),
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

    def _font(self, size, weight="normal"):
        # CustomTkinter font sizes are pixels. Keep body text at least 12 px so
        # Thai glyphs stay comfortable to read on high-resolution displays.
        if self.compact_layout:
            readable_size = max(12, round(size * 1.15))
        else:
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

        if self.compact_layout:
            sidebar = ctk.CTkScrollableFrame(
                self.root,
                width=self.sidebar_width,
                corner_radius=0,
                border_width=0,
                fg_color=SIDEBAR,
                scrollbar_button_color="#343852",
                scrollbar_button_hover_color="#484D6C",
            )
        else:
            sidebar = ctk.CTkFrame(
                self.root,
                width=self.sidebar_width,
                corner_radius=0,
                fg_color=SIDEBAR,
            )
        sidebar.grid(row=0, column=0, sticky="nsew")
        sidebar.grid_columnconfigure(0, weight=1)
        if not self.compact_layout:
            sidebar.grid_propagate(False)
            sidebar.grid_rowconfigure(6, weight=1)

        run_row = 1

        brand = ctk.CTkFrame(sidebar, fg_color="transparent")
        brand.grid(
            row=0,
            column=0,
            sticky="ew",
            padx=12 if self.compact_layout else 20,
            pady=(12, 10),
        )
        brand_icon_size = 42 if self.compact_layout else 50
        cookie_box = ctk.CTkFrame(
            brand,
            width=brand_icon_size,
            height=brand_icon_size,
            corner_radius=14 if self.compact_layout else 16,
            fg_color=PURPLE,
        )
        cookie_box.pack(side="left")
        cookie_box.pack_propagate(False)
        ctk.CTkLabel(cookie_box, text="", image=self.icons["cookie"]).place(relx=0.5, rely=0.5, anchor="center")
        brand_copy = ctk.CTkFrame(brand, fg_color="transparent")
        brand_copy.pack(side="left", padx=(9 if self.compact_layout else 12, 0))
        ctk.CTkLabel(brand_copy, text="COOKIEBOT", text_color="#FFFFFF", font=self._font(16, "bold")).pack(anchor="w")
        ctk.CTkLabel(
            brand_copy,
            text="AUTOMATION" if self.compact_layout else "CLASSIC AUTOMATION",
            text_color="#747992",
            font=self._font(9, "bold"),
        ).pack(anchor="w")

        run_panel = ctk.CTkFrame(sidebar, corner_radius=16, fg_color=SIDEBAR_CARD)
        run_panel.grid(
            row=run_row,
            column=0,
            sticky="ew",
            padx=12 if self.compact_layout else 15,
            pady=(6, 0),
        )
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
        self.max_runs_spinbox = ctk.CTkEntry(
            repeat,
            width=62,
            height=34,
            corner_radius=10,
            border_width=1,
            border_color="#3B3F5C",
            fg_color="#292C47",
            text_color="#FFFFFF",
            justify="center",
            textvariable=self.max_runs_var,
        )
        self.max_runs_spinbox.pack(side="right")
        ctk.CTkLabel(run_panel, text="0 = เล่นไม่จำกัด", text_color="#737891", font=self._font(9), anchor="w").pack(
            fill="x", padx=14, pady=(7, 14)
        )

        workspace = ctk.CTkFrame(self.root, corner_radius=0, fg_color=BG)
        workspace.grid(row=0, column=1, sticky="nsew")
        workspace.grid_columnconfigure(0, weight=1)
        workspace.grid_rowconfigure(1, weight=1)

        topbar = ctk.CTkFrame(workspace, height=60, corner_radius=0, fg_color=CARD)
        topbar.grid(row=0, column=0, sticky="ew")
        topbar.grid_propagate(False)
        title_copy = ctk.CTkFrame(topbar, fg_color="transparent")
        title_copy.pack(side="left", padx=18, pady=8)
        ctk.CTkLabel(title_copy, text="CookieRun Bot", text_color=TEXT, font=self._font(17, "bold"), anchor="w").pack(anchor="w")
        ctk.CTkLabel(
            title_copy,
            text=(
                "ซื้อไอเทม • Start / Stop"
                if self.narrow_controls
                else "ตั้งค่าการซื้อไอเทม แล้วเริ่มบอทได้ทันที"
            ),
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
        self.status_label.pack(side="right", padx=16)

        if self.compact_layout:
            body = ctk.CTkScrollableFrame(
                workspace,
                corner_radius=0,
                border_width=0,
                fg_color=BG,
                scrollbar_button_color="#D9DCE7",
                scrollbar_button_hover_color="#C9CDD9",
            )
            body.grid(row=1, column=0, sticky="nsew", padx=(12, 4), pady=(10, 7))
        else:
            body = ctk.CTkFrame(workspace, fg_color="transparent")
            body.grid(row=1, column=0, sticky="nsew", padx=17, pady=13)
        body.grid_columnconfigure(0, weight=1)
        if not self.compact_layout:
            body.grid_rowconfigure(3, weight=1, minsize=150)

        settings_row = ctk.CTkFrame(body, fg_color="transparent")
        settings_row.grid(row=0, column=0, sticky="nsew", pady=(0, 10))
        settings_row.grid_columnconfigure(0, weight=1, uniform="settings")
        if not self.layout["stack_settings"]:
            settings_row.grid_columnconfigure(1, weight=1, uniform="settings")

        connection = ctk.CTkFrame(
            settings_row, corner_radius=16, fg_color=CARD, border_width=1, border_color=BORDER,
        )
        connection.grid(
            row=0,
            column=0,
            sticky="nsew",
            padx=(0, 5) if not self.layout["stack_settings"] else 0,
            pady=(0, 5) if self.layout["stack_settings"] else 0,
        )
        self._section_header(connection, "plug", "การเชื่อมต่อ ADB", "LDPlayer / Android Emulator")
        fields = ctk.CTkFrame(connection, fg_color="transparent")
        fields.pack(fill="x", padx=16, pady=(0, 13))
        fields.grid_columnconfigure(1, weight=1)
        ip_label = ctk.CTkLabel(fields, text="IP / HOST", text_color=MUTED, font=self._font(9, "bold"))
        self.ip_entry = ctk.CTkEntry(
            fields, height=36, corner_radius=10, border_width=1, border_color=BORDER,
            fg_color="#F8F8FC", text_color=TEXT, textvariable=self.ip_var,
        )
        port_label = ctk.CTkLabel(fields, text="PORT", text_color=MUTED, font=self._font(9, "bold"))
        self.port_entry = ctk.CTkEntry(
            fields, width=82, height=36, corner_radius=10, border_width=1, border_color=BORDER,
            fg_color="#F8F8FC", text_color=TEXT, textvariable=self.port_var,
        )
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
        if self.narrow_controls:
            ip_label.grid(row=0, column=0, sticky="w", padx=(0, 8), pady=(0, 7))
            self.ip_entry.grid(row=0, column=1, sticky="ew", pady=(0, 7))
            port_label.grid(row=1, column=0, sticky="w", padx=(0, 8), pady=(0, 7))
            self.port_entry.grid(row=1, column=1, sticky="ew", pady=(0, 7))
            self.test_button.grid(row=2, column=0, columnspan=2, sticky="ew")
        else:
            ip_label.grid(row=0, column=0, padx=(0, 8))
            self.ip_entry.grid(row=0, column=1, sticky="ew", padx=(0, 13))
            port_label.grid(row=0, column=2, padx=(0, 8))
            self.port_entry.grid(row=0, column=3, padx=(0, 13))
            self.test_button.grid(row=0, column=4)

        options = ctk.CTkFrame(
            settings_row, corner_radius=16, fg_color=CARD, border_width=1, border_color=BORDER,
        )
        options.grid(
            row=1 if self.layout["stack_settings"] else 0,
            column=0 if self.layout["stack_settings"] else 1,
            sticky="nsew",
            padx=(5, 0) if not self.layout["stack_settings"] else 0,
            pady=(5, 0) if self.layout["stack_settings"] else 0,
        )
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
        fast_start_switch = ctk.CTkSwitch(
            option_row,
            text="Fast Start",
            variable=self.fast_start_var,
            **switch_args,
        )
        cookie_relay_switch = ctk.CTkSwitch(
            option_row,
            text="Cookie Relay",
            variable=self.cookie_relay_var,
            **switch_args,
        )
        random_boost_switch = ctk.CTkSwitch(
            option_row,
            text="Random Boost",
            variable=self.use_boost_var,
            command=self._toggle_boost,
            **switch_args,
        )
        if self.narrow_controls:
            fast_start_switch.grid(row=0, column=0, columnspan=3, sticky="w")
            cookie_relay_switch.grid(row=1, column=0, columnspan=3, sticky="w", pady=(4, 0))
            random_boost_switch.grid(row=2, column=0, columnspan=3, sticky="w", pady=(4, 0))
        else:
            fast_start_switch.grid(row=0, column=0, sticky="w", padx=(0, 8))
            cookie_relay_switch.grid(row=0, column=1, sticky="w", padx=(0, 8))
            random_boost_switch.grid(row=0, column=2, sticky="w")
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
        self.boost_combo.grid(
            row=self.layout["boost_combo_row"],
            column=0,
            columnspan=3,
            sticky="ew",
            pady=(9, 0),
        )
        self.boost_combo.current(0)

        statistics = self._card(body, 1)
        self._section_header(
            statistics,
            "activity",
            "สถิติการเล่นรอบปัจจุบัน",
            "Coins และ EXP หลังตัวคูณหยุดแล้ว",
        )
        session_summary = ctk.CTkFrame(statistics, fg_color="transparent")
        session_summary.pack(fill="x", padx=16, pady=(0, 9))
        session_summary.grid_columnconfigure(
            tuple(range(self.summary_columns)),
            weight=1,
            uniform="session_summary",
        )
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
        self._session_summary_tile(
            session_summary,
            3,
            "clock",
            "เวลาที่ใช้",
            self.session_elapsed_var,
            detail_var=self.session_elapsed_detail_var,
            accent=("#EAF2FF", "#356FB6"),
        )

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
        self._append_log("READY  •  ตั้งค่าไอเทม แล้วทดสอบ ADB ก่อนเริ่ม\n")

    def _session_summary_tile(
        self,
        parent,
        position,
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
        row, column = divmod(position, self.summary_columns)
        last_column = self.summary_columns - 1
        last_row = (4 - 1) // self.summary_columns
        tile.grid(
            row=row,
            column=column,
            sticky="nsew",
            padx=(0 if column == 0 else 4, 0 if column == last_column else 4),
            pady=(0 if row == 0 else 4, 0 if row == last_row else 4),
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
