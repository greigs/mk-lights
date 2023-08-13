import network
import time
import random

from ws_connection import ClientClosedError
from ws_server import WebSocketServer, WebSocketClient

from sys import stdin
import array, time
from machine import Pin
import rp2
import micropython
import uselect


ssid = 'CHANGEME'
password = 'CHANGEME'

class ValueGenerator(WebSocketClient):
    value = 0
    def __init__(self, conn):
        super().__init__(conn)

    def process(self):
        try:
            msg = self.connection.read()
            if not msg:
                return
            msg = msg.decode("utf-8")
            print(msg)
            items = msg.split(" ")
            cmd = items[0]
            if cmd == "one()":
                one()
                self.connection.write("->one()")
                print("one()")
            elif cmd == "two()":
                two()
                self.connection.write("->two()")
                print("two()")
            elif cmd == "three()":
                three()
                self.connection.write("->three()")
                print("three()")
            elif cmd == "off()":
                off()
                self.connection.write("->off()")
                print("off()")
        except ClientClosedError:
            pass


class AppServer(WebSocketServer):
    def __init__(self):
        super().__init__("percentage.html", 10)

    def _make_client(self, conn):
        return ValueGenerator(conn)



# how serial lines are ended
TERMINATOR = "\n"
buffered_input = []

# Configure the number of WS2812 LEDs.
NUM_LEDS = 16
PIN_NUM = 22
brightness = 1.0

@rp2.asm_pio(sideset_init=rp2.PIO.OUT_LOW, out_shiftdir=rp2.PIO.SHIFT_LEFT, autopull=True, pull_thresh=24)
def ws2812():
    T1 = 2
    T2 = 5
    T3 = 3
    wrap_target()
    label("bitloop")
    out(x, 1)               .side(0)    [T3 - 1]
    jmp(not_x, "do_zero")   .side(1)    [T1 - 1]
    jmp("bitloop")          .side(1)    [T2 - 1]
    label("do_zero")
    nop()                   .side(0)    [T2 - 1]
    wrap()


# Create the StateMachine with the ws2812 program, outputting on pin
sm = rp2.StateMachine(0, ws2812, freq=8_000_000, sideset_base=Pin(PIN_NUM))

# Start the StateMachine, it will wait for data on its FIFO.
sm.active(1)

# Display a pattern on the LEDs via an array of LED RGB values.
ar = array.array("I", [0 for _ in range(NUM_LEDS)])

##########################################################################
def pixels_show():
    dimmer_ar = array.array("I", [0 for _ in range(NUM_LEDS)])
    for i,c in enumerate(ar):
        r = int(((c >> 8) & 0xFF) * brightness)
        g = int(((c >> 16) & 0xFF) * brightness)
        b = int((c & 0xFF) * brightness)
        dimmer_ar[i] = (g<<16) + (r<<8) + b
    sm.put(dimmer_ar, 8)
    time.sleep_ms(10)

def pixels_set(i, color):
    ar[i] = (color[1]<<16) + (color[0]<<8) + color[2]

def pixels_fill(color):
    for i in range(len(ar)):
        pixels_set(i, color)

def color_chase(color, wait):
    for i in range(NUM_LEDS):
        pixels_set(i, color)
        time.sleep(wait)
        pixels_show()
    time.sleep(0.2)
 
def wheel(pos):
    # Input a value 0 to 255 to get a color value.
    # The colours are a transition r - g - b - back to r.
    if pos < 0 or pos > 255:
        return (0, 0, 0)
    if pos < 85:
        return (255 - pos * 3, pos * 3, 0)
    if pos < 170:
        pos -= 85
        return (0, 255 - pos * 3, pos * 3)
    pos -= 170
    return (pos * 3, 0, 255 - pos * 3)
 
 
def rainbow_cycle(wait):
    for j in range(255):
        for i in range(NUM_LEDS):
            rc_index = (i * 256 // NUM_LEDS) + j
            pixels_set(i, wheel(rc_index & 255))
        pixels_show()
        time.sleep(wait)


def led_on():
    led = machine.Pin("LED", machine.Pin.OUT)
    led.value(1)

def led_off():
    led = machine.Pin("LED", machine.Pin.OUT)
    led.value(0)

BLACK = (0, 0, 0)
RED = (255, 0, 0)
YELLOW = (255, 150, 0)
GREEN = (0, 255, 0)
CYAN = (0, 255, 255)
BLUE = (0, 0, 255)
PURPLE = (180, 0, 255)
WHITE = (255, 255, 255)
COLORS = (RED, YELLOW, GREEN, CYAN, BLUE, PURPLE, WHITE, BLACK)

range1 = range(0,1)
range2 = range(7,8)
range3 = range(14,15)

def off():
    pixels_fill(BLACK)
    pixels_show()

def one():
    for i in range1:
        pixels_set(i, WHITE)
    for i in range2:
        pixels_set(i, BLACK)    
    for i in range3:
        pixels_set(i, BLACK) 
    pixels_show()

def two():
    for i in range1:
        pixels_set(i, WHITE)
    for i in range2:
        pixels_set(i, WHITE)    
    for i in range3:
        pixels_set(i, BLACK) 
    pixels_show()


def three():
    for i in range1:
        pixels_set(i, WHITE)
    for i in range2:
        pixels_set(i, WHITE)    
    for i in range3:
        pixels_set(i, WHITE) 
    pixels_show()

for color in COLORS:       
    pixels_fill(color)
    pixels_show()
    time.sleep(0.1)



#print("fills")
#for color in COLORS:       
#    pixels_fill(color)
#    pixels_show()
#    time.sleep(0.2)

# print("chases")
# for color in COLORS:       
#     color_chase(color, 0.01)

# print("rainbow")
# rainbow_cycle(0)




wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(ssid, password)

max_wait = 10
while max_wait > 0:
    if wlan.status() < 0 or wlan.status() >= 3:
        break
    max_wait -= 1
    print('waiting for connection...')
    time.sleep(1)

if wlan.status() != 3:
    raise RuntimeError('network connection failed')
else:
    print('connected')
    status = wlan.ifconfig()
    print( 'ip = ' + status[0] )

server = AppServer()
server.start(3000)
try:
    while True:
        server.process_all()
        time.sleep(0.3)
except KeyboardInterrupt:
    pass
server.stop()
