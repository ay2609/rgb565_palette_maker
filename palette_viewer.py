import re
import random
import tkinter as tk
from tkinter import ttk


# ── PART 1: parse rgb565_colors.h ─────────────────────────────────────────────
def load_rgb565_header(path):
    """
    Reads lines like:
      #define COLOR_RED 0xF800
    and returns dict name → 16-bit int
    """
    pattern = re.compile(r'#define\s+(\w+)\s+(0x[0-9A-Fa-f]+)')
    colors = {}
    with open(path, 'r') as f:
        for line in f:
            m = pattern.match(line)
            if m:
                name, hex16 = m.groups()
                colors[name] = int(hex16, 16)
    return colors


# ── PART 2: conversions ─────────────────────────────────────────────────────────
def rgb565_to_rgb888(value):
    """Convert 0–0xFFFF RGB565 into (r,g,b) each 0–255."""
    r = (value >> 11) & 0x1F
    g = (value >> 5) & 0x3F
    b = value & 0x1F
    # scale up to 0–255
    return ((r * 255) // 31,
            (g * 255) // 63,
            (b * 255) // 31)


def rgb565_to_rgb888_direct(r, g, b):
    """Convert 0–0xFFFF RGB565 into (r,g,b) each 0–255."""
    return ((r * 255) // 31,
            (g * 255) // 63,
            (b * 255) // 31)

print(rgb565_to_rgb888_direct(16, 7, 5))


def rgb565_components(value):
    """Extract raw (r, g, b) components from RGB565 (5,6,5 bits)."""
    r = (value >> 11) & 0x1F  # 5 bits
    g = (value >> 5) & 0x3F  # 6 bits
    b = value & 0x1F  # 5 bits
    return r, g, b


# ── PART 3: harmony generators ─────────────────────────────────────────────────
def random_scheme(colors, n):
    return random.sample(colors, n)


def complementary(colors, n):
    base = random.choice(colors)
    # Find nearest match in existing colors to the "opposite"
    target = (base + 0x8000) & 0xFFFF  # 180° hue flip
    closest = min(colors, key=lambda c: abs(c - target))
    rest = [c for c in colors if c not in (base, closest)]
    return [base, closest] + random.sample(rest, max(0, n - 2))


SCHEMES = {
    "Random": random_scheme,
    "Complementary": complementary,
    # you can add triadic, analog, etc. here
}


# ── PART 4: GUI ─────────────────────────────────────────────────────────────────
class PaletteApp(tk.Tk):
    def __init__(self, color_map):
        super().__init__()
        self.title("16‑bit Color Palette Generator")
        self.configure(bg="#2e2e2e")
        self.colors = list(color_map.items())
        self.vals = [v for _, v in self.colors]

        self.names = [n for n, _ in self.colors]

        # Modern font
        self.custom_font = ("Helvetica Neue", 12)
        self.swatch_font = ("Helvetica Neue", 10, "bold")

        # Control panel
        ctrl = ttk.Frame(self)
        ctrl.pack(padx=200, pady=55, fill="x")
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TFrame", background="#2e2e2e")
        style.configure("TLabel", background="#2e2e2e", foreground="white", font=self.custom_font)
        style.configure("TButton", font=self.custom_font)
        style.configure("TCombobox", padding=4)
        style.configure("TSpinbox", padding=4)

        ttk.Label(ctrl, text="Scheme:").grid(row=0, column=0, sticky="e", padx=5, pady=5)
        self.scheme_cb = ttk.Combobox(ctrl, values=list(SCHEMES.keys()), state="readonly", width=20)
        self.scheme_cb.current(0)
        self.scheme_cb.grid(row=0, column=1, sticky="w", padx=5)

        ttk.Label(ctrl, text="Colors:").grid(row=1, column=0, sticky="e", padx=5, pady=5)
        self.count_sp = ttk.Spinbox(ctrl, from_=2, to=16, width=5)
        self.count_sp.set(5)
        self.count_sp.grid(row=1, column=1, sticky="w", padx=5)

        btn = ttk.Button(ctrl, text="🎨 Generate", command=self.regenerate_palette)
        btn.grid(row=2, column=0, columnspan=2, pady=10)

        self.canvas = tk.Canvas(self, height=80, bg="#2e2e2e", bd=0, highlightthickness=0)
        self.canvas.pack(fill="x", padx=20, pady=10)
        self.locks = []  # Track (index, value) of locked colors
        self.canvas.bind("<Button-1>", self.toggle_lock)

        self.regenerate_palette()

    def toggle_lock(self, event):
        w = self.canvas.winfo_width()
        n = int(self.count_sp.get())
        sw = w / n
        idx = int(event.x // sw)

        if idx >= len(self.current_palette):
            return

        _, val = self.current_palette[idx]

        for i, (lock_i, lock_val) in enumerate(self.locks):
            if lock_i == idx:
                self.locks.pop(i)
                self.render_palette()  # <-- Force redraw to remove lock symbol
                return  # stop here, no redraw

        self.locks.append((idx, val))
        self.render_palette()  # <-- Force redraw to show lock symbol

    def render_palette(self):
        self.canvas.delete("all")
        self.update_idletasks()
        w = self.canvas.winfo_width() or 500
        n = int(self.count_sp.get())
        sw = w / n

        for i, val in self.current_palette:
            rgb = rgb565_to_rgb888(val)
            rgb565 = rgb565_components(val)
            hex24 = '#%02x%02x%02x' % rgb
            x0, x1 = i * sw, (i + 1) * sw

            lum = (0.299 * rgb[0] + 0.587 * rgb[1] + 0.114 * rgb[2])
            text_color = "black" if lum > 160 else "white"

            self.canvas.create_rectangle(x0, 0, x1, 80, fill=hex24, outline="")

            try:
                name = self.names[self.vals.index(val)].replace("RGB565_", "")
            except ValueError:
                name = f"Unknown_{val}"

            label = f"{name}\n{hex(val)}\n{hex24}\n{rgb565}\n{rgb}"
            self.canvas.create_text((x0 + x1) / 2, 40, text=label,
                                    font=("Helvetica Neue", 9, "bold"),
                                    fill=text_color, justify="center")

            if any(lock_i == i and lock_val == val for lock_i, lock_val in self.locks):
                self.canvas.create_text((x0 + x1) / 2, 70, text="🔒",
                                        font=("Helvetica Neue", 12),
                                        fill=text_color)

    def regenerate_palette(self):
        n = int(self.count_sp.get())
        locked_positions = {i: v for i, v in self.locks}
        locked_vals = set(locked_positions.values())
        remaining_vals = [v for v in self.vals if v not in locked_vals]

        scheme = self.scheme_cb.get()
        func = SCHEMES.get(scheme, random_scheme)
        needed = n - len(locked_positions)
        generated = func(remaining_vals, needed)

        final_palette = []
        gen_idx = 0
        for i in range(n):
            if i in locked_positions:
                final_palette.append(locked_positions[i])
            else:
                final_palette.append(generated[gen_idx])
                gen_idx += 1

        self.current_palette = list(enumerate(final_palette))
        self.render_palette()

    # def redraw(self):
    #     self.canvas.delete("all")
    #     self.update_idletasks()
    #     w = self.canvas.winfo_width() or 500
    #     n = int(self.count_sp.get())
    #     sw = w / n
    #
    #     locked_positions = {i: v for i, v in self.locks}
    #     locked_vals = set(locked_positions.values())
    #     remaining_vals = [v for v in self.vals if v not in locked_vals]
    #
    #     scheme = self.scheme_cb.get()
    #     func = SCHEMES.get(scheme, random_scheme)
    #     needed = n - len(locked_positions)
    #     generated = func(remaining_vals, needed)
    #
    #     # Build full palette with locked colors in correct slots
    #     final_palette = []
    #     gen_idx = 0
    #     for i in range(n):
    #         if i in locked_positions:
    #             final_palette.append(locked_positions[i])
    #         else:
    #             final_palette.append(generated[gen_idx])
    #             gen_idx += 1
    #
    #     self.current_palette = list(enumerate(final_palette))
    #
    #     for i, val in self.current_palette:
    #         rgb = rgb565_to_rgb888(val)
    #         hex24 = '#%02x%02x%02x' % rgb
    #         x0, x1 = i * sw, (i + 1) * sw
    #
    #         lum = (0.299 * rgb[0] + 0.587 * rgb[1] + 0.114 * rgb[2])
    #         text_color = "black" if lum > 160 else "white"
    #
    #         self.canvas.create_rectangle(x0, 0, x1, 80, fill=hex24, outline="")
    #
    #         try:
    #             name = self.names[self.vals.index(val)].replace("RGB565_", "")
    #         except ValueError:
    #             name = f"Unknown_{val}"
    #
    #         label = f"{name}\n{hex(val)}\n{hex24}\n{rgb}"
    #         self.canvas.create_text((x0 + x1) / 2, 40, text=label,
    #                                 font=("Helvetica Neue", 9, "bold"),
    #                                 fill=text_color, justify="center")
    #
    #         if any(lock_i == i and lock_val == val for lock_i, lock_val in self.locks):
    #             self.canvas.create_text((x0 + x1) / 2, 70, text="🔒",
    #                                     font=("Helvetica Neue", 12),
    #                                     fill=text_color)

    # def redraw(self):
    #
    #     n = int(self.count_sp.get())
    #     self.canvas.delete("all")
    #     self.update_idletasks()
    #     w = self.canvas.winfo_width() or 500
    #     sw = w / n
    #     self.current_palette = []  # store displayed colors and their positions
    #
    #     # Handle locked values
    #     locked_vals = [val for _, val in self.locks]
    #     remaining = [v for v in self.vals if v not in locked_vals]
    #     needed = n - len(locked_vals)
    #
    #     scheme = self.scheme_cb.get()
    #     func = SCHEMES.get(scheme, random_scheme)
    #     chosen = locked_vals + func(remaining, needed)
    #     random.shuffle(chosen)  # mix locked colors with generated ones
    #
    #     self.current_palette = list(enumerate(chosen))
    #
    #     for i, val in self.current_palette:
    #         rgb = rgb565_to_rgb888(val)
    #         hex24 = '#%02x%02x%02x' % rgb
    #         x0, x1 = i * sw, (i + 1) * sw
    #
    #         lum = (0.299 * rgb[0] + 0.587 * rgb[1] + 0.114 * rgb[2])
    #         text_color = "black" if lum > 160 else "white"
    #
    #         self.canvas.create_rectangle(x0, 0, x1, 80, fill=hex24, outline="")
    #
    #         try:
    #             name = self.names[self.vals.index(val)].replace("RGB565_", "")
    #         except ValueError:
    #             name = f"Unknown_{val}"
    #
    #         label = f"{name}\n{hex(val)}\n{hex24}\n{rgb}"
    #
    #         self.canvas.create_text((x0 + x1) / 2, 40, text=label,
    #                                 font=("Helvetica Neue", 9, "bold"),
    #                                 fill=text_color, justify="center")
    #
    #         if any(lock_i == i for lock_i, _ in self.locks):
    #             self.canvas.create_text((x0 + x1) / 2, 70, text="🔒",
    #                                     font=("Helvetica Neue", 12),
    #                                     fill=text_color)


if __name__ == "__main__":
    color_map = load_rgb565_header("rgb565_colors.h")
    app = PaletteApp(color_map)
    app.mainloop()
