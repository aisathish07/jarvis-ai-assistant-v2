"""
═══════════════════════════════════════════════════════════════════════════════
FILE: jarvis_gui.py
DESCRIPTION: System tray GUI with chat window (Optional - requires PyQt6)
DEPENDENCIES: PyQt6 (optional)
NOTE: JARVIS works perfectly fine without GUI in CLI mode!
      Only install PyQt6 if you want the graphical interface.
═══════════════════════════════════════════════════════════════════════════════
"""

import sys
import asyncio
import logging
from jarvis_core_optimized import JarvisIntegrated
logger = logging.getLogger("Jarvis.GUI")

# Try to import PyQt6 (optional dependency)
try:
    from PyQt6.QtWidgets import (
        QApplication, QSystemTrayIcon, QMenu, QMainWindow,
        QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
        QTextEdit, QLabel
    )
    from PyQt6.QtCore import Qt, QThread, pyqtSignal
    from PyQt6.QtGui import QAction
    PYQT_AVAILABLE = True
except ImportError:
    PYQT_AVAILABLE = False
    logger.warning("PyQt6 not installed - GUI unavailable")
    logger.info("To use GUI: pip install PyQt6")


# ═══════════════════════════════════════════════════════════════════════════
# QUERY WORKER (Background Thread for AI Processing)
# ═══════════════════════════════════════════════════════════════════════════

if PYQT_AVAILABLE:
    class QueryWorker(QThread):
        """Background thread for processing AI queries without blocking UI"""
        finished = pyqtSignal(str)
        error = pyqtSignal(str)
        
        def __init__(self, jarvis_core, query: str):
            super().__init__()
            self.jarvis_core = jarvis_core
            self.query = query
        
        def run(self):
            """Process query in background"""
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                response = loop.run_until_complete(
                    self.jarvis_core.process_query(self.query, speak=False)
                )
                self.finished.emit(response)
            except Exception as e:
                self.error.emit(str(e))


# ═══════════════════════════════════════════════════════════════════════════
# MAIN CHAT WINDOW
# ═══════════════════════════════════════════════════════════════════════════

if PYQT_AVAILABLE:
    class JarvisMainWindow(QMainWindow):
        """Main chat interface window"""
        
        def __init__(self, jarvis_core):
            super().__init__()
            self.jarvis_core = jarvis_core
            self.worker = None
            self.init_ui()
        
        def init_ui(self):
            """Setup the main window UI"""
            self.setWindowTitle("JARVIS AI Assistant")
            self.setGeometry(100, 100, 700, 600)
            
            # Main widget and layout
            main_widget = QWidget()
            self.setCentralWidget(main_widget)
            layout = QVBoxLayout()
            main_widget.setLayout(layout)
            
            # Title
            title = QLabel("🤖 JARVIS AI Assistant")
            title.setStyleSheet("font-size: 18px; font-weight: bold; padding: 10px;")
            layout.addWidget(title)
            
            # Chat display
            self.chat_display = QTextEdit()
            self.chat_display.setReadOnly(True)
            self.chat_display.setPlaceholderText("Chat history will appear here...")
            self.chat_display.setStyleSheet("padding: 10px; font-size: 12px;")
            layout.addWidget(self.chat_display)
            
            # Input area
            input_layout = QHBoxLayout()
            
            self.input_field = QTextEdit()
            self.input_field.setPlaceholderText("Type your message here...")
            self.input_field.setMaximumHeight(80)
            self.input_field.setStyleSheet("padding: 8px;")
            input_layout.addWidget(self.input_field)
            
            # Send button
            self.send_btn = QPushButton("Send")
            self.send_btn.clicked.connect(self.send_message)
            self.send_btn.setMinimumWidth(100)
            self.send_btn.setMinimumHeight(80)
            self.send_btn.setStyleSheet("font-size: 14px; font-weight: bold;")
            input_layout.addWidget(self.send_btn)
            
            layout.addLayout(input_layout)
            
            # Status bar
            self.status_label = QLabel("Ready - Type your message and press Send")
            self.status_label.setStyleSheet("padding: 5px; background-color: #f0f0f0;")
            layout.addWidget(self.status_label)
        
        def send_message(self):
            """Send message to JARVIS"""
            message = self.input_field.toPlainText().strip()
            if not message:
                return
            
            # Add to chat display
            self.chat_display.append(f"<b style='color: #2196F3;'>You:</b> {message}")
            self.input_field.clear()
            self.status_label.setText("Processing your request...")
            self.send_btn.setEnabled(False)
            
            # Process in background thread
            self.worker = QueryWorker(self.jarvis_core, message)
            self.worker.finished.connect(self.on_response)
            self.worker.error.connect(self.on_error)
            self.worker.start()
        
        def on_response(self, response: str):
            """Handle AI response"""
            self.chat_display.append(f"<b style='color: #4CAF50;'>JARVIS:</b> {response}\n")
            self.status_label.setText("Ready - Type your message")
            self.send_btn.setEnabled(True)
            
            # Scroll to bottom
            scrollbar = self.chat_display.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())
        
        def on_error(self, error: str):
            """Handle error"""
            self.chat_display.append(f"<b style='color: red;'>Error:</b> {error}\n")
            self.status_label.setText("Error occurred - Try again")
            self.send_btn.setEnabled(True)
        
        def closeEvent(self, event):
            """Handle window close - minimize to tray instead"""
            event.ignore()
            self.hide()
            self.status_label.setText("Minimized to system tray")


# ═══════════════════════════════════════════════════════════════════════════
# SYSTEM TRAY APPLICATION
# ═══════════════════════════════════════════════════════════════════════════

if PYQT_AVAILABLE:
    class JarvisTrayApp:
        """System tray application manager"""
        
        def __init__(self, jarvis_core):
            self.app = QApplication(sys.argv)
            self.jarvis_core = jarvis_core
            
            # Main window
            self.main_window = JarvisMainWindow(jarvis_core)
            
            # System tray icon
            self.tray_icon = QSystemTrayIcon()
            self.setup_tray()
        
        def setup_tray(self):
            """Setup system tray icon and menu"""
            menu = QMenu()
            
            # Show window action
            show_action = QAction("Show JARVIS", self.app)
            show_action.triggered.connect(self.show_window)
            menu.addAction(show_action)
            
            menu.addSeparator()
            
            # Exit action
            exit_action = QAction("Exit", self.app)
            exit_action.triggered.connect(self.exit_app)
            menu.addAction(exit_action)
            
            self.tray_icon.setToolTip("JARVIS AI Assistant")
            self.tray_icon.setContextMenu(menu)
            self.tray_icon.show()
            
            # Double-click to show window
            self.tray_icon.activated.connect(self.tray_activated)
        
        def tray_activated(self, reason):
            """Handle tray icon clicks"""
            if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
                self.show_window()
        
        def show_window(self):
            """Show main window"""
            self.main_window.show()
            self.main_window.activateWindow()
        
        def exit_app(self):
            """Exit application"""
            self.tray_icon.hide()
            self.jarvis_core.cleanup()
            QApplication.quit()
        
        def run(self):
            """Start the application"""
            self.show_window()  # Show window on start
            sys.exit(self.app.exec())


# ═══════════════════════════════════════════════════════════════════════════
# LAUNCH FUNCTION
# ═══════════════════════════════════════════════════════════════════════════

def launch_gui(jarvis_core):
    """Launch GUI or show error message if PyQt6 not available"""
    if PYQT_AVAILABLE:
        app = JarvisTrayApp(jarvis_core)
        app.run()
    else:
        print("\n" + "="*60)
        print("GUI MODE NOT AVAILABLE")
        print("="*60)
        print("\nPyQt6 is not installed.")
        print("\nTo use GUI mode:")
        print("  pip install PyQt6")
        print("\nAlternatively, use CLI mode (works great!):")
        print("  python jarvis.py chat")
        print("\nCLI mode has all the same features without needing PyQt6!")
        print("="*60 + "\n")


# ═══════════════════════════════════════════════════════════════════════════
# TESTING
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    if PYQT_AVAILABLE:
        print("✓ GUI module loaded successfully")
        print("To launch GUI: python jarvis.py gui")
        print("Note: You need to import jarvis_core to use GUI")
    else:
        print("✗ PyQt6 not installed")
        print("Install with: pip install PyQt6")
        print("\nNote: GUI is OPTIONAL")
        print("JARVIS works perfectly in CLI mode without PyQt6!")
        print("Just use: python jarvis.py chat")