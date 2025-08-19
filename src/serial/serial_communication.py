from typing import Optional
import time, re, sys, threading
from glob import glob
from src.serial.device import Device
import logging

# =========SERIAL IMPORT=============
try:
    import serial
except ImportError:
    sys.exit(1)
# ===============================

# =========CONSTANTS=============
BAUD = 9600
TIMEOUT = 2
# ===============================

class SerialCommunication:
    devices = {} # {port: Device}
    devices_lock = threading.Lock()
    communication_logger = logging.getLogger("serial_communication")
    
    def __init__(self):
        self.ports = [] # list of serial ports
        self.threads = [] # list of serial threads

    def start(self):
        self._find_ports()
        self._generate_serial_threads()
    
    # Find serial ports connected with arduino
    def _find_ports(self) -> list:
        self.ports = sorted(glob("/dev/ttyACM*") + glob("/dev/ttyUSB*"))
        self.communication_logger.info(f"Found {len(self.ports)} ports")
        return self.ports

    @staticmethod
    def _parse(line: str, port: str) -> Optional[Device]:
        line = line.strip()
        if not line:
            return None
        
        matched_str = re.search(r"\b(UNO[0-6]_)C\d+\s*[:=]\s*-?\d+\b", line, flags=re.IGNORECASE)
        if matched_str:
            board = matched_str.group(1).upper() # UNO0_
            data = {}
            for matched_str in re.finditer(rf"({board}C(\d+))\s*[:=]\s*(-?\d+)", line, flags=re.IGNORECASE):
                ch = int(matched_str.group(2))
                val = int(matched_str.group(3))
                data[f"{board}C{ch}"] = val
            return Device(board, port, time.time(), data)
        
        matched_str = re.search(r"\[\s*(UNO[0-6])\s*\]", line, flags=re.IGNORECASE)
        if matched_str:
            bnorm = matched_str.group(1).upper() # UNO0
            board = f"{bnorm}_"
            rest = re.sub(r'^\s*\[\s*' + bnorm + r'\s*\]\s*', '', line, flags=re.IGNORECASE)
            data = {}
            for matched_str in re.finditer(r'\bC\s*(\d+)\s*[:=]\s*(-?\d+)\b', rest):
                ch = int(matched_str.group(1))
                val = int(matched_str.group(2))
                data[f"{board}C{ch}"] = val
            return Device(board, port, time.time(), data)
        
        return None

    # Serial thread for reading data from arduino
    @staticmethod
    def _serial_thread(port):
        try:
            s = serial.Serial(port, BAUD, timeout=TIMEOUT)
            time.sleep(2.0) # wait for arduino to reset
            s.reset_input_buffer()

            while True:
                line = s.readline()
                if not line:
                    continue
                try:
                    line = line.decode("utf-8").strip()
                except UnicodeDecodeError:
                    # non utf-8 line
                    continue
                except Exception:
                    # other errors
                    continue

                device = SerialCommunication._parse(line, port)
                if not device:
                    continue
                with SerialCommunication.devices_lock:
                    SerialCommunication.devices[device.port] = device
        except Exception as e:
            pass

    def _generate_serial_threads(self):
        for port in self.ports:
            new_thread = threading.Thread(target=SerialCommunication._serial_thread, args=(port,), daemon=True)
            self.threads.append(new_thread)
            self.communication_logger.info(f"Started thread for {port}")
            new_thread.start()