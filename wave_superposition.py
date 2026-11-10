# -*- coding: utf-8 -*-
"""
Traveling Wave Superposition Simulator
Features:
- Live parameter adjustments for amplitudes, frequencies, wave numbers, and angular frequencies
- Real-time animated display of traveling waves and their superposition (interference)
- Controls for playback, pause, reset, speed scaling, and zooming
- Preset scenarios: Standing Wave, Wave Beats, and Destructive Interference
"""

import sys
import tkinter as tk
from tkinter import ttk, messagebox
import numpy as np
import matplotlib
matplotlib.use('TkAgg')
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure


class WaveInterferenceApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Traveling Wave Superposition Simulator")
        self.root.geometry("1200x780")
        self.root.minsize(980, 680)

        # Physics & animation state
        self.t = 0.0
        self.is_running = True
        self.dt = 0.0005        # Base time step per frame
        self.interval_ms = 30   # Frame interval (~33 fps)
        self.anim_id = None

        # Default physics parameters
        self.c_val = 3e8
        self.E01 = 3.0
        self.E02 = 3.0
        self.freq1 = 1e11
        self.freq2 = 35e10
        self.k1 = (2 * np.pi * self.freq1) / self.c_val
        self.k2 = (2 * np.pi * self.freq2) / self.c_val
        self.w1 = 100.0
        self.w2 = 200.0
        self.phi1 = 0.0
        self.phi2 = 0.0
        self.s1 = -1.0  # Right-traveling: kx - wt
        self.s2 = -1.0
        self.xmax = 0.01
        self.npoints = 1000

        # UI Initialization
        self._setup_style()
        self._create_widgets()
        self._bind_shortcuts()

        # Apply parameters and start animation loop
        self.apply_parameters()
        self._animate()

        # Clean window close handler
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def _setup_style(self):
        style = ttk.Style()
        try:
            style.theme_use('clam')
        except Exception:
            pass
        style.configure('TLabel', font=('Segoe UI', 9))
        style.configure('TButton', font=('Segoe UI', 9))
        style.configure('Header.TLabel', font=('Segoe UI', 9, 'bold'))
        style.configure('Title.TLabel', font=('Segoe UI', 12, 'bold'), foreground='#1a237e')

    def _create_widgets(self):
        # Two-column layout
        main_pane = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main_pane.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)

        # Left column: scrollable controls panel
        control_frame = ttk.Frame(main_pane, width=380)
        main_pane.add(control_frame, weight=0)

        # Right column: Matplotlib animated figure
        display_frame = ttk.Frame(main_pane)
        main_pane.add(display_frame, weight=1)

        # Scrollable canvas for controls
        canvas_control = tk.Canvas(control_frame, highlightthickness=0, width=370)
        scrollbar = ttk.Scrollbar(control_frame, orient=tk.VERTICAL, command=canvas_control.yview)
        self.scrollable_content = ttk.Frame(canvas_control, padding=8)

        self.scrollable_content.bind(
            "<Configure>",
            lambda e: canvas_control.configure(scrollregion=canvas_control.bbox("all"))
        )
        canvas_control.create_window((0, 0), window=self.scrollable_content, anchor="nw")
        canvas_control.configure(yscrollcommand=scrollbar.set)

        canvas_control.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Mousewheel scroll support
        def _on_mousewheel(event):
            canvas_control.yview_scroll(int(-1 * (event.delta / 120)), "units")
        canvas_control.bind_all("<MouseWheel>", _on_mousewheel)

        # Build controls and plot
        self._build_control_panel(self.scrollable_content)
        self._build_plot_panel(display_frame)

    def _build_control_panel(self, parent):
        title_lbl = ttk.Label(parent, text="Simulation Controls & Parameters", style='Title.TLabel', anchor='center')
        title_lbl.pack(fill=tk.X, pady=(0, 6))

        # --- Playback Controls ---
        play_box = ttk.LabelFrame(parent, text="Playback Controls", padding=8)
        play_box.pack(fill=tk.X, pady=4)

        btn_row = ttk.Frame(play_box)
        btn_row.pack(fill=tk.X, pady=2)

        self.play_btn = ttk.Button(btn_row, text="⏸ Pause (Space)", command=self.toggle_play)
        self.play_btn.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)

        self.reset_btn = ttk.Button(btn_row, text="🔄 Reset (t=0 / R)", command=self.reset_time)
        self.reset_btn.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)

        # Speed Slider
        speed_frame = ttk.Frame(play_box)
        speed_frame.pack(fill=tk.X, pady=(6, 2))
        ttk.Label(speed_frame, text="Speed:").pack(side=tk.LEFT)
        self.speed_var = tk.DoubleVar(value=1.0)
        self.speed_slider = ttk.Scale(speed_frame, from_=0.1, to=5.0, variable=self.speed_var, orient=tk.HORIZONTAL)
        self.speed_slider.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=4)
        self.speed_lbl = ttk.Label(speed_frame, text="1.0x", width=5)
        self.speed_lbl.pack(side=tk.LEFT)
        self.speed_slider.configure(command=lambda v: self.speed_lbl.config(text=f"{float(v):.1f}x"))

        # --- Presets ---
        preset_box = ttk.LabelFrame(parent, text="Physics Presets", padding=6)
        preset_box.pack(fill=tk.X, pady=4)

        p_row1 = ttk.Frame(preset_box)
        p_row1.pack(fill=tk.X, pady=2)
        ttk.Button(p_row1, text="User Default", command=self.set_preset_original).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)
        ttk.Button(p_row1, text="Standing Wave", command=self.set_preset_standing).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)

        p_row2 = ttk.Frame(preset_box)
        p_row2.pack(fill=tk.X, pady=2)
        ttk.Button(p_row2, text="Wave Beats", command=self.set_preset_beats).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)
        ttk.Button(p_row2, text="Destructive Interf.", command=self.set_preset_destructive).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)

        # --- Wave 1 Settings ---
        w1_box = ttk.LabelFrame(parent, text="Wave 1 (Blue Line)", padding=8)
        w1_box.pack(fill=tk.X, pady=4)

        self.e01_var = tk.StringVar(value=str(self.E01))
        self.freq1_var = tk.StringVar(value=f"{self.freq1:.2e}")
        self.k1_var = tk.StringVar(value=f"{self.k1:.3f}")
        self.w1_var = tk.StringVar(value=str(self.w1))
        self.phi1_var = tk.StringVar(value="0.0")
        self.dir1_var = tk.StringVar(value="+x (Right-traveling)")

        self._create_field(w1_box, "Amplitude (E01):", self.e01_var)
        self._create_field(w1_box, "Frequency f1 (Hz):", self.freq1_var, on_change=self._on_freq1_change)
        self._create_field(w1_box, "Wave number k1 (rad/m):", self.k1_var)
        self._create_field(w1_box, "Angular freq. ω1 (rad/s):", self.w1_var)
        self._create_field(w1_box, "Initial phase φ1 (rad):", self.phi1_var)

        dir1_row = ttk.Frame(w1_box)
        dir1_row.pack(fill=tk.X, pady=2)
        ttk.Label(dir1_row, text="Direction:").pack(side=tk.LEFT)
        dir1_combo = ttk.Combobox(
            dir1_row,
            textvariable=self.dir1_var,
            values=["+x (Right-traveling)", "-x (Left-traveling)"],
            state="readonly",
            width=18
        )
        dir1_combo.pack(side=tk.RIGHT)

        # --- Wave 2 Settings ---
        w2_box = ttk.LabelFrame(parent, text="Wave 2 (Orange Line)", padding=8)
        w2_box.pack(fill=tk.X, pady=4)

        self.e02_var = tk.StringVar(value=str(self.E02))
        self.freq2_var = tk.StringVar(value=f"{self.freq2:.2e}")
        self.k2_var = tk.StringVar(value=f"{self.k2:.3f}")
        self.w2_var = tk.StringVar(value=str(self.w2))
        self.phi2_var = tk.StringVar(value="0.0")
        self.dir2_var = tk.StringVar(value="+x (Right-traveling)")

        self._create_field(w2_box, "Amplitude (E02):", self.e02_var)
        self._create_field(w2_box, "Frequency f2 (Hz):", self.freq2_var, on_change=self._on_freq2_change)
        self._create_field(w2_box, "Wave number k2 (rad/m):", self.k2_var)
        self._create_field(w2_box, "Angular freq. ω2 (rad/s):", self.w2_var)
        self._create_field(w2_box, "Initial phase φ2 (rad):", self.phi2_var)

        dir2_row = ttk.Frame(w2_box)
        dir2_row.pack(fill=tk.X, pady=2)
        ttk.Label(dir2_row, text="Direction:").pack(side=tk.LEFT)
        dir2_combo = ttk.Combobox(
            dir2_row,
            textvariable=self.dir2_var,
            values=["+x (Right-traveling)", "-x (Left-traveling)"],
            state="readonly",
            width=18
        )
        dir2_combo.pack(side=tk.RIGHT)

        # --- Medium & Domain Settings ---
        space_box = ttk.LabelFrame(parent, text="Medium & Domain Settings", padding=8)
        space_box.pack(fill=tk.X, pady=4)

        self.c_var = tk.StringVar(value=f"{self.c_val:.2e}")
        self.xmax_var = tk.StringVar(value=str(self.xmax))
        self.npoints_var = tk.StringVar(value=str(self.npoints))

        self._create_field(space_box, "Wave speed c (m/s):", self.c_var)
        self._create_field(space_box, "Domain length x_max (m):", self.xmax_var)
        self._create_field(space_box, "Grid points N:", self.npoints_var)

        # --- Display Layers ---
        disp_box = ttk.LabelFrame(parent, text="Display Layers", padding=8)
        disp_box.pack(fill=tk.X, pady=4)

        self.show_w1_var = tk.BooleanVar(value=True)
        self.show_w2_var = tk.BooleanVar(value=True)
        self.show_tot_var = tk.BooleanVar(value=True)
        self.show_grid_var = tk.BooleanVar(value=True)

        chk_f1 = ttk.Frame(disp_box)
        chk_f1.pack(fill=tk.X)
        ttk.Checkbutton(chk_f1, text="Show Wave 1", variable=self.show_w1_var, command=self._on_toggle_layers).pack(side=tk.LEFT)
        ttk.Checkbutton(chk_f1, text="Show Wave 2", variable=self.show_w2_var, command=self._on_toggle_layers).pack(side=tk.LEFT, padx=12)

        chk_f2 = ttk.Frame(disp_box)
        chk_f2.pack(fill=tk.X, pady=3)
        ttk.Checkbutton(chk_f2, text="Show Result (Superposition)", variable=self.show_tot_var, command=self._on_toggle_layers).pack(side=tk.LEFT)
        ttk.Checkbutton(chk_f2, text="Show Grid", variable=self.show_grid_var, command=self._on_toggle_grid).pack(side=tk.LEFT, padx=12)

        # Apply Button
        apply_btn = ttk.Button(parent, text="✔ Apply Changes (Enter)", command=self.apply_parameters)
        apply_btn.pack(fill=tk.X, pady=(10, 15))

    def _create_field(self, parent, label_text, var, on_change=None):
        frame = ttk.Frame(parent)
        frame.pack(fill=tk.X, pady=2)
        lbl = ttk.Label(frame, text=label_text)
        lbl.pack(side=tk.LEFT)
        entry = ttk.Entry(frame, textvariable=var, width=14, justify='right')
        entry.pack(side=tk.RIGHT)
        entry.bind("<Return>", lambda e: self.apply_parameters())
        if on_change:
            entry.bind("<FocusOut>", lambda e: on_change())
        return entry

    def _on_freq1_change(self):
        try:
            f = float(self.freq1_var.get())
            c = float(self.c_var.get())
            k = 2 * np.pi * f / c
            self.k1_var.set(f"{k:.3f}")
        except Exception:
            pass

    def _on_freq2_change(self):
        try:
            f = float(self.freq2_var.get())
            c = float(self.c_var.get())
            k = 2 * np.pi * f / c
            self.k2_var.set(f"{k:.3f}")
        except Exception:
            pass

    def _build_plot_panel(self, parent):
        self.fig = Figure(figsize=(8.5, 6), dpi=100)
        self.ax = self.fig.add_subplot(111)

        self.x = np.linspace(0, self.xmax, self.npoints)
        self.line1, = self.ax.plot([], [], label='Wave 1', color='#1f77b4', linestyle='--', alpha=0.75, lw=1.6)
        self.line2, = self.ax.plot([], [], label='Wave 2', color='#ff7f0e', linestyle='--', alpha=0.75, lw=1.6)
        self.line_total, = self.ax.plot([], [], label='Interference Result', color='#000000', lw=2.3)

        self.ax.set_title("Traveling Wave Superposition", fontsize=11, fontweight='bold')
        self.ax.set_xlabel("Position x (m)", fontsize=10)
        self.ax.set_ylabel("Amplitude E", fontsize=10)
        self.ax.grid(True, linestyle=':', alpha=0.6)
        self.ax.legend(loc='upper right', framealpha=0.92)

        self.canvas = FigureCanvasTkAgg(self.fig, master=parent)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        toolbar_frame = ttk.Frame(parent)
        toolbar_frame.pack(fill=tk.X)
        self.toolbar = NavigationToolbar2Tk(self.canvas, toolbar_frame)
        self.toolbar.update()

        # Status footer bar
        self.status_var = tk.StringVar(value="Ready")
        status_bar = ttk.Label(parent, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W, padding=(6, 4))
        status_bar.pack(fill=tk.X)

    def _bind_shortcuts(self):
        self.root.bind("<space>", lambda e: self.toggle_play())
        self.root.bind("<r>", lambda e: self.reset_time())
        self.root.bind("<R>", lambda e: self.reset_time())

    def apply_parameters(self):
        try:
            self.E01 = float(self.e01_var.get())
            self.E02 = float(self.e02_var.get())
            self.k1 = float(self.k1_var.get())
            self.k2 = float(self.k2_var.get())
            self.w1 = float(self.w1_var.get())
            self.w2 = float(self.w2_var.get())
            self.phi1 = float(self.phi1_var.get())
            self.phi2 = float(self.phi2_var.get())
            self.xmax = float(self.xmax_var.get())
            self.npoints = int(self.npoints_var.get())

            self.s1 = -1.0 if "+x" in self.dir1_var.get() else 1.0
            self.s2 = -1.0 if "+x" in self.dir2_var.get() else 1.0

            if self.xmax <= 0 or self.npoints <= 10:
                raise ValueError("x_max must be positive and grid points >= 10.")

            self.x = np.linspace(0, self.xmax, self.npoints)
            self.ax.set_xlim(0, self.xmax)

            # Stable Y-axis bounds
            y_max_bound = (abs(self.E01) + abs(self.E02)) * 1.25
            if y_max_bound == 0:
                y_max_bound = 1.0
            self.ax.set_ylim(-y_max_bound, y_max_bound)

            dir1_str = "+x" if self.s1 == -1.0 else "-x"
            dir2_str = "+x" if self.s2 == -1.0 else "-x"
            self.line1.set_label(f'Wave 1 ({dir1_str}, E={self.E01}, k={self.k1:.1f}, ω={self.w1:.0f})')
            self.line2.set_label(f'Wave 2 ({dir2_str}, E={self.E02}, k={self.k2:.1f}, ω={self.w2:.0f})')
            self.ax.legend(loc='upper right', framealpha=0.92)

            self._update_plot_lines()
            self.canvas.draw_idle()

        except Exception as e:
            messagebox.showerror("Input Error", f"Please check the input values:\n{e}")

    def _update_plot_lines(self):
        # Traveling wave formula: y = E0 * sin(k*x + s*w*t + phi)
        # s = -1 for +x (right-traveling: kx - wt), s = +1 for -x (left-traveling: kx + wt)
        y1 = self.E01 * np.sin(self.k1 * self.x + self.s1 * self.w1 * self.t + self.phi1)
        y2 = self.E02 * np.sin(self.k2 * self.x + self.s2 * self.w2 * self.t + self.phi2)
        y_total = y1 + y2

        self.line1.set_data(self.x, y1)
        self.line2.set_data(self.x, y2)
        self.line_total.set_data(self.x, y_total)

        self.line1.set_visible(self.show_w1_var.get())
        self.line2.set_visible(self.show_w2_var.get())
        self.line_total.set_visible(self.show_tot_var.get())

        self.ax.set_title(f"Wave Interference at t = {self.t:.3f} s", fontsize=11, fontweight='bold')

        # Calculate phase velocities
        v1 = (self.w1 / self.k1) if self.k1 != 0 else 0
        v2 = (self.w2 / self.k2) if self.k2 != 0 else 0
        dir1_sym = "→" if self.s1 == -1.0 else "←"
        dir2_sym = "→" if self.s2 == -1.0 else "←"
        self.status_var.set(
            f"Time: t = {self.t:.3f} s   |   "
            f"Wave 1: {dir1_sym} Phase velocity: {v1:.2f} m/s   |   "
            f"Wave 2: {dir2_sym} Phase velocity: {v2:.2f} m/s"
        )

    def _animate(self):
        if self.is_running:
            speed = self.speed_var.get()
            self.t += self.dt * speed
            self._update_plot_lines()
            self.canvas.draw_idle()

        self.anim_id = self.root.after(self.interval_ms, self._animate)

    def toggle_play(self):
        self.is_running = not self.is_running
        if self.is_running:
            self.play_btn.config(text="⏸ Pause (Space)")
        else:
            self.play_btn.config(text="▶ Play (Space)")

    def reset_time(self):
        self.t = 0.0
        self._update_plot_lines()
        self.canvas.draw_idle()

    def _on_toggle_layers(self):
        self.line1.set_visible(self.show_w1_var.get())
        self.line2.set_visible(self.show_w2_var.get())
        self.line_total.set_visible(self.show_tot_var.get())
        self.canvas.draw_idle()

    def _on_toggle_grid(self):
        self.ax.grid(self.show_grid_var.get(), linestyle=':', alpha=0.6)
        self.canvas.draw_idle()

    # Preset configurations
    def set_preset_original(self):
        """User default parameters from original script"""
        self.e01_var.set("3.0")
        self.freq1_var.set("1.00e+11")
        self.k1_var.set("2094.395")
        self.w1_var.set("100.0")
        self.phi1_var.set("0.0")
        self.dir1_var.set("+x (Right-traveling)")

        self.e02_var.set("3.0")
        self.freq2_var.set("3.50e+11")
        self.k2_var.set("7330.382")
        self.w2_var.set("200.0")
        self.phi2_var.set("0.0")
        self.dir2_var.set("+x (Right-traveling)")

        self.xmax_var.set("0.01")
        self.reset_time()
        self.apply_parameters()

    def set_preset_standing(self):
        """Standing wave: two identical waves traveling in opposite directions"""
        self.e01_var.set("3.0")
        self.freq1_var.set("1.00e+11")
        self.k1_var.set("2094.395")
        self.w1_var.set("100.0")
        self.phi1_var.set("0.0")
        self.dir1_var.set("+x (Right-traveling)")

        self.e02_var.set("3.0")
        self.freq2_var.set("1.00e+11")
        self.k2_var.set("2094.395")
        self.w2_var.set("100.0")
        self.phi2_var.set("0.0")
        self.dir2_var.set("-x (Left-traveling)")

        self.xmax_var.set("0.01")
        self.reset_time()
        self.apply_parameters()

    def set_preset_beats(self):
        """Wave beats: two co-propagating waves with slightly different frequencies"""
        self.e01_var.set("3.0")
        self.freq1_var.set("1.00e+11")
        self.k1_var.set("2094.395")
        self.w1_var.set("100.0")
        self.phi1_var.set("0.0")
        self.dir1_var.set("+x (Right-traveling)")

        self.e02_var.set("3.0")
        self.freq2_var.set("1.10e+11")
        self.k2_var.set("2303.835")
        self.w2_var.set("110.0")
        self.phi2_var.set("0.0")
        self.dir2_var.set("+x (Right-traveling)")

        self.xmax_var.set("0.015")
        self.reset_time()
        self.apply_parameters()

    def set_preset_destructive(self):
        """Complete destructive interference: equal waves with pi phase difference"""
        self.e01_var.set("3.0")
        self.freq1_var.set("1.00e+11")
        self.k1_var.set("2094.395")
        self.w1_var.set("100.0")
        self.phi1_var.set("0.0")
        self.dir1_var.set("+x (Right-traveling)")

        self.e02_var.set("3.0")
        self.freq2_var.set("1.00e+11")
        self.k2_var.set("2094.395")
        self.w2_var.set("100.0")
        self.phi2_var.set(f"{np.pi:.5f}")
        self.dir2_var.set("+x (Right-traveling)")

        self.xmax_var.set("0.01")
        self.reset_time()
        self.apply_parameters()

    def on_close(self):
        self.is_running = False
        if self.anim_id:
            try:
                self.root.after_cancel(self.anim_id)
            except Exception:
                pass
        self.root.destroy()


def main():
    root = tk.Tk()
    app = WaveInterferenceApp(root)
    root.mainloop()


if __name__ == '__main__':
    main()
