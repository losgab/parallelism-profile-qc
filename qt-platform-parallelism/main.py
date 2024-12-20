# This Python file uses the following encoding: utf-8
import sys
import pandas as pd
from os import path
from datetime import datetime

from PySide6.QtWidgets import QApplication, QMainWindow
from PySide6.QtCore import QThread, Signal

'''
Qt app source code for Build Platform Measurement Jig
Author:
    - Gabriel Thien (Asiga 2023-2024)
Project members:
    - Lucasz Kaminski
    - Ramses Gonzales
    - Gabriel Thien
'''
VERSION = "1.0.0"

BIAS_BACK_ROW = 0.000 # Indicators 0, 1, 2
BIAS_MIDDLE_ROW = 0.001 # Indicators 3, 4, 5
BIAS_FRONT_ROW = 0.002 # Indicators 6, 7, 8

PASS_CRITERIA = 0.035

# Important:
# You need to run the following command to generate the ui_form.py file
#     pyside6-uic form.ui -o ui_form.py
from ui_form import Ui_MainWindow
from ExtractData import SerialPortGetter, DataGetter
# from ParallelismChecker import ParallelismChecker
from qr import QRScanner
from PostToSheet import post_to_google_sheets

DATA_FILE = "data.csv"

class MainWindow(QMainWindow):
    get_qr_id = Signal()

    connect_to_data_serial_port = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.showMaximized()

        # Connect click/open on combo box to starting getSerialPortsThread
        # Once done, serve the results from the thread onto the UI

        self.data = {}
        self.num_valid_data = 0

        self.show_bias()

        # Initialise serial port refresher thread
        self.serport_getter = self.serport_thread = None
        self.data_getter = self.data_thread = None

        self.data_port = None

        self.qr_scanner = self.qr_scanner_thread = None
        self.init_buttons() # Test & Save buttons
        self.init_qr_scanner()
        self.init_serport_getter()
        self.init_data_getter()

        # self.ui.serialport_select1.addItem("No Device Selected")
        # self.portgroup1 = 1
        # self.ui.serialport_select1.currentTextChanged.connect(self.serialPort1Selected)
        
        self.parallelism_value = self.identifier = None
        
        # Terminate all threads
        app.aboutToQuit.connect(self.terminate_threads)

        # Thread for receiving data from serial port
        self.portCurrent = None

    def init_buttons(self):
        # self.ui.button_test.clicked.connect(self.save_data)
        self.ui.button_test.clicked.connect(self.grade_part)
        self.ui.button_clear.clicked.connect(self.clear)

    def show_bias(self):
        self.ui.data1_bias.setTitle(f"{BIAS_BACK_ROW}")
        self.ui.data2_bias.setTitle(f"{BIAS_BACK_ROW}")
        self.ui.data3_bias.setTitle(f"{BIAS_BACK_ROW}")
        self.ui.data4_bias.setTitle(f"{BIAS_MIDDLE_ROW}")
        self.ui.data5_bias.setTitle(f"{BIAS_MIDDLE_ROW}")
        self.ui.data6_bias.setTitle(f"{BIAS_MIDDLE_ROW}")
        self.ui.data7_bias.setTitle(f"{BIAS_FRONT_ROW}")
        self.ui.data8_bias.setTitle(f"{BIAS_FRONT_ROW}")
        self.ui.data9_bias.setTitle(f"{BIAS_FRONT_ROW}")

    def new_serial_port_connected(self, dataPortName):
        self.data_port = dataPortName
        self.ui.serial_handler_output.setText(dataPortName)

    # Initialise getting SERIAL PORTS
    def init_serport_getter(self):
        self.serport_getter = SerialPortGetter() # Serial port worker
        self.serport_thread = QThread() # Port Getter Thread
        # self.serport_thread.setParent(self)

        self.serport_getter.moveToThread(self.serport_thread)

        # Start signal
        self.serport_thread.started.connect(self.serport_getter.getPorts)

        # Serve serial ports signal
        # self.serport_getter.dataOut.connect(self.serveSerialPorts) # Connect data signal to receiver function
        
        # Termination Signals
        self.serport_getter.finished.connect(self.serport_thread.quit) # When getter is finished, tell thread to quit
        self.serport_getter.finished.connect(self.serport_thread.wait) # When getter is finished, tell thread to quit
        self.serport_thread.finished.connect(self.serport_thread.deleteLater) # When thread is finished, signal thread cleanup
        self.serport_getter.finished.connect(self.serport_getter.deleteLater) # When getter is finished, signal getter cleanup
        self.serport_thread.start()

    # Initialising getting DATA FROM SERIAL PORT
    def init_data_getter(self):
        self.data_getter = DataGetter() # Serial port worker
        self.data_thread = QThread() # Port Getter Thread
        # self.data_thread.setParent(self)

        self.data_getter.moveToThread(self.data_thread)

        # Connect signals
        self.connect_to_data_serial_port.connect(self.data_getter.findESP32S3Port)
        self.data_getter.new_serial_port_name.connect(self.new_serial_port_connected)

        # Termination Signals
        self.data_getter.finished.connect(self.data_thread.quit) # When getter is finished, tell thread to quit
        self.data_getter.finished.connect(self.data_thread.wait) # Wait for thread to finish quitting
        self.data_thread.finished.connect(self.data_thread.deleteLater) # When thread is finished, signal thread cleanup
        self.data_getter.finished.connect(self.data_getter.deleteLater) # When getter is finished, signal getter cleanup
        self.data_getter.dataOut.connect(self.display_values)
        self.data_thread.start()

        # Give command to connect to ESP32
        self.connect_to_data_serial_port.emit()

    # Initialise QR Scanner
    def init_qr_scanner(self):
        self.qr_scanner = QRScanner()
        self.qr_scanner_thread = QThread()
        # self.qr_scanner_thread.setParent(self)

        self.ui.button_connect_scanner.clicked.connect(self.qr_scanner.read_qr)
        self.qr_scanner.qr_identifier.connect(self.show_identifier)

        self.qr_scanner.moveToThread(self.qr_scanner_thread)

        # Signals
        self.get_qr_id.connect(self.qr_scanner.read_qr)

        # Termination Signals
        self.qr_scanner.finished.connect(self.qr_scanner_thread.quit) # When getter is finished, tell thread to quit
        self.qr_scanner.finished.connect(self.qr_scanner_thread.wait) # Wait for thread to finish quitting
        self.qr_scanner_thread.finished.connect(self.qr_scanner_thread.deleteLater) # When thread is finished, signal thread cleanup
        self.qr_scanner.finished.connect(self.qr_scanner.deleteLater) # When getter is finished, signal getter cleanup
        self.qr_scanner_thread.start()

    def grade_part(self):
        self.clear()
        self.ui.button_test.setText("...")

        # if self.ui.serialport_select1.currentText() == "No Device":
        #     self.ui.grade_data.setText("No Device")
        #     self.ui.parallelism_data.setText("No Device")
        #     self.ui.button_test.setText("TEST PLATFORM")
        #     return
        if self.data_port == "No Device":
            self.ui.grade_data.setText("No Device")
            self.ui.parallelism_data.setText("No Device")
            self.ui.button_test.setText("TEST PLATFORM")
            return
    
        if not self.data or self.num_valid_data < 8: # Accepts 8 or 9 data points
            self.ui.grade_data.setText("DATA ERROR")
            self.ui.parallelism_data.setText("DATA ERROR")
            self.ui.button_test.setText("TEST PLATFORM")
            self.parallelism_value = None
            return

        # Calculating parallelism value
        float_data = [float(value) for value in self.data.values() if value != "--.---"]
        max_min = round(abs(max(float_data) - min(float_data)), 3)
        self.parallelism_value = str(max_min)

        self.ui.parallelism_data.setText(self.parallelism_value)

        if (max_min <= PASS_CRITERIA):
            self.ui.grade_data.setText("PASS")
            self.ui.grade_data.setStyleSheet("background: green")
        else:
            self.ui.grade_data.setText("FAIL")
            self.ui.grade_data.setStyleSheet("background: red")
        
        # Highlight points
        max_index = float_data.index(max(float_data))
        min_index = float_data.index(min(float_data))
        self.highlight_points([max_index, min_index])

        self.get_qr_id.emit()

        # Reset
        self.ui.button_test.setText("TEST PLATFORM")

    def show_identifier(self, qr_code_text):
        self.ui.identifier_data.setText(str(qr_code_text))
        self.identifier = qr_code_text

        # Save data
        self.save_data()

    def highlight_points(self, points):
        for point in points:
            match int(point):
                case 0:
                    self.ui.data1.setStyleSheet("background: green")
                case 1:
                    self.ui.data2.setStyleSheet("background: green")
                case 2:
                    self.ui.data3.setStyleSheet("background: green")
                case 3:
                    self.ui.data4.setStyleSheet("background: green")
                case 4:
                    self.ui.data5.setStyleSheet("background: green")
                case 5:
                    self.ui.data6.setStyleSheet("background: green")
                case 6:
                    self.ui.data7.setStyleSheet("background: green")
                case 7:
                    self.ui.data8.setStyleSheet("background: green")
                case 8:
                    self.ui.data9.setStyleSheet("background: green")

    def clear(self):
        self.ui.parallelism_data.setText("")
        self.ui.identifier_data.setText("")
        self.ui.grade_data.setText("")
        self.ui.data1.setStyleSheet("")
        self.ui.data2.setStyleSheet("")
        self.ui.data3.setStyleSheet("")
        self.ui.data4.setStyleSheet("")
        self.ui.data5.setStyleSheet("")
        self.ui.data6.setStyleSheet("")
        self.ui.data7.setStyleSheet("")
        self.ui.data8.setStyleSheet("")
        self.ui.data9.setStyleSheet("")
        self.ui.grade_data.setStyleSheet("")

    # # SHOW SERIAL PORTS
    # def serveSerialPorts(self, data):
    #     for port in data:
    #         if self.ui.serialport_select1.findText(str(port.description()), Qt.MatchContains) == -1:
    #             self.ui.serialport_select1.addItem(f"[{port.portName()}] {port.description()}")
    #             self.portgroup1 += 1

    # SELECT SERIAL PORT
    def serialPort1Selected(self, portName):
        if portName == "No Device Selected":
            self.ui.data1.setText("No Data")
            self.ui.data2.setText("No Data")
            self.ui.data3.setText("No Data")
            self.ui.data4.setText("No Data")
            self.ui.data5.setText("No Data")
            self.ui.data6.setText("No Data")
            self.ui.data7.setText("No Data")
            self.ui.data8.setText("No Data")
            self.ui.data9.setText("No Data")

            self.data_getter.finish()
            self.portCurrent = None
            return

        portName = portName.split(' ')[0]
        for char in ('[', ']'):
            portName = portName.replace(char, '')

        # Gets the currently selected port
 
        if self.portCurrent != portName:
            self.portCurrent = portName
            self.new_serial_port_name.emit(portName)

    # Display received values
    def display_values(self, data):
        assert(type(data) is dict)

        self.data = data

        # Apply bias to numbers that are valid
        self.num_valid_data = 9
        for key, value in self.data.items():
            # Check if value is a valid real number
            if self.data[key] == "--.---":
                self.num_valid_data -= 1 # Decrement number of valid data
                continue

            # Apply bias to numbers that are valid
            match int(key):
                case 0 | 1 | 2:
                    self.data[key] = f"{round(float(value) + BIAS_BACK_ROW, 3)}"
                case 3 | 4 | 5:
                    self.data[key] = f"{round(float(value) + BIAS_MIDDLE_ROW, 3)}"
                case 6 | 7 | 8:
                    self.data[key] = f"{round(float(value) + BIAS_FRONT_ROW, 3)}"

        for key, value in self.data.items():
            match int(key):
                case 0:
                    self.ui.data1.setText(value)
                case 1:
                    self.ui.data2.setText(value)
                case 2:
                    self.ui.data3.setText(value)
                case 3:
                    self.ui.data4.setText(value)
                case 4:
                    self.ui.data5.setText(value)
                case 5:
                    self.ui.data6.setText(value)
                case 6:
                    self.ui.data7.setText(value)
                case 7:
                    self.ui.data8.setText(value)
                case 8:
                    self.ui.data9.setText(value)

    def save_data(self):
        if self.parallelism_value == None:
            self.ui.parallelism_data.setText("No Parallelism Data")
            return

        if self.identifier == None:
            self.ui.identifier_data.setText("No Identifier Data")
            return

        date = datetime.now().strftime("%H:%M - %d/%m/%Y")
        PlatformID = self.ui.identifier_data.text().strip()
        grade = self.ui.grade_data.text()
        MaxMin = self.ui.parallelism_data.text()
        point_data = {
            "0": "-",
            "1": "-",
            "2": "-",
            "3": "-",
            "4": "-",
            "5": "-",
            "6": "-",
            "7": "-",
            "8": "-"
        } if self.data == {} else self.data

        if path.isfile(DATA_FILE):
            file = pd.read_csv(DATA_FILE)


            new_row = pd.DataFrame([{'Date': f'{date}',
                                     'PlatformID': f'{PlatformID}',
                                     'Grade': f"{grade}", 
                                     'MaxMin': f'{MaxMin}',
                                     '0': f'{point_data["0"]}',
                                     '1': f'{point_data["1"]}',
                                     '2': f'{point_data["2"]}',
                                     '3': f'{point_data["3"]}',
                                     '4': f'{point_data["4"]}',
                                     '5': f'{point_data["5"]}',
                                     '6': f'{point_data["6"]}',
                                     '7': f'{point_data["7"]}',
                                     '8': f'{point_data["8"]}'}])
            file = pd.concat([file, new_row], ignore_index=True)
            file.to_csv(DATA_FILE, index=False)
        else:
            print("File does not exist")

        post_json_data = {
            "date": f'{date}',
            "platform_id": f'{PlatformID}',
            "grade": grade,
            "maxmin": f'{MaxMin}',
            "data_points": point_data
        }

        success = post_to_google_sheets(json_data=post_json_data)
        if success:
            print("Successfully posted to Google Sheets")
        else:
            print("Failed to post to Google Sheets")
        
    def terminate_threads(self):
        if self.serport_thread.isRunning():
            self.serport_getter.finish()
        if self.data_thread.isRunning(): # Thread for data getter
            self.data_getter.finish()
        if self.qr_scanner_thread.isRunning(): # Thread for parallelism checker
            self.qr_scanner.finish_all()
        print("Threads Terminated")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    widget = MainWindow()
    widget.show()

    sys.exit(app.exec())
