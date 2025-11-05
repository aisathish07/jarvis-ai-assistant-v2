# floating_widget.py - Floating assistant widget (FIXED crash issues)
import logging
import math
import queue
import tkinter as tk
from tkinter import Menu
from typing import Callable

import customtkinter as ctk

ctk.set_appearance_mode("dark")
logger = logging.getLogger("AI_Assistant.FloatingWidget")


class FloatingWidget:
    """
    Floating, always-on-top assistant widget.
    Features:
    - Draggable orb that follows you around
    - Animated pulsing when listening/speaking
    - Click to activate voice command
    - Right-click for quick menu
    - Minimize to system tray
    """

    def __init__(self, command_callback: Callable, on_close: Callable):
        self.command_callback = command_callback
        self.on_close = on_close

        # Create window
        self.root = tk.Tk()
        self.root.title("Jarvis")
        self.root.overrideredirect(True)  # Remove window decorations
        self.root.attributes("-topmost", True)  # Always on top
        self.root.attributes("-alpha", 0.95)  # Slight transparency

        # Window size and position
        self.size = 120
        screen_width = self.root.winfo_screenwidth()
        self.root.geometry(f"{self.size}x{self.size}+{screen_width - 150}+100")

        # Make window transparent background
        self.root.configure(bg="#000001")
        self.root.wm_attributes("-transparentcolor", "#000001")

        # State
        self.dragging = False
        self.drag_x = 0
        self.drag_y = 0
        self.state = "idle"  # idle, listening, speaking, thinking
        self.animation_frame = 0
        self.pulse_size = 1.0
        self.expanded = False
        self.is_running = True

        # Canvas for drawing
        self.canvas = tk.Canvas(
            self.root,
            width=self.size,
            height=self.size,
            bg="#000001",
            highlightthickness=0,
            cursor="hand2",
        )
        self.canvas.pack()

        # Create orb
        self.orb_center = self.size // 2
        self.orb_radius = 40
        self.orb = self.canvas.create_oval(
            self.orb_center - self.orb_radius,
            self.orb_center - self.orb_radius,
            self.orb_center + self.orb_radius,
            self.orb_center + self.orb_radius,
            fill="#1a1a2e",
            outline="#00ffbf",
            width=3,
        )

        # Inner glow
        self.glow = self.canvas.create_oval(
            self.orb_center - self.orb_radius + 10,
            self.orb_center - self.orb_radius + 10,
            self.orb_center + self.orb_radius - 10,
            self.orb_center + self.orb_radius - 10,
            fill="",
            outline="#00ffbf",
            width=1,
        )

        # Status text
        self.status_text = self.canvas.create_text(
            self.orb_center, self.orb_center, text="J", font=("Arial", 28, "bold"), fill="#00ffbf"
        )

        # Bind events
        self.canvas.bind("<Button-1>", self.on_click)
        self.canvas.bind("<Button-3>", self.show_menu)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)
        self.canvas.bind("<Enter>", self.on_hover)
        self.canvas.bind("<Leave>", self.on_leave)

        # Context menu
        self.menu = Menu(self.root, tearoff=0)
        self.menu.add_command(label="🎤 Voice Command", command=self.trigger_voice)
        self.menu.add_separator()
        self.menu.add_command(label="⚙️ Settings", command=self.open_settings)
        self.menu.add_command(label="📊 Stats", command=self.show_stats)
        self.menu.add_separator()
        self.menu.add_command(label="❌ Exit", command=self.safe_close)

        # Queue for updates from main thread
        self.update_queue = queue.Queue()

        # Start animation loop
        self.animate()

        # Start processing updates
        self.process_updates()

        logger.info("Floating widget initialized")

    def safe_close(self):
        """Safely close the widget"""
        try:
            logger.info("Safe close requested")
            self.is_running = False
            if self.on_close:
                self.on_close()
        except Exception as e:
            logger.error(f"Error in safe_close: {e}")

    def animate(self):
        """Smooth animation loop"""
        if not self.is_running:
            return

        try:
            self.animation_frame += 1

            if self.state == "listening":
                # Pulsing blue
                self.pulse_size = 1.0 + 0.2 * math.sin(self.animation_frame * 0.2)
                color = "#00bfff"
                self.canvas.itemconfig(self.orb, outline=color, width=3)
                self.canvas.itemconfig(self.status_text, text="🎤")

            elif self.state == "speaking":
                # Pulsing green
                self.pulse_size = 1.0 + 0.15 * math.sin(self.animation_frame * 0.3)
                color = "#00ff88"
                self.canvas.itemconfig(self.orb, outline=color, width=4)
                self.canvas.itemconfig(self.status_text, text="🔊")

            elif self.state == "thinking":
                # Rotating gradient
                angle = (self.animation_frame * 5) % 360
                color = f"#{int(128 + 127 * math.sin(math.radians(angle))):02x}ff{int(128 + 127 * math.cos(math.radians(angle))):02x}"
                self.canvas.itemconfig(self.orb, outline=color)
                self.canvas.itemconfig(self.status_text, text="🧠")

            else:  # idle
                # Gentle breathing
                self.pulse_size = 1.0 + 0.05 * math.sin(self.animation_frame * 0.1)
                self.canvas.itemconfig(self.orb, outline="#00ffbf", width=3)
                self.canvas.itemconfig(self.status_text, text="J")

            # Update orb size
            radius = self.orb_radius * self.pulse_size
            self.canvas.coords(
                self.orb,
                self.orb_center - radius,
                self.orb_center - radius,
                self.orb_center + radius,
                self.orb_center + radius,
            )

            # Update glow
            glow_radius = radius - 15
            self.canvas.coords(
                self.glow,
                self.orb_center - glow_radius,
                self.orb_center - glow_radius,
                self.orb_center + glow_radius,
                self.orb_center + glow_radius,
            )

            # Schedule next frame (60 FPS)
            if self.is_running:
                self.root.after(16, self.animate)
        except Exception as e:
            logger.error(f"Animation error: {e}")

    def on_click(self, event):
        """Handle click - trigger voice command"""
        try:
            if not self.dragging:
                logger.info("Orb clicked - triggering voice command")
                self.trigger_voice()
            self.drag_x = event.x
            self.drag_y = event.y
        except Exception as e:
            logger.error(f"Click error: {e}")

    def on_drag(self, event):
        """Handle dragging the widget"""
        try:
            self.dragging = True
            x = self.root.winfo_x() + event.x - self.drag_x
            y = self.root.winfo_y() + event.y - self.drag_y
            self.root.geometry(f"+{x}+{y}")
        except Exception as e:
            logger.error(f"Drag error: {e}")

    def on_release(self, event):
        """Handle release - snap to screen edge if close"""
        try:
            self.root.after(100, lambda: setattr(self, "dragging", False))

            # Snap to edges
            screen_w = self.root.winfo_screenwidth()
            screen_h = self.root.winfo_screenheight()
            x = self.root.winfo_x()
            y = self.root.winfo_y()

            # Snap to right edge
            if x > screen_w - 200:
                x = screen_w - self.size - 10
            # Snap to left edge
            elif x < 50:
                x = 10

            # Keep within vertical bounds
            if y < 0:
                y = 0
            elif y > screen_h - self.size:
                y = screen_h - self.size

            self.root.geometry(f"+{x}+{y}")
        except Exception as e:
            logger.error(f"Release error: {e}")

    def on_hover(self, event):
        """Show tooltip on hover"""
        try:
            self.root.attributes("-alpha", 1.0)
        except Exception as e:
            logger.error(f"Hover error: {e}")

    def on_leave(self, event):
        """Restore transparency"""
        try:
            self.root.attributes("-alpha", 0.95)
        except Exception as e:
            logger.error(f"Leave error: {e}")

    def show_menu(self, event):
        """Show context menu"""
        try:
            self.menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.menu.grab_release()

    def trigger_voice(self):
        """Trigger voice command"""
        try:
            logger.info("Voice command triggered")
            if self.command_callback:
                self.command_callback("WAKE_WORD_DETECTED", "manual")
        except Exception as e:
            logger.error(f"Trigger voice error: {e}")

    def open_settings(self):
        """Open settings window"""
        try:
            logger.info("Settings requested")
            if self.command_callback:
                self.command_callback("OPEN_SETTINGS", None)
        except Exception as e:
            logger.error(f"Open settings error: {e}")

    def show_stats(self):
        """Show system stats"""
        try:
            logger.info("Stats requested")
            if self.command_callback:
                self.command_callback("SHOW_STATS", None)
        except Exception as e:
            logger.error(f"Show stats error: {e}")

    def set_state(self, state: str):
        """Update assistant state"""
        try:
            if self.is_running:
                self.update_queue.put(("state", state))
        except Exception as e:
            logger.error(f"Set state error: {e}")

    def show_message(self, message: str, duration: int = 3000):
        """Show temporary message"""
        try:
            if self.is_running:
                self.update_queue.put(("message", message, duration))
        except Exception as e:
            logger.error(f"Show message error: {e}")

    def process_updates(self):
        """Process updates from queue"""
        if not self.is_running:
            return

        try:
            while not self.update_queue.empty():
                try:
                    update = self.update_queue.get_nowait()
                    cmd = update[0]

                    if cmd == "state":
                        self.state = update[1]
                    elif cmd == "message":
                        # TODO: Show tooltip message
                        pass
                except queue.Empty:
                    break
                except Exception as e:
                    logger.error(f"Process update error: {e}")
        except Exception as e:
            logger.error(f"Process updates error: {e}")

        if self.is_running:
            self.root.after(50, self.process_updates)

    def run(self):
        """Start the widget"""
        try:
            logger.info("Starting widget main loop")
            self.root.mainloop()
        except Exception as e:
            logger.error(f"Widget run error: {e}")
        finally:
            self.is_running = False

    def destroy(self):
        """Clean shutdown"""
        try:
            logger.info("Destroying widget")
            self.is_running = False
            self.root.quit()
            self.root.destroy()
        except Exception as e:
            logger.error(f"Destroy error: {e}")


if __name__ == "__main__":
    # Test the widget standalone
    import logging

    logging.basicConfig(level=logging.INFO)

    def test_callback(event_type, data):
        print(f"Event: {event_type}, Data: {data}")

    def test_close():
        print("Close requested")
        import sys

        sys.exit(0)

    widget = FloatingWidget(test_callback, test_close)
    widget.run()
