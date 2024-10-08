# This Python file uses the following encoding: utf-8
import sys

from PySide6.QtWidgets import QApplication, QMainWindow
from PySide6.QtCore import QThread
from PySide6.QtCore import Qt

# Important:
# You need to run the following command to generate the ui_form.py file
#     pyside6-uic form.ui -o ui_form.py
from ui_form import Ui_MainWindow
from ExtractData import SerialPortGetter, DataGetter
from ParallelismChecker import ParallelismChecker


class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.showMaximized()

        # Connect click/open on combo box to starting getSerialPortsThread
        # Once done, serve the results from the thread onto the UI

        # Initialise serial port refresher thread
        self.serport_getter = self.serport_thread = None
        self.data_getter = self.data_thread = None
        self.init_serport_getter()

        self.initialise_comboboxes() # Device Selector
        self.init_parallelism_checker() # Start parallelism checking thread
        self.init_buttons() # Test & Save buttons

        # Terminate all threads
        app.aboutToQuit.connect(self.terminate_threads)

        # Thread for receiving data from serial port
        self.port1_response = ""
        self.portCurrent = None

    def init_buttons(self):
        self.ui.button_test.clicked.connect(self.parallelism_checker.compute)
        self.ui.button_clear.clicked.connect(self.clear_highlights)

    def compute_platform(self, data):
        if self.portCurrent == None:
            print("ERR: No Device Selected")
            self.ui.grade_data.setText("ERROR: NO DATA")
            self.ui.button_test.setText("ERROR: NO DATA")
            return
        else:
            print("Something")
        # if not self.data_getter.isRunning():
        #     print("No data input from serial port!")
        # print(self.receiver_thread.isRunning())

    # INITIALISE COMBO BOXES
    def initialise_comboboxes(self):
        self.ui.serialport_select1.addItem("No Device Selected")
        self.portgroup1 = 1
        self.ui.serialport_select1.currentTextChanged.connect(self.serialPort1Selected)

    # Initialise getting SERIAL PORTS
    def init_serport_getter(self):
        self.serport_getter = SerialPortGetter() # Serial port worker
        self.serport_thread = QThread() # Port Getter Thread

        self.serport_getter.moveToThread(self.serport_thread)

        # Start signal
        self.serport_thread.started.connect(self.serport_getter.getPorts)

        # Termination Signals
        self.serport_getter.finished.connect(self.serport_thread.quit) # When getter is finished, tell thread to quit
        self.serport_getter.finished.connect(self.serport_thread.wait) # When getter is finished, tell thread to quit
        self.serport_thread.finished.connect(self.serport_thread.deleteLater) # When thread is finished, signal thread cleanup
        self.serport_getter.finished.connect(self.serport_getter.deleteLater) # When getter is finished, signal getter cleanup
        self.serport_getter.dataOut.connect(self.serveSerialPorts) # Connect data signal to receiver function
        self.serport_thread.start()

    # Initialising getting DATA FROM SERIAL PORT
    def init_data_getter(self):
        self.data_getter = DataGetter(self.portCurrent, 10) # Serial port worker
        self.data_thread = QThread() # Port Getter Thread

        self.data_getter.moveToThread(self.data_thread)

        # Start signal
        self.data_thread.started.connect(self.data_getter.getData)

        # Process data received signal
        self.data_getter.dataOut.connect(self.display_values)
        self.data_getter.dataOut.connect(self.parallelism_checker.receive)

        # Termination Signals
        self.data_getter.finished.connect(self.data_thread.quit) # When getter is finished, tell thread to quit
        self.data_getter.finished.connect(self.data_thread.wait) # Wait for thread to finish quitting
        self.data_thread.finished.connect(self.data_thread.deleteLater) # When thread is finished, signal thread cleanup
        self.data_getter.finished.connect(self.data_getter.deleteLater) # When getter is finished, signal getter cleanup
        self.data_thread.start()

    # Initialising parallelism checker from data
    def init_parallelism_checker(self):
        self.parallelism_checker = ParallelismChecker() # Compute Thread
        self.parallelism_thread = QThread() # Port Getter Thread

        self.parallelism_checker.moveToThread(self.parallelism_thread)

        # Signals
        self.parallelism_checker.parallel_computed.connect(self.show_parallelism_value)
        self.parallelism_checker.flatness_computed.connect(self.show_flatness_value)
        self.parallelism_checker.peak_points.connect(self.highlight_points)
        self.parallelism_checker.clear_results.connect(self.clear_highlights)

        # # Termination Signals
        self.parallelism_checker.finished.connect(self.parallelism_thread.quit) # When getter is finished, tell thread to quit
        self.parallelism_checker.finished.connect(self.parallelism_thread.wait) # Wait for thread to finish quitting
        self.parallelism_thread.finished.connect(self.parallelism_thread.deleteLater) # When thread is finished, signal thread cleanup
        self.parallelism_checker.finished.connect(self.parallelism_checker.deleteLater) # When getter is finished, signal getter cleanup
        self.parallelism_thread.start()

    def show_parallelism_value(self, parallelism_value):
        self.ui.parallelism_data.setText(str(parallelism_value))

    def show_flatness_value(self, flatness_value):
        self.ui.flatness_data.setText(str(flatness_value))

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

    def clear_highlights(self):
        self.ui.parallelism_data.setText("None")
        self.ui.flatness_data.setText("None")
        self.ui.data1.setStyleSheet("")
        self.ui.data2.setStyleSheet("")
        self.ui.data3.setStyleSheet("")
        self.ui.data4.setStyleSheet("")
        self.ui.data5.setStyleSheet("")
        self.ui.data6.setStyleSheet("")
        self.ui.data7.setStyleSheet("")
        self.ui.data8.setStyleSheet("")
        self.ui.data9.setStyleSheet("")

    # SHOW SERIAL PORTS
    def serveSerialPorts(self, data):
        for port in data:
            if self.ui.serialport_select1.findText(str(port.description()), Qt.MatchContains) == -1:
                self.ui.serialport_select1.addItem(f"[{port.portName()}] {port.description()}")
                self.portgroup1 += 1
                # self.ui.serialport_select2.addItem(f"[{port.portName()}] {port.description()}")
                # self.portgroup2 += 1

    # SELECT SERIAL PORT
    def serialPort1Selected(self, portName):
        if portName == "No Device Selected":
            print("No port selected")
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

        # Get raw port name from selection
        portName = portName.split(' ')[0]
        # print(portName)
        for char in ('[', ']'):
            portName = portName.replace(char, '')

        # Gets the currently selected port

        # new_port = str(self.ui.serialport_select1.currentText())
        if self.portCurrent != portName:
            print(f"New Port: {self.portCurrent} -> {portName}")

            if self.portCurrent is not None:
                self.data_getter.finish()

            self.portCurrent = portName
            self.init_data_getter()
            print(f"Thread started for port: {str(self.ui.serialport_select1.currentText())}")

    # Display received values
    def display_values(self, data):
        # print(data)
        assert(type(data) is dict)
        for i in data.keys():
            match int(i):
                case 0: #
                    self.ui.data1.setText(data[i])
                case 1:
                    self.ui.data2.setText(data[i])
                case 2:
                    self.ui.data3.setText(data[i])
                case 3:
                    self.ui.data4.setText(data[i])
                case 4:
                    self.ui.data5.setText(data[i])
                case 5:
                    self.ui.data6.setText(data[i])
                case 6:
                    self.ui.data7.setText(data[i])
                case 7:
                    self.ui.data8.setText(data[i])
                case 8:
                    self.ui.data9.setText(data[i])

    def terminate_threads(self):
        if self.serport_thread.isRunning():
            self.serport_getter.finish()
        if self.data_thread is not None:
            self.data_getter.finish()
        if self.parallelism_thread.isRunning(): # Thread for parallelism checker
            self.parallelism_checker.finish()
        print("Threads Terminated")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    widget = MainWindow()
    widget.show()

    sys.exit(app.exec())
