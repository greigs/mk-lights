import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import websocket
import _thread
import time
import rel

class FileChangeHandler(FileSystemEventHandler):
    def __init__(self, ws):
        self.ws = ws
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
                    ws.send('three()')
                    
                    self.isOn = True
                    time.sleep(2)
                    ws.send('off()')
                    
                    self.isOn = False
                  elif line.__contains__('SAMPLE 14: 60'):
                    ws.send('one()')
                    
                    self.isOn = True
                    time.sleep(1.25)
                    ws.send('two()')
                    
                    self.isOn = False
                  else:
                    ws.send('off()')
                    
                    self.isOn = True


def on_message(ws, message):
    print(message)

def on_error(ws, error):
    print(error)

def on_close(ws, close_status_code, close_msg):
    print("### closed ###")

def on_open(ws):
    print("Opened connection")



if __name__ == "__main__":

    websocket.enableTrace(True)
    ws = websocket.WebSocketApp("ws://192.168.1.8:3000",
                              on_open=on_open,
                              on_message=on_message,
                              on_error=on_error,
                              on_close=on_close)

    ws.run_forever(dispatcher=rel, reconnect=5)  # Set dispatcher to automatic reconnection, 5 second reconnect delay if connection closed unexpectedly
    ws.send('off()')

    event_handler = FileChangeHandler(ws)
    observer = Observer()
    observer.schedule(event_handler, path="C:\\roms\\bsnes-plus-v05.100-master\\", recursive=False)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()

    observer.join()

    rel.signal(2, rel.abort)  # Keyboard Interrupt
    rel.dispatch()
