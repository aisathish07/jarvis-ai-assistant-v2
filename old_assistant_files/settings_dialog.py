# settings_dialog.py - Settings configuration window
import os
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox

import customtkinter as ctk

ctk.set_appearance_mode("dark")


class SettingsDialog:
    """Settings configuration dialog for Jarvis Assistant"""

    def __init__(self, parent=None):
        self.window = ctk.CTkToplevel(parent) if parent else ctk.CTk()
        self.window.title("Jarvis Settings - MSI Thin 15 B13UC")
        self.window.geometry("700x600")
        self.window.resizable(False, False)

        # Make modal if parent exists
        if parent:
            self.window.transient(parent)
            self.window.grab_set()

        # Settings dict
        self.settings = self.load_settings()

        # Create UI
        self.create_ui()

    def load_settings(self) -> dict:
        """Load settings from .env and config"""
        settings = {
            "gemini_api_key": os.getenv("GEMINI_API_KEY", ""),
            "elevenlabs_api_key": os.getenv("ELEVENLABS_API_KEY", ""),
            "weather_api_key": os.getenv("OPENWEATHERMAP_API_KEY", ""),
            "news_api_key": os.getenv("NEWSAPI_API_KEY", ""),
            "local_only": os.getenv("LOCAL_ONLY", "false").lower() == "true",
            "web_agent_mode": os.getenv("WEB_AGENT_MODE", "balanced"),
            "web_agent_enabled": os.getenv("WEB_AGENT_ENABLED", "true").lower() == "true",
            "whisper_model": os.getenv("WHISPER_MODEL_SIZE", "base"),
            "tts_priority": os.getenv("TTS_PRIORITY", "elevenlabs,gtts,piper"),
            "auto_start": self.check_auto_start(),
            "hotkey": "ctrl+space",
            "theme": "dark",
        }
        return settings

    def check_auto_start(self) -> bool:
        """Check if auto-start is enabled"""
        startup_folder = (
            Path(os.getenv("APPDATA"))
            / "Microsoft"
            / "Windows"
            / "Start Menu"
            / "Programs"
            / "Startup"
        )
        shortcut = startup_folder / "Jarvis.lnk"
        return shortcut.exists()

    def create_ui(self):
        """Create settings UI"""
        # Tabbed interface
        tabview = ctk.CTkTabview(self.window)
        tabview.pack(fill="both", expand=True, padx=10, pady=10)

        # Create tabs
        tab_api = tabview.add("API Keys")
        tab_performance = tabview.add("Performance")
        tab_behavior = tabview.add("Behavior")
        tab_advanced = tabview.add("Advanced")

        # === API KEYS TAB ===
        self.create_api_tab(tab_api)

        # === PERFORMANCE TAB ===
        self.create_performance_tab(tab_performance)

        # === BEHAVIOR TAB ===
        self.create_behavior_tab(tab_behavior)

        # === ADVANCED TAB ===
        self.create_advanced_tab(tab_advanced)

        # Bottom buttons
        button_frame = ctk.CTkFrame(self.window)
        button_frame.pack(fill="x", padx=10, pady=(0, 10))

        ctk.CTkButton(
            button_frame,
            text="💾 Save & Apply",
            command=self.save_settings,
            fg_color="#00ff88",
            text_color="black",
            width=150,
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            button_frame,
            text="🔄 Reset to Default",
            command=self.reset_settings,
            fg_color="orange",
            width=150,
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            button_frame, text="❌ Cancel", command=self.window.destroy, fg_color="gray", width=100
        ).pack(side="right", padx=5)

    def create_api_tab(self, parent):
        """Create API keys tab"""
        frame = ctk.CTkScrollableFrame(parent)
        frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Info label
        ctk.CTkLabel(
            frame, text="🔑 Configure API Keys for External Services", font=("Arial", 14, "bold")
        ).pack(pady=(0, 20))

        # Gemini API Key (Required)
        ctk.CTkLabel(frame, text="Gemini API Key (Required)", anchor="w").pack(
            fill="x", pady=(0, 5)
        )
        self.gemini_entry = ctk.CTkEntry(frame, placeholder_text="Get from ai.google.dev")
        self.gemini_entry.pack(fill="x", pady=(0, 5))
        self.gemini_entry.insert(0, self.settings["gemini_api_key"])

        ctk.CTkButton(
            frame,
            text="Get Gemini Key",
            command=lambda: os.system("start https://ai.google.dev"),
            width=120,
            height=25,
        ).pack(anchor="w", pady=(0, 15))

        # ElevenLabs API Key (Optional)
        ctk.CTkLabel(frame, text="ElevenLabs API Key (Optional - Better TTS)", anchor="w").pack(
            fill="x", pady=(0, 5)
        )
        self.elevenlabs_entry = ctk.CTkEntry(frame, placeholder_text="Get from elevenlabs.io")
        self.elevenlabs_entry.pack(fill="x", pady=(0, 5))
        self.elevenlabs_entry.insert(0, self.settings["elevenlabs_api_key"])

        ctk.CTkButton(
            frame,
            text="Get ElevenLabs Key",
            command=lambda: os.system("start https://elevenlabs.io"),
            width=150,
            height=25,
        ).pack(anchor="w", pady=(0, 15))

        # Weather API Key (Optional)
        ctk.CTkLabel(frame, text="OpenWeatherMap API Key (Optional)", anchor="w").pack(
            fill="x", pady=(0, 5)
        )
        self.weather_entry = ctk.CTkEntry(frame, placeholder_text="Get from openweathermap.org")
        self.weather_entry.pack(fill="x", pady=(0, 15))
        self.weather_entry.insert(0, self.settings["weather_api_key"])

        # News API Key (Optional)
        ctk.CTkLabel(frame, text="NewsAPI Key (Optional)", anchor="w").pack(fill="x", pady=(0, 5))
        self.news_entry = ctk.CTkEntry(frame, placeholder_text="Get from newsapi.org")
        self.news_entry.pack(fill="x", pady=(0, 15))
        self.news_entry.insert(0, self.settings["news_api_key"])

        # Local Only Mode
        self.local_only_var = tk.BooleanVar(value=self.settings["local_only"])
        ctk.CTkCheckBox(
            frame, text="🔒 Local Only Mode (No external API calls)", variable=self.local_only_var
        ).pack(anchor="w", pady=10)

    def create_performance_tab(self, parent):
        """Create performance settings tab"""
        frame = ctk.CTkScrollableFrame(parent)
        frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Info
        ctk.CTkLabel(
            frame,
            text="⚡ Optimized for MSI Thin 15 B13UC (16GB RAM, RTX 3050)",
            font=("Arial", 14, "bold"),
        ).pack(pady=(0, 20))

        # Web Agent Mode
        ctk.CTkLabel(
            frame, text="Web Agent Performance Mode:", anchor="w", font=("Arial", 12, "bold")
        ).pack(fill="x", pady=(0, 5))

        mode_frame = ctk.CTkFrame(frame)
        mode_frame.pack(fill="x", pady=(0, 15))

        self.web_mode_var = tk.StringVar(value=self.settings["web_agent_mode"])

        ctk.CTkRadioButton(
            mode_frame,
            text="🪶 Lightweight (300MB RAM, basic features)",
            variable=self.web_mode_var,
            value="lightweight",
        ).pack(anchor="w", padx=10, pady=5)

        ctk.CTkRadioButton(
            mode_frame,
            text="⚖️ Balanced (600MB RAM, recommended)",
            variable=self.web_mode_var,
            value="balanced",
        ).pack(anchor="w", padx=10, pady=5)

        ctk.CTkRadioButton(
            mode_frame,
            text="🚀 Full Power (1GB RAM, all features)",
            variable=self.web_mode_var,
            value="full",
        ).pack(anchor="w", padx=10, pady=5)

        # Whisper Model
        ctk.CTkLabel(
            frame, text="Speech Recognition Model:", anchor="w", font=("Arial", 12, "bold")
        ).pack(fill="x", pady=(15, 5))

        whisper_frame = ctk.CTkFrame(frame)
        whisper_frame.pack(fill="x", pady=(0, 15))

        self.whisper_var = tk.StringVar(value=self.settings["whisper_model"])

        models = [
            ("tiny", "🏃 Tiny (39M, fastest, lower accuracy)"),
            ("base", "⚡ Base (74M, balanced - recommended)"),
            ("small", "🎯 Small (244M, better accuracy)"),
            ("medium", "🔥 Medium (769M, high accuracy, slower)"),
        ]

        for value, text in models:
            ctk.CTkRadioButton(
                whisper_frame, text=text, variable=self.whisper_var, value=value
            ).pack(anchor="w", padx=10, pady=3)

        # Web Agent Toggle
        self.web_enabled_var = tk.BooleanVar(value=self.settings["web_agent_enabled"])
        ctk.CTkCheckBox(
            frame, text="🌐 Enable Web Agent (browser automation)", variable=self.web_enabled_var
        ).pack(anchor="w", pady=10)

    def create_behavior_tab(self, parent):
        """Create behavior settings tab"""
        frame = ctk.CTkScrollableFrame(parent)
        frame.pack(fill="both", expand=True, padx=10, pady=10)

        ctk.CTkLabel(frame, text="🎭 Assistant Behavior Settings", font=("Arial", 14, "bold")).pack(
            pady=(0, 20)
        )

        # TTS Priority
        ctk.CTkLabel(
            frame, text="Text-to-Speech Priority:", anchor="w", font=("Arial", 12, "bold")
        ).pack(fill="x", pady=(0, 5))

        tts_frame = ctk.CTkFrame(frame)
        tts_frame.pack(fill="x", pady=(0, 15))

        ctk.CTkLabel(tts_frame, text="Drag to reorder (highest priority first):", anchor="w").pack(
            fill="x", padx=10, pady=5
        )

        # Simple TTS selection (not draggable in this version)
        self.tts_vars = {
            "elevenlabs": tk.BooleanVar(value="elevenlabs" in self.settings["tts_priority"]),
            "gtts": tk.BooleanVar(value="gtts" in self.settings["tts_priority"]),
            "piper": tk.BooleanVar(value="piper" in self.settings["tts_priority"]),
        }

        ctk.CTkCheckBox(
            tts_frame,
            text="🎤 ElevenLabs (Best quality, requires API key)",
            variable=self.tts_vars["elevenlabs"],
        ).pack(anchor="w", padx=10, pady=3)
        ctk.CTkCheckBox(
            tts_frame, text="🌐 Google TTS (Online, free)", variable=self.tts_vars["gtts"]
        ).pack(anchor="w", padx=10, pady=3)
        ctk.CTkCheckBox(
            tts_frame, text="🔧 Piper (Offline, local)", variable=self.tts_vars["piper"]
        ).pack(anchor="w", padx=10, pady=3)

        # Auto-start
        self.auto_start_var = tk.BooleanVar(value=self.settings["auto_start"])
        ctk.CTkCheckBox(
            frame,
            text="🚀 Start Jarvis automatically when Windows starts",
            variable=self.auto_start_var,
        ).pack(anchor="w", pady=(15, 5))

        # Hotkey (read-only for now)
        ctk.CTkLabel(frame, text="Global Hotkey:", anchor="w", font=("Arial", 12, "bold")).pack(
            fill="x", pady=(15, 5)
        )
        ctk.CTkLabel(
            frame, text="Ctrl+Space (click floating orb to change)", anchor="w", text_color="gray"
        ).pack(fill="x", pady=(0, 15))

    def create_advanced_tab(self, parent):
        """Create advanced settings tab"""
        frame = ctk.CTkScrollableFrame(parent)
        frame.pack(fill="both", expand=True, padx=10, pady=10)

        ctk.CTkLabel(frame, text="⚙️ Advanced Configuration", font=("Arial", 14, "bold")).pack(
            pady=(0, 20)
        )

        # System Info
        info_frame = ctk.CTkFrame(frame)
        info_frame.pack(fill="x", pady=(0, 15))

        ctk.CTkLabel(info_frame, text="System Information:", font=("Arial", 12, "bold")).pack(
            anchor="w", padx=10, pady=(10, 5)
        )

        import psutil

        ram_gb = psutil.virtual_memory().total / (1024**3)
        cpu_count = psutil.cpu_count()

        info_text = f"""
        RAM: {ram_gb:.1f} GB
        CPU Cores: {cpu_count}
        GPU: NVIDIA RTX 3050 4GB
        Platform: {os.name.upper()}
        Python: {os.sys.version.split()[0]}
        """

        ctk.CTkLabel(info_frame, text=info_text, anchor="w", justify="left").pack(
            anchor="w", padx=20, pady=(0, 10)
        )

        # Cache Management
        ctk.CTkLabel(frame, text="Cache Management:", font=("Arial", 12, "bold")).pack(
            fill="x", pady=(15, 5)
        )

        cache_frame = ctk.CTkFrame(frame)
        cache_frame.pack(fill="x", pady=(0, 15))

        ctk.CTkButton(
            cache_frame, text="🗑️ Clear App Cache", command=self.clear_app_cache, width=180
        ).pack(side="left", padx=10, pady=10)

        ctk.CTkButton(
            cache_frame, text="🗑️ Clear Web Cache", command=self.clear_web_cache, width=180
        ).pack(side="left", padx=10, pady=10)

        # Logs
        ctk.CTkLabel(frame, text="Logs & Diagnostics:", font=("Arial", 12, "bold")).pack(
            fill="x", pady=(15, 5)
        )

        log_frame = ctk.CTkFrame(frame)
        log_frame.pack(fill="x", pady=(0, 15))

        ctk.CTkButton(
            log_frame, text="📄 Open Log File", command=self.open_log_file, width=180
        ).pack(side="left", padx=10, pady=10)

        ctk.CTkButton(
            log_frame, text="📊 Show Statistics", command=self.show_statistics, width=180
        ).pack(side="left", padx=10, pady=10)

        # Database
        ctk.CTkLabel(frame, text="Database:", font=("Arial", 12, "bold")).pack(
            fill="x", pady=(15, 5)
        )

        db_frame = ctk.CTkFrame(frame)
        db_frame.pack(fill="x", pady=(0, 15))

        ctk.CTkButton(
            db_frame,
            text="💾 Backup Database",
            command=self.backup_database,
            width=180,
            fg_color="#0088ff",
        ).pack(side="left", padx=10, pady=10)

        ctk.CTkButton(
            db_frame, text="🔄 Restore Database", command=self.restore_database, width=180
        ).pack(side="left", padx=10, pady=10)

    def save_settings(self):
        """Save all settings"""
        try:
            # Update .env file
            env_path = Path(".env")
            env_content = []

            if env_path.exists():
                with open(env_path, "r") as f:
                    env_content = f.readlines()

            # Update settings
            settings_map = {
                "GEMINI_API_KEY": self.gemini_entry.get(),
                "ELEVENLABS_API_KEY": self.elevenlabs_entry.get(),
                "OPENWEATHERMAP_API_KEY": self.weather_entry.get(),
                "NEWSAPI_API_KEY": self.news_entry.get(),
                "LOCAL_ONLY": str(self.local_only_var.get()).lower(),
                "WEB_AGENT_MODE": self.web_mode_var.get(),
                "WEB_AGENT_ENABLED": str(self.web_enabled_var.get()).lower(),
                "WHISPER_MODEL_SIZE": self.whisper_var.get(),
            }

            # Build TTS priority
            tts_priority = [k for k, v in self.tts_vars.items() if v.get()]
            settings_map["TTS_PRIORITY"] = f'["{tts_priority}"]'

            # Write .env
            new_content = []
            for line in env_content:
                key = line.split("=")[0].strip()
                if key in settings_map:
                    new_content.append(f"{key}={settings_map[key]}\n")
                    del settings_map[key]
                else:
                    new_content.append(line)

            # Add remaining settings
            for key, value in settings_map.items():
                new_content.append(f"{key}={value}\n")

            with open(env_path, "w") as f:
                f.writelines(new_content)

            # Handle auto-start
            self.set_auto_start(self.auto_start_var.get())

            messagebox.showinfo(
                "Success",
                "Settings saved successfully!\n\nRestart Jarvis for changes to take effect.",
            )

            self.window.destroy()

        except Exception as e:
            messagebox.showerror("Error", f"Failed to save settings:\n{e}")

    def reset_settings(self):
        """Reset to default settings"""
        if messagebox.askyesno("Confirm Reset", "Reset all settings to default values?"):
            # Reset UI elements
            self.gemini_entry.delete(0, tk.END)
            self.elevenlabs_entry.delete(0, tk.END)
            self.weather_entry.delete(0, tk.END)
            self.news_entry.delete(0, tk.END)

            self.local_only_var.set(False)
            self.web_mode_var.set("balanced")
            self.whisper_var.set("base")
            self.web_enabled_var.set(True)

            for var in self.tts_vars.values():
                var.set(True)

    def set_auto_start(self, enabled: bool):
        """Configure auto-start"""
        try:
            import winshell
            from win32com.client import Dispatch

            startup_folder = Path(winshell.startup())
            shortcut_path = startup_folder / "Jarvis.lnk"
            exe_path = Path(os.sys.executable).parent / "Jarvis.exe"

            if enabled:
                shell = Dispatch("WScript.Shell")
                shortcut = shell.CreateShortCut(str(shortcut_path))
                shortcut.Targetpath = str(exe_path)
                shortcut.WorkingDirectory = str(exe_path.parent)
                shortcut.IconLocation = str(exe_path)
                shortcut.save()
            else:
                if shortcut_path.exists():
                    shortcut_path.unlink()
        except Exception as e:
            messagebox.showwarning("Auto-start", f"Could not configure auto-start:\n{e}")

    def clear_app_cache(self):
        """Clear application cache"""
        try:
            cache_dir = Path("cache")
            if cache_dir.exists():
                import shutil

                shutil.rmtree(cache_dir)
                cache_dir.mkdir()
            messagebox.showinfo("Success", "App cache cleared!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to clear cache:\n{e}")

    def clear_web_cache(self):
        """Clear web agent cache"""
        try:
            # Playwright cache
            import subprocess

            subprocess.run(["playwright", "uninstall"], check=False)
            subprocess.run(["playwright", "install", "chromium"], check=False)
            messagebox.showinfo("Success", "Web cache cleared and browser reinstalled!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to clear web cache:\n{e}")

    def open_log_file(self):
        """Open log file"""
        log_path = Path("logs/assistant.log")
        if log_path.exists():
            os.startfile(log_path)
        else:
            messagebox.showinfo("Info", "No log file found yet.")

    def show_statistics(self):
        """Show usage statistics"""
        # TODO: Implement stats viewer
        messagebox.showinfo("Statistics", "Statistics feature coming soon!")

    def backup_database(self):
        """Backup database"""
        try:
            import shutil
            from datetime import datetime

            db_path = Path("assistant_memory.db")
            if not db_path.exists():
                messagebox.showinfo("Info", "No database found to backup.")
                return

            backup_name = f"assistant_memory_backup_{datetime.now():%Y%m%d_%H%M%S}.db"
            backup_path = filedialog.asksaveasfilename(
                defaultextension=".db",
                filetypes=[("Database files", "*.db")],
                initialfile=backup_name,
            )

            if backup_path:
                shutil.copy2(db_path, backup_path)
                messagebox.showinfo("Success", f"Database backed up to:\n{backup_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Backup failed:\n{e}")

    def restore_database(self):
        """Restore database from backup"""
        try:
            backup_path = filedialog.askopenfilename(
                filetypes=[("Database files", "*.db")], title="Select backup file"
            )

            if backup_path and messagebox.askyesno(
                "Confirm Restore", "This will replace your current database.\n\nContinue?"
            ):
                import shutil

                db_path = Path("assistant_memory.db")
                shutil.copy2(backup_path, db_path)
                messagebox.showinfo("Success", "Database restored!\n\nRestart Jarvis.")
        except Exception as e:
            messagebox.showerror("Error", f"Restore failed:\n{e}")

    def show(self):
        """Show dialog"""
        self.window.mainloop()


if __name__ == "__main__":
    dialog = SettingsDialog()
    dialog.show()
