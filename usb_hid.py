import hid
import time
import psutil
from config import VID, PID, USAGE_PAGE, USAGE

class HIDWorker:
    """Background thread to handle USB communication with Macropad."""
    
    def __init__(self, app_instance):
        self.app = app_instance

    def get_hid_path(self):
        """Find the exact USB interface path for the Macropad."""
        for device in hid.enumerate(VID, PID):
            if device['usage_page'] == USAGE_PAGE and device['usage'] == USAGE:
                return device['path']
        return None

    def run(self):
        """Main loop for USB reading and writing."""
        while self.app.running:
            path = self.get_hid_path()
            if not path:
                self.app.update_status("Status: Macropad Disconnected", "red")
                time.sleep(2)
                continue

            self.app.update_status("Status: Connected", "green")
            device = hid.device()
            
            try:
                device.open_path(path)
                device.set_nonblocking(1) 

                while self.app.running:
                    try:
                        res = device.read(32)
                        if res and len(res) >= 2 and res[0] == 0xAA:
                            self.app.macropad_layer = res[1]
                            self.app.last_update = 0 
                    except Exception:
                        break 

                    now = time.time()
                    if now - self.app.last_update >= 1.0:
                        gui_layer_key = str(self.app.macropad_layer + 1)
                        lines = self.app.layer_data.get(gui_layer_key, [""]*8)
                        
                        is_empty = all(line.strip() == "" for line in lines)

                        try:
                            if is_empty:
                                payload = [0x00, 0xFF] + [0] * 31
                                if device.write(payload) < 0: 
                                    break 
                            else:
                                cpu = psutil.cpu_percent()
                                ram_gb = psutil.virtual_memory().used / (1024 ** 3)

                                for i in range(8):
                                    line = lines[i] if i < len(lines) else ""
                                    formatted = line.replace("{cpu}", f"{cpu:.1f}").replace("{ram}", f"{ram_gb:.1f}")
                                    formatted = formatted.ljust(21, ' ')[:21]

                                    payload = [i] + list(formatted.encode('utf-8'))
                                    payload += [0] * (32 - len(payload))
                                    payload.insert(0, 0x00)
                                    
                                    if device.write(payload) < 0:
                                        raise Exception("Connection lost during transmission") 

                            self.app.last_update = now
                        except Exception:
                            break 

                    time.sleep(0.05)
            
            except Exception:
                pass
            
            self.app.update_status("Status: Macropad Disconnected", "red")
            try: 
                device.close() 
            except Exception: 
                pass
            time.sleep(2)
