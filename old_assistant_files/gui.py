# gui.py – chat-bot interface (scrollable chat + fixed input bar) FIXED
from __future__ import annotations

import queue
import threading
import tkinter as tk
from typing import Any, Optional

import customtkinter as ctk

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class AssistantGUI:
    """Chat-bot GUI: big scrollable chat + fixed bottom input bar.
    Keeps orb, metrics, suggestions at the top."""

    def __init__(self, input_queue: queue.Queue) -> None:
        self.input_queue = input_queue
        self.stop_event = threading.Event()

        # ----------  root window  ----------
        self.root = ctk.CTk()
        self.root.title("Jarvis")
        self.root.geometry("500x700")
        self.root.resizable(False, False)
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        # ----------  layout: top / middle / bottom  ----------
        self._build_top()
        self._build_chat_area()
        self._build_input_bar()

        # ----------  queue processor (FIXED: bounded queue)  ----------
        self.gui_queue: queue.Queue = queue.Queue(maxsize=100)
        self.root.after(50, self._process_gui_queue)

        # ----------  public hooks  ----------
        self.on_metrics = self.update_metrics

    # ------------------------------------------------------------------
    #  TOP  – orb, metrics, suggestions
    # ------------------------------------------------------------------
    def _build_top(self) -> None:
        top = ctk.CTkFrame(self.root)
        top.pack(side="top", fill="x", padx=10, pady=(10, 5))

        # metrics
        self.metrics_label = ctk.CTkLabel(
            top, text="Model: – | 0 tokens | 0.0 s", font=("Arial", 11)
        )
        self.metrics_label.pack(side="left", padx=8)

        self.token_label = ctk.CTkLabel(top, text="Tokens: 0", font=("Arial", 13))
        self.token_label.pack(side="right", padx=8)

        self.status_label = ctk.CTkLabel(top, text="Ready", font=("Arial", 13))
        self.status_label.pack(side="left", padx=8)

        # orb canvas
        self.wave_canvas = tk.Canvas(
            self.root, width=460, height=90, bg="#2b2b2b", highlightthickness=0
        )
        self.wave_canvas.pack(pady=5)
        self.orb = self.wave_canvas.create_oval(210, 20, 250, 60, fill="gray", outline="")
        self._orb_amplitude = 0.0
        self._target_amplitude = 0.0
        self._smooth_orb()

        # context strip
        self.context_label = ctk.CTkLabel(
            self.root, text="Context: –", font=("Arial", 12), anchor="w"
        )
        self.context_label.pack(fill="x", padx=10, pady=2)

        # suggestions (scrollable, collapsible)
        sugg_frame = ctk.CTkFrame(self.root)
        sugg_frame.pack(side="top", fill="x", padx=10, pady=5)
        self.sugg_inner = ctk.CTkScrollableFrame(sugg_frame, height=100)
        self.sugg_inner.pack(fill="both", expand=True)

    # ------------------------------------------------------------------
    #  CHAT AREA  – big scrollable history (central, permanent)
    # ------------------------------------------------------------------
    def _build_chat_area(self) -> None:
        chat_outer = ctk.CTkFrame(self.root)
        chat_outer.pack(side="top", fill="both", expand=True, padx=10, pady=5)

        self.chat_frame = ctk.CTkScrollableFrame(chat_outer)
        self.chat_frame.pack(fill="both", expand=True)

    # ------------------------------------------------------------------
    #  INPUT BAR  – glued to bottom (non-movable)
    # ------------------------------------------------------------------
    def _build_input_bar(self) -> None:
        bar = ctk.CTkFrame(self.root)
        bar.pack(side="bottom", fill="x", padx=10, pady=(5, 10))

        self.text_input = ctk.CTkEntry(bar, placeholder_text="Message Jarvis...")
        self.text_input.pack(side="left", fill="x", expand=True, padx=(0, 5))
        self.text_input.bind("<Return>", self.send_message)

        self.mic_button = ctk.CTkButton(bar, text="🎤", width=40, command=self.toggle_mic)
        self.mic_button.pack(side="right", padx=(5, 0))

        self.send_button = ctk.CTkButton(bar, text="Send", width=80, command=self.send_message)
        self.send_button.pack(side="right", padx=(5, 0))

    # ------------------------------------------------------------------
    #  ORB ANIMATION
    # ------------------------------------------------------------------
    def _smooth_orb(self) -> None:
        """Animate orb based on current amplitude."""
        try:
            self._orb_amplitude += (self._target_amplitude - self._orb_amplitude) * 0.18
            base_radius = 20
            radius = base_radius + int(self._orb_amplitude * 18)
            cx, cy = 230, 45

            # FIXED: Validate canvas exists
            if self.wave_canvas and self.wave_canvas.winfo_exists():
                self.wave_canvas.coords(
                    self.orb, cx - radius, cy - radius, cx + radius, cy + radius
                )
                self.wave_canvas.delete("wave_line")
                if self._target_amplitude > 0.05:
                    h = int(20 * self._orb_amplitude)
                    self.wave_canvas.create_line(
                        20, 85 - h, 440, 85 - h, fill="#00ffbf", width=2, tag="wave_line"
                    )
                self.root.after(50, self._smooth_orb)
        except Exception as e:
            import logging

            logging.warning("Orb animation error: %s", e)
            self.root.after(50, self._smooth_orb)

    # ------------------------------------------------------------------
    #  PUBLIC API
    # ------------------------------------------------------------------
    def set_state(self, state: str, detail: Optional[str] = None) -> None:
        try:
            self.gui_queue.put_nowait(("set_state", state, detail))
        except queue.Full:
            import logging

            logging.warning("GUI queue full, dropping state update")

    def add_history(self, text: str, is_user: bool = False) -> None:
        try:
            self.gui_queue.put_nowait(("add_history", text, is_user))
        except queue.Full:
            import logging

            logging.warning("GUI queue full, dropping history")

    def add_suggestion(self, text: str) -> None:
        try:
            self.gui_queue.put_nowait(("show_suggestion", text))
        except queue.Full:
            pass

    def clear_suggestions(self) -> None:
        try:
            self.gui_queue.put_nowait(("clear_suggestions",))
        except queue.Full:
            pass

    def update_metrics(self, metrics: dict[str, Any]) -> None:
        try:
            self.gui_queue.put_nowait(("update_metrics", metrics))
        except queue.Full:
            pass

    def update_context(self, ctx: str) -> None:
        try:
            self.gui_queue.put_nowait(("update_context", ctx))
        except queue.Full:
            pass

    # ------------------------------------------------------------------
    #  QUEUE PROCESSOR
    # ------------------------------------------------------------------
    def _process_gui_queue(self) -> None:
        try:
            while True:
                try:
                    msg = self.gui_queue.get_nowait()
                except queue.Empty:
                    break

                cmd, *args = msg
                try:
                    if cmd == "set_state":
                        self._set_state_impl(args[0], args[1] if len(args) > 1 else None)
                    elif cmd == "add_history":
                        self._add_bubble_impl(args[0], args[1])
                    elif cmd == "show_suggestion":
                        self._show_suggestion_impl(args[0])
                    elif cmd == "clear_suggestions":
                        self._clear_suggestions_impl()
                    elif cmd == "update_metrics":
                        self._update_metrics_impl(args[0])
                    elif cmd == "update_context":
                        self.context_label.configure(text=f"Context: {args[0]}")
                    elif cmd == "destroy":
                        self.on_close()
                except Exception as e:
                    import logging

                    logging.error("Error processing GUI command %s: %s", cmd, e)
        except Exception as e:
            import logging

            logging.error("GUI queue processor error: %s", e)

        self.root.after(50, self._process_gui_queue)

    # ----------  Implementation helpers  ----------
    def _set_state_impl(self, state: str, detail: Optional[str] = None) -> None:
        """Update status and control orb animation."""
        text = f"State: {state}"
        if detail:
            text += f" – {detail}"
        self.status_label.configure(text=text)

        if state == "speaking":
            self._target_amplitude = 1.0
        elif state == "listening":
            self._target_amplitude = 0.7
        elif state == "thinking":
            self._target_amplitude = 0.5
        else:
            self._target_amplitude = 0.0

    def _add_bubble_impl(self, text: str, is_user: bool) -> None:
        """Insert a chat bubble (user / assistant)."""
        try:
            card = ctk.CTkFrame(self.chat_frame, fg_color="#2e2e2e", corner_radius=8)
            card.pack(fill="x", pady=4, padx=6, anchor="e" if is_user else "w")

            lbl = ctk.CTkLabel(
                card, text=text, wraplength=420, justify="right" if is_user else "left"
            )
            lbl.pack(anchor="e" if is_user else "w", padx=8, pady=4)

            # FIXED: Safe auto-scroll
            try:
                self.chat_frame._parent_canvas.yview_moveto(1.0)
            except Exception:
                pass  # Private attribute may not exist in all CTk versions
        except Exception as e:
            import logging

            logging.error("Error adding bubble: %s", e)

    def _show_suggestion_impl(self, text: str) -> None:
        """Show one actionable suggestion card."""
        try:
            card = ctk.CTkFrame(self.sugg_inner, fg_color="#2e2e2e", corner_radius=8)
            card.pack(fill="x", padx=6, pady=6)

            lbl = ctk.CTkLabel(card, text=text, wraplength=380, justify="left")
            lbl.pack(anchor="w", padx=8, pady=(8, 6))

            btn_frame = ctk.CTkFrame(card, fg_color="transparent")
            btn_frame.pack(fill="x", padx=8, pady=(0, 8))

            accept_btn = ctk.CTkButton(
                btn_frame,
                text="Run",
                width=80,
                command=lambda: self.input_queue.put(("SUGGESTION_ACCEPT", text)),
            )
            accept_btn.pack(side="left", padx=(0, 8))

            dismiss_btn = ctk.CTkButton(
                btn_frame,
                text="Dismiss",
                width=80,
                fg_color="gray",
                command=lambda: self.input_queue.put(("SUGGESTION_DISMISS", text)),
            )
            dismiss_btn.pack(side="left")
        except Exception as e:
            import logging

            logging.error("Error showing suggestion: %s", e)

    def _clear_suggestions_impl(self) -> None:
        """Clear all suggestions."""
        try:
            for w in self.sugg_inner.winfo_children():
                w.destroy()
        except Exception as e:
            import logging

            logging.error("Error clearing suggestions: %s", e)

    def _update_metrics_impl(self, metrics: dict[str, Any]) -> None:
        """Update metrics display (only call once!)."""
        try:
            provider = metrics.get("last_provider", "–")
            tokens = metrics.get("total_tokens", 0)
            latency = metrics.get("last_latency", 0.0)
            self.metrics_label.configure(
                text=f"🧠 {provider}  |  📊 {tokens} tok  |  ⏱️ {latency:.1f} s"
            )
        except Exception as e:
            import logging

            logging.error("Error updating metrics: %s", e)

    # ----------  User actions  ----------
    def send_message(self, event=None) -> None:
        """Send typed message."""
        text = self.text_input.get().strip()
        if text:
            self.input_queue.put(("TEXT_COMMAND", text))
            self.text_input.delete(0, "end")

    def toggle_mic(self) -> None:
        """Mic button clicked."""
        self.input_queue.put(("WAKE_WORD_DETECTED", "manual"))

    # ----------  Main / shutdown  ----------
    def run(self) -> None:
        """Block until window closed."""
        self.root.mainloop()

    def on_close(self) -> None:
        """Clean shutdown."""
        self.stop_event.set()
        self.input_queue.put(("EXIT", None))
        try:
            self.root.destroy()
        except Exception as e:
            import logging

            logging.warning("Error destroying window: %s", e)
