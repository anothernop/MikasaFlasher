import subprocess
import os
import sys
import time
import tkinter as tk
from tkinter import filedialog, messagebox
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from ttkbootstrap.scrolled import ScrolledText

# Default path to ADB & Fastboot on Windows
PLATFORM_TOOLS_PATH = r"C:\platform-tools"
ADB_PATH = os.path.join(PLATFORM_TOOLS_PATH, "adb.exe")
FASTBOOT_PATH = os.path.join(PLATFORM_TOOLS_PATH, "fastboot.exe")

class MikasaFlasher:
    def __init__(self, root):
        self.root = root
        self.root.title("Mikasa Flasher")
        self.root.geometry("700x600")
        self.root.resizable(False, False)
        
        # Variables
        self.gsi_path = tk.StringVar()
        self.vbmeta_path = tk.StringVar()
        self.slot = tk.StringVar(value="A")
        
        self.setup_ui()
    
    def setup_ui(self):
        # Apply modern theme
        style = ttk.Style("flatly")  # Modern theme: flatly, darkly, litera, etc.
        style.configure("TButton", font=("Helvetica", 10))
        style.configure("TLabel", font=("Helvetica", 10))
        style.configure("TRadiobutton", font=("Helvetica", 10))
        
        # Main frame
        main_frame = ttk.Frame(self.root, padding=20)
        main_frame.pack(fill=BOTH, expand=True)
        
        # Header
        ttk.Label(main_frame, text="Mikasa Flasher", font=("Helvetica", 16, "bold"), bootstyle=PRIMARY).pack(pady=(0, 20))
        
        # GSI file selection
        gsi_frame = ttk.Labelframe(main_frame, text="GSI Image", padding=10, bootstyle=INFO)
        gsi_frame.pack(fill=X, pady=5)
        ttk.Entry(gsi_frame, textvariable=self.gsi_path, width=50, bootstyle=SECONDARY).pack(side=LEFT, padx=(0, 10))
        ttk.Button(gsi_frame, text="Browse", command=self.browse_gsi, bootstyle=(INFO, OUTLINE)).pack(side=LEFT)
        
        # vbmeta file selection
        vbmeta_frame = ttk.Labelframe(main_frame, text="vbmeta Image (Optional)", padding=10, bootstyle=INFO)
        vbmeta_frame.pack(fill=X, pady=5)
        ttk.Entry(vbmeta_frame, textvariable=self.vbmeta_path, width=50, bootstyle=SECONDARY).pack(side=LEFT, padx=(0, 10))
        ttk.Button(vbmeta_frame, text="Browse", command=self.browse_vbmeta, bootstyle=(INFO, OUTLINE)).pack(side=LEFT)
        
        # Slot selection
        slot_frame = ttk.Labelframe(main_frame, text="Select Slot", padding=10, bootstyle=INFO)
        slot_frame.pack(fill=X, pady=5)
        ttk.Radiobutton(slot_frame, text="Slot A", value="A", variable=self.slot, bootstyle=PRIMARY).pack(side=LEFT, padx=10)
        ttk.Radiobutton(slot_frame, text="Slot B", value="B", variable=self.slot, bootstyle=PRIMARY).pack(side=LEFT)
        
        # Flash button
        ttk.Button(main_frame, text="Flash GSI", command=self.flash_gsi, bootstyle=(SUCCESS, SOLID), width=20).pack(pady=20)
        
        # Log output
        log_frame = ttk.Labelframe(main_frame, text="Log Output", padding=10, bootstyle=INFO)
        log_frame.pack(fill=BOTH, expand=True, pady=5)
        self.log_text = ScrolledText(log_frame, height=15, autohide=True, bootstyle=SECONDARY)
        self.log_text.pack(fill=BOTH, expand=True)
        
        # Warning label
        ttk.Label(main_frame, text="Warning: Flashing may erase data. Backup first!", bootstyle=(WARNING, ITALIC)).pack(pady=10)
    
    def log(self, message):
        """Add message to log output."""
        self.log_text.insert(tk.END, f"[Mikasa Flasher] {message}\n")
        self.log_text.see(tk.END)
        self.root.update()
    
    def run_command(self, cmd):
        """Run a shell command and return True if successful."""
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, shell=True, check=True)
            self.log(f"Command: {' '.join(cmd)}")
            self.log(f"Output: {result.stdout}")
            return True
        except subprocess.CalledProcessError as e:
            self.log(f"Error: {e.stderr}")
            return False
        except Exception as e:
            self.log(f"Exception: {str(e)}")
            return False
    
    def browse_gsi(self):
        """Browse for GSI image file."""
        file = filedialog.askopenfilename(title="Select GSI Image", filetypes=[("IMG files", "*.img")])
        if file:
            self.gsi_path.set(file)
    
    def browse_vbmeta(self):
        """Browse for vbmeta image file."""
        file = filedialog.askopenfilename(title="Select vbmeta Image", filetypes=[("IMG files", "*.img")])
        if file:
            self.vbmeta_path.set(file)
    
    def check_super_partition(self):
        """Check if the device uses a super partition."""
        try:
            result = subprocess.run([FASTBOOT_PATH, "getvar", "is-logical:system"], capture_output=True, text=True, shell=True)
            output = result.stdout.lower()
            self.log(f"Checking super partition: {output}")
            return "is-logical:system: yes" in output or "true" in output
        except:
            self.log("Warning: Could not determine super partition status. Assuming non-super partition.")
            return False
    
    def flash_gsi(self):
        """Flash GSI to the specified A/B slot, with super partition and vbmeta support."""
        if not self.gsi_path.get():
            messagebox.showerror("Error", "Please select a GSI file!")
            return
        
        if not os.path.exists(self.gsi_path.get()):
            messagebox.showerror("Error", "GSI file not found!")
            return
        
        if self.vbmeta_path.get() and not os.path.exists(self.vbmeta_path.get()):
            messagebox.showerror("Error", "vbmeta file not found!")
            return
        
        if not messagebox.askyesno("Confirm", f"Flash GSI to slot {self.slot.get()}?\nThis will erase data on the slot. Backup first!"):
            return
        
        # Verify ADB and Fastboot
        if not os.path.exists(ADB_PATH):
            messagebox.showerror("Error", f"ADB not found at {ADB_PATH}. Install Android Platform Tools at C:\\platform-tools.")
            return
        if not os.path.exists(FASTBOOT_PATH):
            messagebox.showerror("Error", f"Fastboot not found at {FASTBOOT_PATH}. Install Android Platform Tools at C:\\platform-tools.")
            return
        
        self.log(f"Starting GSI flash to slot {self.slot.get()}")
        self.log(f"GSI file: {self.gsi_path.get()}")
        if self.vbmeta_path.get():
            self.log(f"vbmeta file: {self.vbmeta_path.get()}")
        
        # Step 1: Reboot to bootloader
        self.log("1. Rebooting to fastboot...")
        if not self.run_command([ADB_PATH, "reboot", "bootloader"]):
            messagebox.showerror("Error", "Failed to reboot to fastboot. Ensure device is connected and USB Debugging is enabled.")
            return
        
        # Wait for device to enter fastboot
        time.sleep(3)
        
        # Step 2: Check fastboot devices
        self.log("2. Checking fastboot devices...")
        if not self.run_command([FASTBOOT_PATH, "devices"]):
            messagebox.showerror("Error", "No device detected in fastboot mode!")
            return
        
        # Step 3: Flash vbmeta if provided
        if self.vbmeta_path.get():
            self.log("3. Flashing vbmeta to disable verity & verification...")
            if not self.run_command([FASTBOOT_PATH, "--disable-verity", "--disable-verification", "flash", "vbmeta", self.vbmeta_path.get()]):
                self.log("Warning: Failed to flash vbmeta. Continuing with flashing process...")
        else:
            self.log("3. No vbmeta file provided. Skipping vbmeta flash...")
        
        # Step 4: Check for super partition
        is_super = self.check_super_partition()
        slot_suffix = "_a" if self.slot.get() == "A" else "_b"
        
        if is_super:
            # Super partition device
            self.log("4. Detected super partition. Switching to fastbootd...")
            if not self.run_command([FASTBOOT_PATH, "reboot", "fastboot"]):
                messagebox.showerror("Error", "Failed to reboot to fastbootd mode!")
                return
            
            # Wait for fastbootd
            time.sleep(5)
            
            # Step 5: Delete logical partitions
            self.log(f"5. Deleting logical partitions for slot {self.slot.get()}...")
            for partition in ["system", "product"]:
                self.run_command([FASTBOOT_PATH, "delete-logical-partition", f"{partition}{slot_suffix}"])
            
            # Step 6: Create new system partition
            self.log(f"6. Creating system partition for slot {self.slot.get()}...")
            if not self.run_command([FASTBOOT_PATH, "create-logical-partition", f"system{slot_suffix}", "0"]):
                messagebox.showerror("Error", f"Failed to create system{slot_suffix} partition!")
                return
            
            # Step 7: Flash GSI
            self.log("7. Flashing GSI...")
            if not self.run_command([FASTBOOT_PATH, "flash", f"system{slot_suffix}", self.gsi_path.get()]):
                messagebox.showerror("Error", "Failed to flash GSI!")
                return
        else:
            # Non-super partition device
            self.log("4. No super partition detected. Proceeding with standard A/B flashing...")
            
            # Step 5: Set active slot
            self.log(f"5. Setting active slot to {self.slot.get()}...")
            if not self.run_command([FASTBOOT_PATH, "set_active", self.slot.get().lower()]):
                messagebox.showerror("Error", f"Failed to set active slot {self.slot.get()}!")
                return
            
            # Step 6: Erase system partition
            self.log("6. Erasing system partition...")
            if not self.run_command([FASTBOOT_PATH, "erase", f"system{slot_suffix}"]):
                messagebox.showerror("Error", "Failed to erase system partition!")
                return
            
            # Step 7: Flash GSI
            self.log("7. Flashing GSI...")
            if not self.run_command([FASTBOOT_PATH, "flash", f"system{slot_suffix}", self.gsi_path.get()]):
                messagebox.showerror("Error", "Failed to flash GSI!")
                return
        
        # Step 8: Reboot
        self.log("8. Rebooting device...")
        if not self.run_command([FASTBOOT_PATH, "reboot"]):
            self.log("Warning: Reboot command failed, but flashing may have succeeded.")
        
        self.log("=== Flash completed! Reboot device and check if it boots. ===")
        self.log("Note: If bootloop occurs, try wiping data via recovery.")
        messagebox.showinfo("Success", "Flash completed! Check if device boots. If bootloop occurs, wipe data via recovery.")
    
    def on_closing(self):
        """Handle window close."""
        self.root.destroy()
        sys.exit()

if __name__ == "__main__":
    root = ttk.Window(themename="flatly")
    app = MikasaFlasher(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()
