import os
import sys
from PIL import Image, ImageDraw

def toggle_os_autostart(is_enabled):
    """Register or remove the application from OS Startup."""
    # Get the safe executable path
    exe_path = sys.executable if getattr(sys, 'frozen', False) else os.path.abspath(sys.argv[0])
    
    if os.name == 'nt':
        import winreg
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        app_name = "MacropadOLED"
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_ALL_ACCESS)
            if is_enabled:
                cmd = f'"{exe_path}" --minimized'
                winreg.SetValueEx(key, app_name, 0, winreg.REG_SZ, cmd)
            else:
                try: 
                    winreg.DeleteValue(key, app_name)
                except FileNotFoundError: 
                    pass
            winreg.CloseKey(key)
        except Exception: 
            pass

    elif os.name == 'posix':
        autostart_dir = os.path.expanduser("~/.config/autostart")
        desktop_file = os.path.join(autostart_dir, "macropad_oled.desktop")
        
        if is_enabled:
            os.makedirs(autostart_dir, exist_ok=True)
            python_bin = sys.executable 
            
            desktop_content = f"""[Desktop Entry]
Type=Application
Exec={python_bin} {exe_path} --minimized
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
Name=Macropad OLED
Comment=Macropad Background Service
"""
            try:
                with open(desktop_file, "w") as f:
                    f.write(desktop_content)
            except Exception: 
                pass
        else:
            if os.path.exists(desktop_file):
                os.remove(desktop_file)

def create_tray_icon_image():
    """Create a black square icon with a cyan center for the System Tray."""
    image = Image.new('RGB', (64, 64), color='black')
    draw = ImageDraw.Draw(image)
    draw.rectangle((16, 16, 48, 48), fill='#00ffff')
    return image
