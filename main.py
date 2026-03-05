import tkinter as tk
from tkinter import ttk
import threading
import time
import sys
import pystray
import config
import system_utils
from usb_hid import HIDWorker

class MacropadOLEDApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Macropad OLED Editor")
        self.root.geometry("400x520") 
        
        self.root.protocol('WM_DELETE_WINDOW', self.hide_to_tray)
        
        # Load configs and states
        self.layer_data = config.load_config()
        self.current_gui_layer = tk.StringVar(value="1")
        
        self.macropad_layer = 0
        self.last_update = 0
        self.running = True

        # Initialize UI elements
        self.setup_gui()
        
        # Start USB HID Thread
        hid_worker = HIDWorker(self)
        threading.Thread(target=hid_worker.run, daemon=True).start()

        if "--minimized" in sys.argv:
            self.root.after(0, self.hide_to_tray)

    def setup_gui(self):
        self.status_label = tk.Label(self.root, text="Status: Looking for Macropad...", fg="orange", font=("Arial", 10, "bold"))
        self.status_label.pack(pady=10)

        frame_top = tk.Frame(self.root)
        frame_top.pack(pady=5)
        tk.Label(frame_top, text="Edit OLED Text for Layer:").pack(side=tk.LEFT, padx=5)
        
        layer_combo = ttk.Combobox(frame_top, textvariable=self.current_gui_layer, values=[str(i) for i in range(1, 7)], state="readonly", width=5)
        layer_combo.pack(side=tk.LEFT)
        layer_combo.bind("<<ComboboxSelected>>", self.refresh_entries)

        tk.Label(self.root, text="Variables: {cpu} or {ram}", font=("Arial", 8, "italic"), fg="gray").pack()

        # OLED Text Area Frame
        self.text_frame = tk.Frame(self.root, bg="gray", bd=2, relief="sunken")
        self.text_frame.pack(pady=10)

        # 21-Character Ruler
        ruler = "123456789012345678901"
        tk.Label(self.text_frame, text=ruler, font=("Courier", 12), fg="#555555", bg="black").pack(fill="x")

        self.text_area = tk.Text(
            self.text_frame, height=8, width=21, 
            font=("Courier", 12, "bold"), bg="black", fg="#00ffff",
            insertbackground="white", wrap=tk.NONE 
        )
        self.text_area.pack(padx=5, pady=5)
        
        self.text_area.bind("<KeyPress>", self.on_keypress)
        self.text_area.bind("<KeyRelease>", self.on_keyrelease)

        # Buttons Frame
        btn_frame = tk.Frame(self.root)
        btn_frame.pack(pady=10)

        save_btn = tk.Button(btn_frame, text="Save & Update", command=self.save_config, bg="#0052cc", fg="white", font=("Arial", 10, "bold"))
        save_btn.grid(row=0, column=0, padx=5)

        clear_btn = tk.Button(btn_frame, text="Clear Layer", command=self.clear_layer, bg="#cc0000", fg="white", font=("Arial", 10, "bold"))
        clear_btn.grid(row=0, column=1, padx=5)

        # Autostart Checkbox
        self.autostart_var = tk.BooleanVar(value=self.layer_data.get("autostart", False))
        autostart_chk = tk.Checkbutton(
            self.root, text="Start Minimized (Auto-Run)", 
            variable=self.autostart_var, 
            command=self.toggle_autostart
        )
        autostart_chk.pack(pady=5)

        self.refresh_entries()

    def hide_to_tray(self):
        """Hide Tkinter GUI and show System Tray icon."""
        self.root.withdraw()
        
        # Right-click context menu
        menu = pystray.Menu(
            pystray.MenuItem('Open Settings', self.show_from_tray, default=True),
            pystray.MenuItem('Exit (Close Program)', self.quit_program)
        )
        
        self.tray_icon = pystray.Icon("Macropad", system_utils.create_tray_icon_image(), "Macropad OLED", menu)
        threading.Thread(target=self.tray_icon.run, daemon=True).start()

    def show_from_tray(self, icon, item):
        """Restore GUI from System Tray."""
        icon.stop()
        self.root.after(0, self.root.deiconify)

    def quit_program(self, icon=None, item=None):
        """Kill all threads and destroy app."""
        self.running = False
        if hasattr(self, 'tray_icon'):
            self.tray_icon.stop()
        self.root.after(0, self.root.destroy)

    def toggle_autostart(self):
        is_enabled = self.autostart_var.get()
        self.layer_data["autostart"] = is_enabled
        config.save_config(self.layer_data)
        system_utils.toggle_os_autostart(is_enabled)

    def on_keypress(self, event):
        """Block input if line exceeds 21 characters or text exceeds 8 lines."""
        if event.keysym in ('BackSpace', 'Delete', 'Left', 'Right', 'Up', 'Down', 'Home', 'End'):
            return
        if event.keysym == 'Return':
            content = self.text_area.get("1.0", "end-1c")
            if len(content.split('\n')) >= 8:
                return "break"
            return
        if event.char and event.char.isprintable():
            if self.text_area.tag_ranges(tk.SEL):
                return
            cursor_pos = self.text_area.index(tk.INSERT)
            line_idx = cursor_pos.split('.')[0]
            line_text = self.text_area.get(f"{line_idx}.0", f"{line_idx}.end")
            if len(line_text) >= 21:
                return "break"

    def on_keyrelease(self, event=None):
        """Force crop text when pasting large contents."""
        content = self.text_area.get("1.0", "end-1c")
        lines = content.split('\n')
        changed = False

        if len(lines) > 8:
            lines = lines[:8]
            changed = True

        for i in range(len(lines)):
            if len(lines[i]) > 21:
                lines[i] = lines[i][:21]
                changed = True

        if changed:
            cursor_pos = self.text_area.index(tk.INSERT)
            self.text_area.delete("1.0", tk.END)
            self.text_area.insert("1.0", "\n".join(lines))
            try:
                self.text_area.mark_set(tk.INSERT, cursor_pos)
            except Exception:
                pass

    def refresh_entries(self, event=None):
        """Refresh Text Area when switching layers in combobox."""
        layer = self.current_gui_layer.get()
        lines = self.layer_data.get(layer, [""]*8)
        full_text = "\n".join(lines)
        self.text_area.delete("1.0", tk.END)
        self.text_area.insert("1.0", full_text)

    def save_config(self):
        """Save current Text Area content to config and trigger USB update."""
        layer = self.current_gui_layer.get()
        content = self.text_area.get("1.0", "end-1c")
        raw_lines = content.split('\n')
        
        new_lines = []
        for i in range(8):
            if i < len(raw_lines):
                new_lines.append(raw_lines[i])
            else:
                new_lines.append("")
                
        self.layer_data[layer] = new_lines
        config.save_config(self.layer_data)
        
        self.last_update = 0
        self.update_status("Saved!", "green")
        self.root.after(2000, lambda: self.update_status("Status: Connected", "green"))

    def clear_layer(self):
        """Empty the text area and save."""
        self.text_area.delete("1.0", tk.END)
        self.save_config()

    def update_status(self, text, color):
        """Thread-safe way to update UI status label from background worker."""
        self.root.after(0, lambda: self.status_label.config(text=text, fg=color))


if __name__ == "__main__":
    root = tk.Tk()
    app = MacropadOLEDApp(root)
    root.mainloop()
