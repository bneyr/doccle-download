"""
Simple GUI launcher for Doccle Downloader
.pyw extension runs without console window on Windows
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import sys
import os
import logging
from pathlib import Path
import json

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from doccle_downloader import DoccleDownloader


class DoccleGUI:
    """Simple GUI for running the Doccle downloader"""

    def __init__(self, root):
        self.root = root
        self.root.title("Doccle Document Downloader")
        self.root.geometry("600x500")
        self.root.resizable(False, False)

        self.is_running = False
        self.setup_ui()
        self.load_config()

    def setup_ui(self):
        """Create the user interface"""
        # Title
        title_label = tk.Label(
            self.root,
            text="Doccle Document Downloader",
            font=("Arial", 16, "bold"),
            pady=10
        )
        title_label.pack()

        # Configuration frame
        config_frame = ttk.LabelFrame(self.root, text="Configuration", padding=10)
        config_frame.pack(fill="x", padx=10, pady=5)

        # Username
        tk.Label(config_frame, text="Username:").grid(row=0, column=0, sticky="w", pady=5)
        self.username_entry = tk.Entry(config_frame, width=40)
        self.username_entry.grid(row=0, column=1, pady=5, padx=5)

        # Password
        tk.Label(config_frame, text="Password:").grid(row=1, column=0, sticky="w", pady=5)
        self.password_entry = tk.Entry(config_frame, width=40, show="*")
        self.password_entry.grid(row=1, column=1, pady=5, padx=5)

        # Download folder
        tk.Label(config_frame, text="Download Folder:").grid(row=2, column=0, sticky="w", pady=5)
        self.folder_entry = tk.Entry(config_frame, width=40)
        self.folder_entry.grid(row=2, column=1, pady=5, padx=5)

        # Headless option
        self.headless_var = tk.BooleanVar()
        headless_check = tk.Checkbutton(
            config_frame,
            text="Run in background (headless mode)",
            variable=self.headless_var
        )
        headless_check.grid(row=3, column=0, columnspan=2, sticky="w", pady=5)

        # Only unread option
        self.only_unread_var = tk.BooleanVar()
        only_unread_check = tk.Checkbutton(
            config_frame,
            text="Download only unread documents",
            variable=self.only_unread_var
        )
        only_unread_check.grid(row=4, column=0, columnspan=2, sticky="w", pady=5)

        # Max documents
        tk.Label(config_frame, text="Max documents:").grid(row=5, column=0, sticky="w", pady=5)
        self.max_docs_entry = tk.Entry(config_frame, width=15)
        self.max_docs_entry.grid(row=5, column=1, pady=5, padx=5, sticky="w")
        tk.Label(config_frame, text="(leave empty for all)", font=("Arial", 8)).grid(row=5, column=1, pady=5, padx=(120, 0), sticky="w")

        # Buttons frame
        button_frame = tk.Frame(self.root)
        button_frame.pack(pady=10)

        # Save config button
        self.save_btn = tk.Button(
            button_frame,
            text="Save Settings",
            command=self.save_config,
            bg="#4CAF50",
            fg="white",
            padx=10,
            pady=5
        )
        self.save_btn.grid(row=0, column=0, padx=5)

        # Download button
        self.download_btn = tk.Button(
            button_frame,
            text="Download Documents",
            command=self.start_download,
            bg="#2196F3",
            fg="white",
            padx=10,
            pady=5,
            font=("Arial", 10, "bold")
        )
        self.download_btn.grid(row=0, column=1, padx=5)

        # Log frame
        log_frame = ttk.LabelFrame(self.root, text="Log", padding=5)
        log_frame.pack(fill="both", expand=True, padx=10, pady=5)

        # Log text area
        self.log_text = scrolledtext.ScrolledText(
            log_frame,
            height=12,
            state='disabled',
            wrap='word'
        )
        self.log_text.pack(fill="both", expand=True)

        # Status bar
        self.status_label = tk.Label(
            self.root,
            text="Ready",
            bd=1,
            relief=tk.SUNKEN,
            anchor=tk.W
        )
        self.status_label.pack(side=tk.BOTTOM, fill=tk.X)

    def load_config(self):
        """Load configuration from config.json"""
        try:
            if os.path.exists("config.json"):
                with open("config.json", 'r') as f:
                    config = json.load(f)
                    self.username_entry.insert(0, config.get('username', ''))
                    self.password_entry.insert(0, config.get('password', ''))
                    self.folder_entry.insert(0, config.get('download_folder', ''))
                    self.headless_var.set(config.get('headless', False))
                    self.only_unread_var.set(config.get('only_unread', False))
                    max_docs = config.get('max_documents')
                    if max_docs:
                        self.max_docs_entry.insert(0, str(max_docs))
        except Exception as e:
            self.log(f"Could not load config: {str(e)}")

    def save_config(self):
        """Save configuration to config.json"""
        try:
            # Parse max_documents
            max_docs = None
            max_docs_str = self.max_docs_entry.get().strip()
            if max_docs_str:
                try:
                    max_docs = int(max_docs_str)
                    if max_docs <= 0:
                        max_docs = None
                except ValueError:
                    max_docs = None

            # Load existing config to preserve wait_timeout and other settings
            existing_config = {}
            try:
                if os.path.exists("config.json"):
                    with open("config.json", 'r') as f:
                        existing_config = json.load(f)
            except:
                pass

            config = {
                "username": self.username_entry.get(),
                "password": self.password_entry.get(),
                "download_folder": self.folder_entry.get(),
                "wait_timeout": existing_config.get("wait_timeout", 20),
                "headless": self.headless_var.get(),
                "only_unread": self.only_unread_var.get(),
                "max_documents": max_docs
            }

            with open("config.json", 'w') as f:
                json.dump(config, f, indent=4)

            self.log("✓ Settings saved successfully")
            messagebox.showinfo("Success", "Settings saved successfully!")

        except Exception as e:
            self.log(f"✗ Error saving settings: {str(e)}")
            messagebox.showerror("Error", f"Could not save settings: {str(e)}")

    def log(self, message):
        """Add message to log window"""
        self.log_text.configure(state='normal')
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.log_text.configure(state='disabled')

    def set_status(self, message):
        """Update status bar"""
        self.status_label.config(text=message)

    def start_download(self):
        """Start the download process in a separate thread"""
        if self.is_running:
            messagebox.showwarning("Warning", "Download is already running!")
            return

        # Validate inputs
        if not self.username_entry.get() or not self.password_entry.get():
            messagebox.showerror("Error", "Please enter username and password!")
            return

        # Save config first
        self.save_config()

        # Clear log
        self.log_text.configure(state='normal')
        self.log_text.delete(1.0, tk.END)
        self.log_text.configure(state='disabled')

        # Disable button and start download
        self.is_running = True
        self.download_btn.config(state='disabled', text="Downloading...")
        self.set_status("Downloading...")

        # Run in separate thread to not freeze GUI
        thread = threading.Thread(target=self.run_download)
        thread.daemon = True
        thread.start()

    def run_download(self):
        """Run the download process"""
        try:
            self.log("Starting Doccle Downloader...")
            self.log("-" * 60)

            # Create custom logger that writes to GUI
            downloader = DoccleDownloader()

            # Redirect logger to GUI
            import logging
            gui_handler = GUILogHandler(self)
            downloader.logger.addHandler(gui_handler)

            downloader.run()

            self.log("-" * 60)
            self.log("✓ Download completed!")
            self.set_status("Download completed successfully")

            messagebox.showinfo(
                "Success",
                f"Documents downloaded to:\n{downloader.config['download_folder']}"
            )

        except Exception as e:
            self.log(f"✗ Error: {str(e)}")
            self.set_status("Error occurred")
            messagebox.showerror("Error", f"Download failed:\n{str(e)}")

        finally:
            self.is_running = False
            self.download_btn.config(state='normal', text="Download Documents")


class GUILogHandler(logging.Handler):
    """Custom logging handler that writes to GUI"""

    def __init__(self, gui):
        super().__init__()
        self.gui = gui

    def emit(self, record):
        msg = self.format(record)
        # Schedule GUI update in main thread
        self.gui.root.after(0, lambda: self.gui.log(msg))


def main():
    """Entry point for GUI"""
    root = tk.Tk()
    app = DoccleGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
