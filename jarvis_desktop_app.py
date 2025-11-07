import sys
import asyncio
from PyQt6.QtWidgets import QApplication, QMainWindow, QTextEdit, QLineEdit, QVBoxLayout, QWidget, QSystemTrayIcon, QMenu
from PyQt6.QtGui import QIcon, QAction
from PyQt6.QtCore import Qt, QObject, pyqtSignal, QThread
from jarvis_core_optimized import create_jarvis

class JarvisWorker(QObject):
    new_message = pyqtSignal(str)

    def __init__(self, jarvis_core):
        super().__init__()
        self.jarvis_core = jarvis_core
        self.is_running = True

    def run(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.jarvis_core.initialize())
        while self.is_running:
            # This loop can be used for background tasks if needed
            loop.run_until_complete(asyncio.sleep(0.1))

    def stop(self):
        self.is_running = False

    def process_query(self, query):
        loop = asyncio.get_event_loop()
        response = loop.run_until_complete(self.jarvis_core.process_query(query, speak=False))
        self.new_message.emit(response)


class JarvisDesktopApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.create_system_tray_icon()
        self.init_jarvis()

    def init_jarvis(self):
        # This will run in a separate thread, so we need a new event loop
        self.jarvis_core = asyncio.run(create_jarvis(enable_voice=False))
        self.worker_thread = QThread()
        self.jarvis_worker = JarvisWorker(self.jarvis_core)
        self.jarvis_worker.moveToThread(self.worker_thread)

        self.worker_thread.started.connect(self.jarvis_worker.run)
        self.jarvis_worker.new_message.connect(self.update_conversation)

        self.worker_thread.start()

    def init_ui(self):
        self.setWindowTitle("J.A.R.V.I.S.")
        self.setGeometry(100, 100, 800, 600)

        # Apply JARVIS-style stylesheet
        self.setStyleSheet("""
            QMainWindow {
                background-color: #0A0F1A;
            }
            QWidget {
                background-color: #0A0F1A;
                color: #E0E0E0;
                font-family: 'Consolas', 'Courier New', monospace;
            }
            QTextEdit {
                background-color: #141A26;
                border: 1px solid #367BF0;
                border-radius: 5px;
                font-size: 14px;
            }
            QLineEdit {
                background-color: #141A26;
                border: 1px solid #367BF0;
                border-radius: 5px;
                font-size: 14px;
                padding: 5px;
            }
            QMenu {
                background-color: #141A26;
                border: 1px solid #367BF0;
            }
            QMenu::item:selected {
                background-color: #367BF0;
                color: #FFFFFF;
            }
        """)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        self.conversation_view = QTextEdit()
        self.conversation_view.setReadOnly(True)
        layout.addWidget(self.conversation_view)

        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Type your command here...")
        self.input_field.returnPressed.connect(self.handle_input)
        layout.addWidget(self.input_field)

    def create_system_tray_icon(self):
        self.tray_icon = QSystemTrayIcon(self)
        # I will create an icon later. For now, I'll use a standard icon.
        self.tray_icon.setIcon(QIcon(self.style().standardIcon(getattr(self.style(), 'SP_ComputerIcon'))))

        tray_menu = QMenu()
        show_action = QAction("Show", self)
        show_action.triggered.connect(self.show)
        tray_menu.addAction(show_action)

        quit_action = QAction("Quit", self)
        quit_action.triggered.connect(self.quit_app)
        tray_menu.addAction(quit_action)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()

    def handle_input(self):
        user_input = self.input_field.text()
        if user_input:
            self.conversation_view.append(f"> {user_input}")
            self.jarvis_worker.process_query(user_input)
            self.input_field.clear()

    def update_conversation(self, message):
        self.conversation_view.append(f"Jarvis: {message}")

    def closeEvent(self, event):
        event.ignore()
        self.hide()

    def quit_app(self):
        self.tray_icon.hide()
        self.jarvis_worker.stop()
        self.worker_thread.quit()
        self.worker_thread.wait()
        QApplication.instance().quit()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_win = JarvisDesktopApp()
    main_win.show()
    sys.exit(app.exec())
