import serial
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class FileChangeHandler(FileSystemEventHandler):
    def __init__(self, serial_port):
        self.serial_port = serial_port
        self.isOn = False

    def on_modified(self, event):
        if event.is_directory:
            return

        if event.src_path == "C:\\roms\\bsnes-plus-v05.100-master\\notes.log":
            with open(event.src_path, "r") as file:
                new_lines = file.readlines()
            if new_lines.__sizeof__() > 0:
                  line = new_lines[-1]
                  print(line)
                  if line.__contains__('SAMPLE 14: 72'):
                    self.serial_port.write('three()\r'.encode())
                    self.serial_port.flushInput()
                    self.isOn = True
                    time.sleep(2)
                    self.serial_port.write('off()\r'.encode())
                    self.serial_port.flushInput()
                    self.isOn = False
                  elif line.__contains__('SAMPLE 14: 60'):
                    self.serial_port.write('one()\r'.encode())
                    self.serial_port.flushInput()
                    self.isOn = True
                    time.sleep(1.25)
                    self.serial_port.write('two()\r'.encode())
                    self.serial_port.flushInput()
                    self.isOn = False
                  else:
                    self.serial_port.write('off()\r'.encode())
                    self.serial_port.flushInput()
                    self.isOn = True


if __name__ == "__main__":
    ser = serial.Serial("COM3", baudrate=115200, timeout=1)

    event_handler = FileChangeHandler(ser)
    observer = Observer()
    observer.schedule(event_handler, path="C:\\roms\\bsnes-plus-v05.100-master\\", recursive=False)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()

    observer.join()
    ser.close()
