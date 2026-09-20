import time
import digitalio
import board
from PIL import Image, ImageDraw, ImageFont
import adafruit_rgb_display.st7789 as st7789

# MiniPiTFT display setup
# Based on the Lab 2 screen_clock.py starter code
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

# Landscape screen
height = disp.width
width = disp.height
image = Image.new("RGB", (width, height))
rotation = 90
draw = ImageDraw.Draw(image)

font = ImageFont.truetype(
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18
)
small_font = ImageFont.truetype(
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 13
)

# Turn on backlight
backlight = digitalio.DigitalInOut(board.D22)
backlight.switch_to_output()
backlight.value = True

# MiniPiTFT button B (GPIO 24)
interact_button = digitalio.DigitalInOut(board.D24)
interact_button.switch_to_input(pull=digitalio.Pull.UP)

state = "meal"


def draw_cat():
    # Simple cat face
    draw.polygon([(90, 48), (100, 30), (110, 48)],
                 fill=(255, 255, 255))
    draw.polygon([(130, 48), (140, 30), (150, 48)],
                 fill=(255, 255, 255))

    draw.ellipse((90, 40, 150, 100),
                 outline=(255, 255, 255), width=3)

    # Eyes
    draw.ellipse((105, 60, 110, 65), fill=(255, 255, 255))
    draw.ellipse((130, 60, 135, 65), fill=(255, 255, 255))

    # Nose
    draw.polygon([(118, 72), (122, 72), (120, 76)],
                 fill=(255, 255, 255))

    # Mouth
    draw.line((120, 76, 114, 82), fill=(255, 255, 255), width=2)
    draw.line((120, 76, 126, 82), fill=(255, 255, 255), width=2)


while True:
    draw.rectangle((0, 0, width, height), outline=0, fill=(0, 0, 0))

    current_time = time.strftime("%H:%M:%S")
    draw.text((5, 5), current_time, font=small_font,
              fill=(255, 255, 255))

    draw_cat()

    if state == "meal":
        draw.text((65, 105), "Time to eat!",
                  font=font, fill=(255, 255, 255))
        draw.text((5, 118), "Press B to feed",
                  font=small_font, fill=(255, 255, 255))

        if not interact_button.value:
            state = "thanks"
            state_start = time.time()
            time.sleep(0.2)

    elif state == "thanks":
        draw.text((35, 105), "Yummy! Thank you!",
                  font=font, fill=(255, 255, 255))

        if time.time() - state_start > 2:
            state = "play"

    elif state == "play":
        draw.text((70, 105), "Let's play!",
                  font=font, fill=(255, 255, 255))

    disp.image(image, rotation)
    time.sleep(0.05)
