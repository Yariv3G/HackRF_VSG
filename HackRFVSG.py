import sys
import SoapySDR
from SoapySDR import *
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QSlider, QVBoxLayout, QHBoxLayout,
    QPushButton, QComboBox, QFileDialog
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
import numpy as np
import os


class TransmitThread(QThread):
    updateStatus = pyqtSignal(str)

    def __init__(self, sdr, txStream, signal, parent=None):
        super().__init__(parent)
        self.sdr = sdr
        self.txStream = txStream
        self.signal = signal
        self.running = True

    def run(self):
        while self.running:
            self.sdr.writeStream(self.txStream, [self.signal], len(self.signal))

    def stop(self):
        self.running = False
        self.wait()


class HackRFGui(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("HackRF Vector Signal Generator")
        self.initUI()

        # Initialize HackRF device
        self.sdr = SoapySDR.Device(dict(driver="hackrf"))
        self.txStream = self.sdr.setupStream(SOAPY_SDR_TX, SOAPY_SDR_CF32)
        self.transmitThread = None
        self.signal_file = None

    def initUI(self):
        # Frequency input
        self.freqLabel = QLabel("Frequency (MHz):")
        self.freqInput = QLineEdit("2400")
        self.freqInput.textChanged.connect(self.update_frequency)

        # Sample rate input
        self.sampleRateLabel = QLabel("Sample Rate (MHz):")
        self.sampleRateInput = QLineEdit("10")  # Default sample rate of 10 MHz

        # Signal Source dropdown
        self.signalSourceLabel = QLabel("Signal Source:")
        self.signalSourceDropdown = QComboBox()
        self.signalSourceDropdown.addItem("Continuous Wave (CW)")
        self.signalSourceDropdown.addItem("Load from .bin File")
        self.signalSourceDropdown.currentIndexChanged.connect(self.on_signal_source_change)

        # Gain sliders and indicators
        self.ifGainLabel = QLabel("IF Gain:")
        self.ifGainSlider = QSlider(Qt.Horizontal)
        self.ifGainSlider.setRange(0, 47)  # Example range for IF gain
        self.ifGainSlider.setValue(20)
        self.ifGainSlider.valueChanged.connect(self.update_if_gain)

        self.ifGainValue = QLabel("20")  # Default IF gain display

        self.rfGainLabel = QLabel("RF Gain:")
        self.rfGainSlider = QSlider(Qt.Horizontal)
        self.rfGainSlider.setRange(0, 47)  # Example range for RF gain
        self.rfGainSlider.setValue(20)
        self.rfGainSlider.valueChanged.connect(self.update_rf_gain)

        self.rfGainValue = QLabel("20")  # Default RF gain display

        # Layout for IF and RF gains
        ifGainLayout = QHBoxLayout()
        ifGainLayout.addWidget(self.ifGainLabel)
        ifGainLayout.addWidget(self.ifGainSlider)
        ifGainLayout.addWidget(self.ifGainValue)

        rfGainLayout = QHBoxLayout()
        rfGainLayout.addWidget(self.rfGainLabel)
        rfGainLayout.addWidget(self.rfGainSlider)
        rfGainLayout.addWidget(self.rfGainValue)

        # Start/Stop Transmission Button
        self.startBtn = QPushButton("Start Transmission")
        self.startBtn.clicked.connect(self.toggle_transmission)

        # Status Label
        self.statusLabel = QLabel("Status: Idle")

        # Layout
        layout = QVBoxLayout()
        layout.addWidget(self.freqLabel)
        layout.addWidget(self.freqInput)
        layout.addWidget(self.sampleRateLabel)
        layout.addWidget(self.sampleRateInput)
        layout.addWidget(self.signalSourceLabel)
        layout.addWidget(self.signalSourceDropdown)
        layout.addLayout(ifGainLayout)
        layout.addLayout(rfGainLayout)
        layout.addWidget(self.startBtn)
        layout.addWidget(self.statusLabel)

        self.setLayout(layout)

    def on_signal_source_change(self):
        if self.signalSourceDropdown.currentText() == "Load from .bin File":
            file_dialog = QFileDialog()
            self.signal_file, _ = file_dialog.getOpenFileName(self, "Select Signal File", "", "Binary Files (*.bin)")
            if self.signal_file:
                self.statusLabel.setText(f"Loaded file: {os.path.basename(self.signal_file)}")
            else:
                self.signalSourceDropdown.setCurrentIndex(0)  # Revert to CW if no file selected

    def update_if_gain(self):
        if_gain = self.ifGainSlider.value()
        self.ifGainValue.setText(str(if_gain))
        self.sdr.setGain(SOAPY_SDR_TX, 0, if_gain)

    def update_rf_gain(self):
        rf_gain = self.rfGainSlider.value()
        self.rfGainValue.setText(str(rf_gain))
        self.sdr.setGain(SOAPY_SDR_TX, 0, rf_gain)

    def update_frequency(self):
        try:
            frequency = float(self.freqInput.text()) * 1e6  # Convert to Hz
            self.sdr.setFrequency(SOAPY_SDR_TX, 0, frequency)
        except ValueError:
            self.statusLabel.setText("Error: Invalid frequency input")

    def toggle_transmission(self):
        if not self.transmitThread or not self.transmitThread.isRunning():
            # Start transmission
            self.start_transmission()
        else:
            # Stop transmission
            self.stop_transmission()

    def start_transmission(self):
        # Get settings from GUI
        frequency = float(self.freqInput.text()) * 1e6  # Convert to Hz
        sample_rate = float(self.sampleRateInput.text()) * 1e6  # Convert to Hz
        self.sdr.setSampleRate(SOAPY_SDR_TX, 0, sample_rate)
        self.sdr.setFrequency(SOAPY_SDR_TX, 0, frequency)

        # Generate the signal
        if self.signalSourceDropdown.currentText() == "Continuous Wave (CW)":
            amplitude = 0.5
            wave_frequency = 1e3  # 1 kHz tone
            t = np.arange(0, 1024) / sample_rate
            signal = amplitude * np.exp(2j * np.pi * wave_frequency * t).astype(np.complex64)
        elif self.signal_file:
            with open(self.signal_file, "rb") as f:
                signal = np.frombuffer(f.read(), dtype=np.complex64)

        # Start transmission thread
        self.transmitThread = TransmitThread(self.sdr, self.txStream, signal)
        self.transmitThread.start()

        # Update UI
        self.startBtn.setText("Stop Transmission")
        self.statusLabel.setText("Status: Transmitting")

    def stop_transmission(self):
        if self.transmitThread:
            self.transmitThread.stop()
            self.transmitThread = None

        # Update UI
        self.startBtn.setText("Start Transmission")
        self.statusLabel.setText("Status: Idle")

    def closeEvent(self, event):
        if self.transmitThread:
            self.transmitThread.stop()
        self.sdr.deactivateStream(self.txStream)
        self.sdr.closeStream(self.txStream)
        self.sdr = None
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    gui = HackRFGui()
    gui.show()
    sys.exit(app.exec_())
