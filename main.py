import requests
import sys
from PyQt5.QtCore import Qt, QSettings
from PyQt5.QtWidgets import QApplication, \
        QWidget, \
        QVBoxLayout, \
        QHBoxLayout, \
        QLineEdit, \
        QPushButton, \
        QLabel, \
        QMessageBox

from start_window import StartWindow
         

class LoginWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Login Form")

        # Set the window size
        self.setFixedSize(400, 200)

        # Create the main vertical layout
        self.layout = QVBoxLayout()
        # Create an inner layout to center the form (using QVBoxLayout)
        self.center_layout = QVBoxLayout()

        # Email field (label and input together in horizontal layout)
        self.email_layout = QHBoxLayout()
        self.email_label = QLabel("Email:")
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("Enter your email")
        self.email_input.setFixedWidth(250)  # Resize input field
        self.email_input.setFixedHeight(30)  # Resize input field
        self.email_layout.addWidget(self.email_label)
        self.email_layout.addWidget(self.email_input)

        # Password field (label and input together in horizontal layout)
        self.password_layout = QHBoxLayout()
        self.password_label = QLabel("Password:")
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Enter your password")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setFixedWidth(250)  # Resize input field
        self.password_input.setFixedHeight(30)  # Resize input field
        self.password_layout.addWidget(self.password_label)
        self.password_layout.addWidget(self.password_input)

        # Submit button - Centered button layout
        self.submit_button_layout = QHBoxLayout()
        self.submit_button = QPushButton("Login")
        self.submit_button.clicked.connect(self.submit_form)
        self.submit_button.setFixedWidth(100)  # Adjust the button width as needed
        self.submit_button.setFixedHeight(30)  # Adjust the button width as needed
        self.submit_button_layout.addWidget(self.submit_button)
        self.submit_button_layout.setAlignment(Qt.AlignCenter)  # Center the button

        # Add label-input layouts and submit button layout to the center layout
        self.center_layout.addLayout(self.email_layout)
        self.center_layout.addLayout(self.password_layout)
        self.center_layout.addLayout(self.submit_button_layout)

        # Center the form in the window by setting alignment
        self.center_layout.setAlignment(Qt.AlignCenter)

        # Add the centered layout to the main layout
        self.layout.addLayout(self.center_layout)

        # Set the layout for the window
        self.setLayout(self.layout)

    def submit_form(self):
        email = self.email_input.text()
        password = self.password_input.text()

        response = requests.post('http://127.0.0.1:5000/api/login', json={'email': email, 'password': password})
        
        if response.status_code == 200:  # Assuming successful login
            print("Login successful")
            data = response.json()

            # Store credentials (ensure encryption for security)
            settings = QSettings("MyApp", "UserPreferences")
            settings.setValue("email", email)
            settings.setValue("user_id", data['user_id'])
            settings.setValue("secret_key", data['access_token'])  

            # Open the Start Window
            self.open_start_window()

        else:
            print("Login failed:", response.text)
            
            # Show error message box
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Critical)
            msg.setWindowTitle("Login Failed")
            msg.setText("Invalid email or password. Please try again.")
            msg.exec_()

        # Clear fields after submission
        self.email_input.clear()
        self.password_input.clear()

    def open_start_window(self):
        """Opens Start Window and closes Login Window"""
        self.start_window = StartWindow(self)  # Pass self (LoginWindow instance)
        self.start_window.show()
        self.close()

if __name__ == '__main__':
    app = QApplication(sys.argv)

    # Check if secret_key exists
    settings = QSettings("MyApp", "UserPreferences")
    secret_key = settings.value("secret_key", "")

    login_window = LoginWindow()

    if secret_key:
        window = StartWindow(login_window)  # Pass login_window to StartWindow
    else:
        window = login_window

    window.show()
    sys.exit(app.exec_())