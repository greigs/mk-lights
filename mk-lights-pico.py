# Example using PIO to drive a set of WS2812 LEDs.

from sys import stdin
import array, time
from machine import Pin
import rp2
import micropython
import uselect

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


def read_serial_input():
    """
    Buffers serial input.
    Writes it to input_line_this_tick when we have a full line.
    Clears input_line_this_tick otherwise.
    """
    # stdin.read() is blocking which means we hang here if we use it. Instead use select to tell us if there's anything available
    # note: select() is deprecated. Replace with Poll() to follow best practises
    select_result = uselect.select([stdin], [], [], 0)
    while select_result[0]:
        # there's no easy micropython way to get all the bytes.
        # instead get the minimum there could be and keep checking with select and a while loop
        input_character = stdin.read(1)
        print(input_character)
        # add to the buffer
        buffered_input.append(input_character)
        # check if there's any input remaining to buffer
        select_result = uselect.select([stdin], [], [], 0)
    # if a full line has been submitted
    if TERMINATOR in buffered_input:
        line_ending_index = buffered_input.index(TERMINATOR)
        # make it available
        input_line_this_tick = "".join(buffered_input[:line_ending_index])
        # remove it from the buffer.
        # If there's remaining data, leave that part. This removes the earliest line so should allow multiple lines buffered in a tick to work.
        # however if there are multiple lines each tick, the buffer will continue to grow.
        if line_ending_index < len(buffered_input):
            buffered_input = buffered_input[line_ending_index + 1 :]
        else:
            buffered_input = []
    # otherwise clear the last full line so subsequent ticks can infer the same input is new input (not cached)
    else:
        input_line_this_tick = ""

def led_on():
    led = Pin(25, Pin.OUT) # version for Pico 
    led.value(1)

def led_off():
    led = Pin(25, Pin.OUT) # version for Pico
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
while True:
    read_serial_input()


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
