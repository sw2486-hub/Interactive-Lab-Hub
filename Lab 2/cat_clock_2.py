import time
import digitalio
import board
from PIL import Image, ImageDraw, ImageFont
import adafruit_rgb_display.st7789 as st7789


# --------------------------------------------------
# MiniPiTFT setup
# Based on the Lab 2 screen_clock.py starter code
# --------------------------------------------------

cs_pin = digitalio.DigitalInOut(board.D5)
dc_pin = digitalio.DigitalInOut(board.D25)
reset_pin = None

BAUDRATE = 64000000
spi = board.SPI()

disp = st7789.ST7789(
    spi,
    cs=cs_pin,
    dc=dc_pin,
    rst=reset_pin,
    baudrate=BAUDRATE,
    width=135,
    height=240,
    x_offset=53,
    y_offset=40,
)

height = disp.width
width = disp.height

image = Image.new("RGB", (width, height))
rotation = 90
draw = ImageDraw.Draw(image)

font = ImageFont.truetype(
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 17
)

small_font = ImageFont.truetype(
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 12
)

big_font = ImageFont.truetype(
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 20
)


# --------------------------------------------------
# Backlight
# --------------------------------------------------

backlight = digitalio.DigitalInOut(board.D22)
backlight.switch_to_output()
backlight.value = True


# --------------------------------------------------
# MiniPiTFT buttons
# A = Switch Screen
# B = Interact
# --------------------------------------------------

button_a = digitalio.DigitalInOut(board.D23)
button_a.switch_to_input(pull=digitalio.Pull.UP)

button_b = digitalio.DigitalInOut(board.D24)
button_b.switch_to_input(pull=digitalio.Pull.UP)


# --------------------------------------------------
# Cat clock states
# --------------------------------------------------

states = [
    "sleep",
    "meal",
    "play",
    "waiting",
    "meal",
    "play",
    "waiting",
    "meal",
    "sleep"
]

state_index = 0
current_state = states[state_index]

screen = "cat"
message = ""

state_start = time.time()


# --------------------------------------------------
# Draw cat
# --------------------------------------------------

def draw_cat(state):

    # ears
    draw.polygon(
        [(90, 45), (100, 27), (110, 45)],
        fill=(255, 255, 255)
    )

    draw.polygon(
        [(130, 45), (140, 27), (150, 45)],
        fill=(255, 255, 255)
    )

    # face
    draw.ellipse(
        (90, 38, 150, 98),
        outline=(255, 255, 255),
        width=3
    )

    if state == "sleep":

        # closed eyes
        draw.line(
            (103, 62, 112, 62),
            fill=(255, 255, 255),
            width=2
        )

        draw.line(
            (128, 62, 137, 62),
            fill=(255, 255, 255),
            width=2
        )

        draw.text(
            (155, 40),
            "Zzz",
            font=small_font,
            fill=(255, 255, 255)
        )

    else:

        # open eyes
        draw.ellipse(
            (105, 58, 110, 64),
            fill=(255, 255, 255)
        )

        draw.ellipse(
            (130, 58, 135, 64),
            fill=(255, 255, 255)
        )

    # nose
    draw.polygon(
        [(118, 72), (122, 72), (120, 76)],
        fill=(255, 255, 255)
    )

    # mouth
    draw.line(
        (120, 76, 114, 82),
        fill=(255, 255, 255),
        width=2
    )

    draw.line(
        (120, 76, 126, 82),
        fill=(255, 255, 255),
        width=2
    )


# --------------------------------------------------
# Cat screen
# --------------------------------------------------

def draw_cat_screen():

    current_time = time.strftime("%H:%M:%S")

    draw.text(
        (5, 5),
        current_time,
        font=small_font,
        fill=(255, 255, 255)
    )

    draw.text(
        (150, 5),
        "CAT CLOCK",
        font=small_font,
        fill=(255, 255, 255)
    )

    draw_cat(current_state)

    if current_state == "sleep":

        draw.text(
            (75, 105),
            "Sleeping...",
            font=font,
            fill=(255, 255, 255)
        )

    elif current_state == "meal":

        draw.text(
            (65, 102),
            "Time to eat!",
            font=font,
            fill=(255, 255, 255)
        )

        draw.text(
            (5, 120),
            "B: Feed",
            font=small_font,
            fill=(255, 255, 255)
        )

    elif current_state == "play":

        draw.text(
            (72, 102),
            "Let's play!",
            font=font,
            fill=(255, 255, 255)
        )

        draw.text(
            (5, 120),
            "B: Play",
            font=small_font,
            fill=(255, 255, 255)
        )

    elif current_state == "waiting":

        draw.text(
            (78, 102),
            "Waiting...",
            font=font,
            fill=(255, 255, 255)
        )

    if message != "":
        draw.rectangle(
            (35, 85, 205, 112),
            fill=(0, 0, 0)
        )

        draw.text(
            (45, 90),
            message,
            font=small_font,
            fill=(255, 255, 255)
        )

    draw.text(
        (165, 120),
        "A: Schedule",
        font=small_font,
        fill=(255, 255, 255)
    )


# --------------------------------------------------
# Schedule screen
# --------------------------------------------------

def draw_schedule():

    draw.text(
        (55, 5),
        "CAT DAILY ROUTINE",
        font=font,
        fill=(255, 255, 255)
    )

    draw.text(
        (20, 35),
        "8:00 AM   Meal",
        font=small_font,
        fill=(255, 255, 255)
    )

    draw.text(
        (20, 52),
        "Morning   Play",
        font=small_font,
        fill=(255, 255, 255)
    )

    draw.text(
        (20, 69),
        "Daytime   Sleep / Wait",
        font=small_font,
        fill=(255, 255, 255)
    )

    draw.text(
        (20, 86),
        "5:30 PM   Meal",
        font=small_font,
        fill=(255, 255, 255)
    )

    draw.text(
        (20, 103),
        "11:30 PM  Meal + Sleep",
        font=small_font,
        fill=(255, 255, 255)
    )

    draw.text(
        (165, 120),
        "A: Cat",
        font=small_font,
        fill=(255, 255, 255)
    )


# --------------------------------------------------
# Move to next state
# --------------------------------------------------

def next_state():

    global state_index
    global current_state
    global state_start
    global message

    state_index += 1

    if state_index >= len(states):
        state_index = 0

    current_state = states[state_index]

    state_start = time.time()
    message = ""


# --------------------------------------------------
# Main loop
# --------------------------------------------------

while True:

    draw.rectangle(
        (0, 0, width, height),
        outline=0,
        fill=(0, 0, 0)
    )

    # Button A switches between screens
    if not button_a.value:

        if screen == "cat":
            screen = "schedule"
        else:
            screen = "cat"

        time.sleep(0.25)

    # Button B interacts with the cat
    if screen == "cat" and not button_b.value:

        if current_state == "meal":

            message = "Yummy! Thank you!"
            disp.image(image, rotation)

            time.sleep(1)

            next_state()

        elif current_state == "play":

            message = "That was fun!"
            disp.image(image, rotation)

            time.sleep(1)

            next_state()

        time.sleep(0.25)

    # Demo mode:
    # Sleep and waiting automatically move forward
    # after a few seconds.
    if current_state == "sleep":

        if time.time() - state_start > 4:
            next_state()

    elif current_state == "waiting":

        if time.time() - state_start > 4:
            next_state()

    # Draw selected screen
    if screen == "cat":
        draw_cat_screen()
    else:
        draw_schedule()

    disp.image(image, rotation)

    time.sleep(0.05)
