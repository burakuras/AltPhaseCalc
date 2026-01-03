import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
import threading
from datetime import datetime, timedelta
import numpy as np

# Astronomi kütüphaneleri
from astropy.coordinates import SkyCoord, EarthLocation, AltAz
from astropy.time import Time
from astropy import units as u
from astroquery.vizier import Vizier

# --- Yapılandırma ---
DB_FILENAME = "stars_db.json"
LOCATION_NAME = "for ANKARA UNIVERSITY KREIKEN OBSERVATORY"
LATITUDE = 39.8436 * u.deg
LONGITUDE = 32.7992 * u.deg
ELEVATION = 1256 * u.m
UTC_OFFSET = 3

OBSERVER_LOC = EarthLocation(lat=LATITUDE, lon=LONGITUDE, height=ELEVATION)

# --- RENK PALETİ ---
COLOR_BG_MAIN = "#121212"
COLOR_CARD_BG = "#1e1e1e"
COLOR_INPUT_BG = "#2d2d2d"
COLOR_ACCENT = "#bb86fc"   # Mor
COLOR_TEXT_MAIN = "#fc8301"  # Turuncu
COLOR_TEXT_SEC = "#b0b0b0"

class BinaryStarPlanner(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Eclipsing Binary Planner (V11 - Burak Uras Edition)")
        self.geometry("1280x850")
        self.configure(bg=COLOR_BG_MAIN)
        
        # İkon yükleme denemesi (Eğer icon.ico varsa kullanır)
        try:
            self.iconbitmap("icon.ico")
        except:
            pass

        self._setup_modern_theme()

        self.tag_colors = {
            "eclipse": ("#3e1818", "#ff9999"),
            "low":     ("#3e3010", "#ffe082"),
            "horizon": ("#181818", "#555555"),
            "normal":  (COLOR_CARD_BG, COLOR_TEXT_MAIN)
        }

        self.stars_data = self.load_database()
        self.create_layout()

    def _setup_modern_theme(self):
        style = ttk.Style(self)
        style.theme_use('clam')
        style.configure(".", background=COLOR_BG_MAIN, foreground=COLOR_TEXT_MAIN, borderwidth=0)
        style.configure("Card.TFrame", background=COLOR_CARD_BG)
        style.configure("Header.TLabel", background=COLOR_BG_MAIN, foreground=COLOR_TEXT_MAIN, font=("Segoe UI", 18, "bold"))
        style.configure("CardTitle.TLabel", background=COLOR_CARD_BG, foreground=COLOR_ACCENT, font=("Segoe UI", 11, "bold"))
        style.configure("Normal.TLabel", background=COLOR_CARD_BG, foreground=COLOR_TEXT_SEC, font=("Segoe UI", 10))
        style.configure("Modern.TEntry", fieldbackground=COLOR_INPUT_BG, foreground=COLOR_TEXT_MAIN, insertcolor=COLOR_TEXT_MAIN, borderwidth=5, relief="flat")
        
        style.configure("Accent.TButton", background=COLOR_ACCENT, foreground="#000000", font=("Segoe UI", 9, "bold"), borderwidth=0, padding=5)
        style.map("Accent.TButton", background=[('active', COLOR_TEXT_MAIN), ('pressed', '#aaaaaa')])

        style.configure("VSX.TButton", background="#2196F3", foreground="#ffffff", font=("Segoe UI", 9, "bold"), borderwidth=0, padding=5)
        style.map("VSX.TButton", background=[('active', '#64b5f6'), ('pressed', '#1976d2')])

        style.configure("Treeview", background=COLOR_CARD_BG, foreground=COLOR_TEXT_MAIN, fieldbackground=COLOR_CARD_BG, font=("Consolas", 10), borderwidth=0, rowheight=28)
        style.configure("Treeview.Heading", background="#252525", foreground=COLOR_TEXT_SEC, font=("Segoe UI", 9, "bold"), borderwidth=0, relief="flat")
        style.map("Treeview.Heading", background=[('active', '#303030')])
        style.configure("Vertical.TScrollbar", background=COLOR_CARD_BG, troughcolor=COLOR_CARD_BG, arrowcolor=COLOR_TEXT_SEC, borderwidth=0, relief="flat")

    def load_database(self):
        if not os.path.exists(DB_FILENAME): return []
        try:
            with open(DB_FILENAME, 'r') as f: return json.load(f)
        except: return []

    def save_database(self):
        try:
            with open(DB_FILENAME, 'w') as f: json.dump(self.stars_data, f, indent=4)
        except Exception as e: messagebox.showerror("Hata", str(e))

    # --- SIMBAD ---
    def fetch_simbad_coords(self):
        name = self.entry_name.get().strip()
        if not name: return messagebox.showwarning("Warning", "Please enter a variable star name.")
        
        self.btn_fetch.config(state=tk.DISABLED, text="Searching...")
        threading.Thread(target=self._query_simbad_worker, args=(name,), daemon=True).start()

    def _query_simbad_worker(self, name):
        try:
            coords = SkyCoord.from_name(name)
            ra_deg = coords.ra.degree
            dec_deg = coords.dec.degree
            self.after(0, lambda: self._update_ui_coords(ra_deg, dec_deg))
        except Exception as e:
            err_msg = str(e)
            if "Name could not be resolved" in err_msg:
                self.after(0, lambda: messagebox.showerror("Not Found", f"'{name}' not found in Simbad."))
            else:
                self.after(0, lambda: messagebox.showerror("Error", f"Simbad Error: {err_msg}"))
        finally:
            self.after(0, lambda: self.btn_fetch.config(state=tk.NORMAL, text="Simbad RA/Dec"))

    def _update_ui_coords(self, ra, dec):
        self.entry_ra.delete(0, tk.END); self.entry_ra.insert(0, f"{ra:.6f}")
        self.entry_dec.delete(0, tk.END); self.entry_dec.insert(0, f"{dec:.6f}")

    # --- VSX + GCVS ---
    def fetch_vsx_data(self):
        name = self.entry_name.get().strip()
        if not name: return messagebox.showwarning("Warning", "Please enter a variable star name.")
        
        self.btn_vsx.config(state=tk.DISABLED, text="Searching...")
        threading.Thread(target=self._query_smart_worker, args=(name,), daemon=True).start()

    def _query_smart_worker(self, name):
        period = None
        epoch = None
        source_used = ""
        errors = []

        # 1. VSX
        try:
            v_vsx = Vizier(columns=['Name', 'Period', 'P1', 'Epoch'], catalog="B/vsx")
            result_vsx = v_vsx.query_object(name)
            
            if result_vsx and len(result_vsx) > 0:
                data = result_vsx[0][0]
                if 'Period' in data.columns and not np.ma.is_masked(data['Period']):
                    period = float(data['Period'])
                elif 'P1' in data.columns and not np.ma.is_masked(data['P1']):
                    period = float(data['P1'])
                
                if 'Epoch' in data.columns and not np.ma.is_masked(data['Epoch']):
                    epoch = float(data['Epoch'])
                
                if period: source_used = "VSX"
        except Exception as e:
            errors.append(f"VSX Error: {str(e)}")

        # 2. GCVS
        if period is None:
            try:
                v_gcvs = Vizier(columns=['Period', 'Epoch'], catalog="B/gcvs")
                result_gcvs = v_gcvs.query_object(name)

                if result_gcvs and len(result_gcvs) > 0:
                    data = result_gcvs[0][0]
                    if 'Period' in data.columns and not np.ma.is_masked(data['Period']):
                        period = float(data['Period'])
                    if 'Epoch' in data.columns and not np.ma.is_masked(data['Epoch']):
                        epoch = float(data['Epoch'])
                    
                    if period: source_used = "GCVS"
            except Exception as e:
                errors.append(f"GCVS Error: {str(e)}")

        # Epoch Fix
        if period:
            final_period = period
            final_epoch = epoch

            if final_epoch is not None:
                s_epoch = str(final_epoch)
                parts = s_epoch.split('.')
                integer_part = parts[0]
                if len(integer_part) == 5:
                    try:
                        final_epoch = float("24" + s_epoch)
                    except:
                        pass

            if final_epoch is None:
                self.after(0, lambda: messagebox.showinfo("Partial Data", f"Source: {source_used}\nPeriod found but Epoch is missing."))
                self.after(0, lambda: self._update_ui_vsx(final_period, ""))
            else:
                self.after(0, lambda: self._update_ui_vsx(final_period, final_epoch))
        else:
            err_str = "\n".join(errors)
            self.after(0, lambda: messagebox.showerror("Not Found", f"No data found for '{name}'.\n\n{err_str}"))

        self.after(0, lambda: self.btn_vsx.config(state=tk.NORMAL, text="AAVSO/VSX Data Fetch"))

    def _update_ui_vsx(self, period, epoch):
        self.entry_period.delete(0, tk.END); self.entry_period.insert(0, str(period))
        if epoch != "":
            self.entry_epoch.delete(0, tk.END); self.entry_epoch.insert(0, str(epoch))
        if not self.entry_ra.get():
             self.fetch_simbad_coords()

    # --- BUTTONS ---
    def add_star(self):
        try:
            name = self.entry_name.get().strip()
            vals = []
            for e in [self.entry_ra, self.entry_dec, self.entry_epoch, self.entry_period]:
                val_str = e.get()
                if not val_str: raise ValueError("Please fill all fields.")
                vals.append(float(val_str))
            
            if not name: raise ValueError("Please enter a variable star name.")
            
            for s in self.stars_data:
                if s['name'].lower() == name.lower():
                    if not messagebox.askyesno("Update?", f"'{name}' already exists. Update it?"):
                        return
                    self.stars_data.remove(s)
                    break

            self.stars_data.append({"name": name, "ra": vals[0], "dec": vals[1], "epoch": vals[2], "period": vals[3]})
            self.save_database(); self.refresh_list(); self.clear_inputs()
        except Exception as e: messagebox.showerror("Error", str(e))

    def delete_star(self):
        selected_item = self.tree_stars.selection()
        if not selected_item:
            return

        name = self.tree_stars.item(selected_item[0])['values'][0]
        self.stars_data = [s for s in self.stars_data if s['name'] != name]
        self.save_database()
        self.refresh_list()

    def calculate(self):
        for item in self.tree_res.get_children(): self.tree_res.delete(item)
        try:
            start = datetime.strptime(self.entry_date.get(), "%Y-%m-%d").replace(hour=18, minute=0, second=0)
            for i in range(13):
                local = start + timedelta(hours=i)
                astro_t = Time(local - timedelta(hours=UTC_OFFSET))
                frame = AltAz(obstime=astro_t, location=OBSERVER_LOC)
                
                for s in self.stars_data:
                    target = SkyCoord(ra=s['ra']*u.deg, dec=s['dec']*u.deg, frame='icrs')
                    ltt = astro_t.light_travel_time(target, location=OBSERVER_LOC)
                    hjd = (astro_t + ltt).jd
                    
                    phase = ((hjd - s['epoch']) / s['period']) % 1.0
                    if phase < 0: phase += 1.0
                    alt = target.transform_to(frame).alt.degree

                    stat, tag = "Observable", "normal"
                    if alt < 0: stat, tag = "Below Horizon", "horizon"
                    elif alt < 20: stat, tag = "Low Altitude", "low"
                    
                    if phase <= 0.05 or phase >= 0.95: 
                        if alt > 0: stat, tag = "MINIMUM", "eclipse"
                    self.tree_res.insert("", tk.END, values=(local.strftime("%H:%M"), s['name'], f"{phase:.4f}", f"{alt:.1f}", stat), tags=(tag,))
        except Exception as e: messagebox.showerror("Error", str(e))

    def refresh_list(self):
        for item in self.tree_stars.get_children(): self.tree_stars.delete(item)
        for s in self.stars_data: self.tree_stars.insert("", tk.END, values=(s['name'], s['period']))

    def clear_inputs(self):
        for e in [self.entry_name, self.entry_ra, self.entry_dec, self.entry_epoch, self.entry_period]: e.delete(0, tk.END)

    def create_layout(self):
        header_frame = tk.Frame(self, bg=COLOR_BG_MAIN, height=80)
        header_frame.pack(fill=tk.X, side=tk.TOP, pady=(20, 10), padx=30)
        
        # Sol Taraf: Başlık
        tk.Label(header_frame, text="ECLIPSING BINARY PLANNER", font=("Segoe UI", 24, "bold"), bg=COLOR_BG_MAIN, fg=COLOR_TEXT_MAIN).pack(side=tk.LEFT)
        tk.Label(header_frame, text=LOCATION_NAME, font=("Segoe UI", 12), bg=COLOR_BG_MAIN, fg=COLOR_TEXT_SEC).pack(side=tk.LEFT, padx=20, pady=(12,0))
        
        # --- BURAK URAS CREDITS (SAĞ ÜST) ---
        tk.Label(header_frame, text="Code by Burak Uras", font=("Segoe UI", 10, "italic"), bg=COLOR_BG_MAIN, fg=COLOR_TEXT_SEC).pack(side=tk.RIGHT, anchor="se", pady=(15, 0))

        main_container = tk.Frame(self, bg=COLOR_BG_MAIN)
        main_container.pack(fill=tk.BOTH, expand=True, padx=30, pady=20)
        main_container.columnconfigure(1, weight=1)
        main_container.rowconfigure(0, weight=1)

        sidebar = tk.Frame(main_container, bg=COLOR_BG_MAIN, width=350)
        sidebar.grid(row=0, column=0, sticky="ns", padx=(0, 20))
        sidebar.pack_propagate(False)

        self._create_card_add_star(sidebar)
        tk.Frame(sidebar, bg=COLOR_BG_MAIN, height=20).pack()
        self._create_card_database(sidebar)

        content = tk.Frame(main_container, bg=COLOR_BG_MAIN)
        content.grid(row=0, column=1, sticky="nsew")
        self._create_card_results(content)

    def _create_card_add_star(self, parent):
        card = ttk.Frame(parent, style="Card.TFrame", padding=20)
        card.pack(fill=tk.X)
        ttk.Label(card, text="ADD STAR", style="CardTitle.TLabel").pack(anchor="w", pady=(0, 15))
        form = tk.Frame(card, bg=COLOR_CARD_BG)
        form.pack(fill=tk.X)
        tk.Frame(form, height=1, bg=COLOR_CARD_BG).grid(row=0, columnspan=2, pady=5)
        
        ttk.Label(form, text="Star Name", style="Normal.TLabel").grid(row=1, column=0, sticky="w")
        self.entry_name = ttk.Entry(form, style="Modern.TEntry", width=15)
        self.entry_name.grid(row=2, column=0, columnspan=2, sticky="ew", padx=(0, 0), pady=(0,10))
        
        btn_frame = tk.Frame(form, bg=COLOR_CARD_BG)
        btn_frame.grid(row=3, column=0, columnspan=2, sticky="ew")
        
        self.btn_fetch = ttk.Button(btn_frame, text="Simbad RA/Dec", style="Accent.TButton", command=self.fetch_simbad_coords)
        self.btn_fetch.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        self.btn_vsx = ttk.Button(btn_frame, text="AAVSO/VSX Data Fetch", style="VSX.TButton", command=self.fetch_vsx_data)
        self.btn_vsx.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 0))

        fields = ["RA (deg)", "Dec (deg)", "Epoch (HJD)", "Period (days)"]
        self.entries = []
        for i, text in enumerate(fields):
            row_idx = 4 + (i * 2)
            ttk.Label(form, text=text, style="Normal.TLabel").grid(row=row_idx, column=0, columnspan=2, sticky="w", pady=(10, 0))
            e = ttk.Entry(form, style="Modern.TEntry")
            e.grid(row=row_idx+1, column=0, columnspan=2, sticky="ew")
            self.entries.append(e)
        self.entry_ra, self.entry_dec, self.entry_epoch, self.entry_period = self.entries
        tk.Frame(card, height=20, bg=COLOR_CARD_BG).pack()
        ttk.Button(card, text="+ DATABASE SAVE", style="Accent.TButton", command=self.add_star).pack(fill=tk.X)

    def _create_card_database(self, parent):
        card = ttk.Frame(parent, style="Card.TFrame", padding=20)
        card.pack(fill=tk.BOTH, expand=True)
        
        header_frame = tk.Frame(card, bg=COLOR_CARD_BG)
        header_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(header_frame, text="REGISTERED STARS", style="CardTitle.TLabel").pack(side=tk.LEFT)
        ttk.Button(header_frame, text="DELETE SELECTED", style="Accent.TButton", command=self.delete_star).pack(side=tk.RIGHT)
        
        list_container = tk.Frame(card, bg=COLOR_CARD_BG)
        list_container.pack(fill=tk.BOTH, expand=True)
        self.tree_stars = ttk.Treeview(list_container, columns=('name', 'period'), show='headings')
        self.tree_stars.heading('name', text='Star', anchor="w"); self.tree_stars.column('name', width=120)
        self.tree_stars.heading('period', text='Period', anchor="w"); self.tree_stars.column('period', width=80)
        self.tree_stars.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb = ttk.Scrollbar(list_container, orient="vertical", command=self.tree_stars.yview)
        self.tree_stars.configure(yscrollcommand=sb.set)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.refresh_list()

    def _create_card_results(self, parent):
        card = ttk.Frame(parent, style="Card.TFrame", padding=25)
        card.pack(fill=tk.BOTH, expand=True)
        top_bar = tk.Frame(card, bg=COLOR_CARD_BG)
        top_bar.pack(fill=tk.X, pady=(0, 20))
        ttk.Label(top_bar, text="Plan of Observation", style="CardTitle.TLabel").pack(side=tk.LEFT)
        ctrl_group = tk.Frame(top_bar, bg=COLOR_CARD_BG)
        ctrl_group.pack(side=tk.RIGHT)
        ttk.Label(ctrl_group, text="Date:", style="Normal.TLabel").pack(side=tk.LEFT, padx=(0, 10))
        self.entry_date = ttk.Entry(ctrl_group, style="Modern.TEntry", width=15)
        self.entry_date.insert(0, datetime.now().strftime("%Y-%m-%d"))
        self.entry_date.pack(side=tk.LEFT, padx=(0, 20))
        ttk.Button(ctrl_group, text="CALCULATE", style="Accent.TButton", command=self.calculate).pack(side=tk.LEFT)
        cols = ('time', 'name', 'phase', 'alt', 'status')
        headers = ['Time', 'Variable Star', 'Phase', 'Altitude (°)', 'Status']
        widths = [100, 150, 100, 100, 200]
        self.tree_res = ttk.Treeview(card, columns=cols, show='headings')
        for col, head, w in zip(cols, headers, widths):
            self.tree_res.heading(col, text=head, anchor="w")
            self.tree_res.column(col, width=w, anchor="w")
        self.tree_res.pack(fill=tk.BOTH, expand=True)
        for tag, (bg, fg) in self.tag_colors.items():
            self.tree_res.tag_configure(tag, background=bg, foreground=fg)

if __name__ == "__main__":
    app = BinaryStarPlanner()
    app.mainloop()
