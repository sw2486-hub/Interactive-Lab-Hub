# Distributed Interaction

**Shenye Wang**

For submission, replace this section with your documentation!

---

## Prep

1. Pull the new changes
2. Read: [The Presence Table](https://dl.acm.org/doi/10.1145/1935701.1935800) ([video](https://vimeo.com/15932020))

## Overview

Build interactive systems where **multiple devices communicate over a network** using MQTT messaging. Work in teams of 3+ with Raspberry Pis.

**Parts:**
- A: Learn MQTT messaging
- B: Try collaborative pixel grid demo  
- C: Build your own distributed system

---

## Part A: MQTT Messaging

MQTT = lightweight messaging for IoT. Publish/subscribe model with central broker.

**Concepts:**
- **Broker**: `farlab.infosci.cornell.edu:1883`
- **Topic**: Like `IDD/bedroom/temperature` (use `#` wildcard)
- **Publish/Subscribe**: Send and receive messages

**Install MQTT tools on your Pi:**
```bash
sudo apt-get update
sudo apt-get install -y mosquitto-clients
```

**Test it:**

Set the `MQTT_USER` and `MQTT_PASSWORD` environment variables using the credentials supplied in the course instructions before running the commands below.

**Subscribe to messages (listener):**
```bash
mosquitto_sub -h farlab.infosci.cornell.edu -p 1883 -t 'IDD/#' -u "$MQTT_USER" -P "$MQTT_PASSWORD"
```

**Publish a message (sender):**
```bash
mosquitto_pub -h farlab.infosci.cornell.edu -p 1883 -t 'IDD/test/yourname' -m 'Hello!' -u "$MQTT_USER" -P "$MQTT_PASSWORD"
```

> **💡 Tips:**
> - Replace `yourname` with your actual name in the topic
> - Use single quotes around the password: `'MQTT_PASSWORD'`
> - For your own projects, publish under your team's topic space: `IDD/<yourteam>/...` (for example `IDD/team3/bedroom/light`). Everyone shares one broker login, so anything you publish can reach everyone's projects.

**🔧 Debug Tool:** View all MQTT messages in real-time at `http://farlab.infosci.cornell.edu:5001`

![MQTT Explorer showing messages](imgs/MQTT-explorer.png)

**💡 Brainstorm 5 ideas for messaging between devices**

Collaborative Color Mixer
Each Pi reads a colored object and publishes its RGB values to IDD/ourteam/color/<device_id> as {"r":255,"g":0,"b":0}. A shared display combines the colors from all devices. Users work together to create a target color.

Distributed Musical Instrument
Three Pis control different musical features: proximity controls volume, gestures control rhythm, and color controls pitch. Each publishes sensor data under IDD/ourteam/music/<parameter>. A central program combines the messages to produce music that users control together.

Remote Presence Display
Each Pi detects whether someone is nearby and publishes {"present":true} or {"present":false} to IDD/ourteam/presence/<device_id>. Other Pis subscribe and show which locations are occupied, creating a simple sense of connection between separate spaces.

Cooperative Gesture Game
Each Pi detects a player's gesture and publishes {"gesture":"up"} to IDD/ourteam/game/<player_id>/gesture. A game controller sends a target gesture sequence to all devices. Players must perform their gestures in the correct order to complete the challenge.

Shared Room Mood Display
Each Pi measures a different aspect of the environment, such as light, proximity, or movement, and publishes readings under IDD/ourteam/room/<sensor_type>. A central program combines the readings into a room state, such as “quiet” or “active,” and publishes it to IDD/ourteam/room/mood. All Pi screens update to show the shared mood.

Because MQTT does not define message meanings, our team would agree on topic names, device IDs, payload fields, units, and valid values before implementation. This flexibility lets us design custom interactions, but every device must follow the same conventions to interpret messages correctly.

## Part B: Collaborative Pixel Grid

Each Pi = one pixel, controlled by RGB sensor, displayed in real-time grid.

**Architecture:** `Pi (sensor) → MQTT → Server → Web Browser`

**Setup:**

1. **Sensor**

#### Light/Proximity/Gesture sensor (APDS-9960)
We use this sensor [Adafruit APDS-9960](https://www.adafruit.com/product/3595) for this exmaple to detect light (also RGB)
 
<img src="https://cdn-shop.adafruit.com/970x728/3595-06.jpg" width=200>

Connect it to your pi with Qwiic connector


<img src="imgs/IMG_0270.jpg" height="200" />
We need to use the screen to display the color detection, so we need to stop the running piscreen.service to make your screen available again

```bash
# stop the screen service
sudo systemctl stop piscreen.service
```

if you want to restart the screen service
```bash
# start the screen service
sudo systemctl start piscreen.service
```
 
2. **Server** (one person on laptop):
```bash
cd "Lab 6"
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-server.txt
python app.py
```

2. **View in browser:**
   - Grid: `http://farlab.infosci.cornell.edu:5000`
   - Controller: `http://farlab.infosci.cornell.edu:5000/controller`

3. **Pi publisher** (everyone on their Pi):
```bash
# First time setup - create virtual environment
cd "Lab 6"
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-pi.txt

# Run the publisher
python pixel_grid_publisher.py
```

Hold colored objects near sensor to change your pixel!

![Pixel grid with two devices](imgs/two-devices-grid.png)

**📸 Include: Screenshot of grid + photo of your Pi setup**

---
<img width="1280" height="1707" alt="321794172382_ pic" src="https://github.com/user-attachments/assets/511c006d-ebd8-4784-a8bb-c9f63d6dc416" />



https://github.com/user-attachments/assets/95009eee-a4cc-4b49-87d5-eafd7e94d4da






## Part C — Color Cocktail Bar

### 1. What We Built

Color Cocktail Bar is a collaborative game in which three participants use colored objects to create a virtual drink. Each participant uses a Raspberry Pi connected to an APDS-9960 color sensor.

The three stations control different parts of the drink:

| Station | Role | Red | Green | Blue |
| --- | --- | --- | --- | --- |
| A | Base | Strawberry | Green apple | Blueberry |
| B | Flavor | Cherry | Lime | Blue syrup |
| C | Garnish | Paper umbrella | Mint leaves | Star stirrer |

All three participants can interact simultaneously. Each Pi sends its detected color through MQTT, and the selections appear together on a shared webpage.

The webpage displays a target order. Participants coordinate their color choices to select the requested ingredients. When all three selections match the order continuously for two seconds, the game confirms completion and increases the score.

### 2. HTML Webpage: Demo and Live Modes

[View the HTML webpage source](cocktail/templates/color_cocktail_bar.html)

Download the HTML file and open it in a browser to try **Demo** mode. **Live sensors** mode uses the local Flask server and MQTT sensor bridge.

The interface is built in `color_cocktail_bar.html`. It contains a target order, a drink preview, and three station panels.

The order card shows the required base, flavor, and garnish. The drink preview changes as participants select ingredients, while the station panels show each participant’s selection and connection status.

#### Demo Mode

Demo mode allows users to control all three stations through on-screen red, green, and blue buttons. It works without Raspberry Pis or sensors.

This mode helped us develop and test the ingredient mappings, drink visualization, order matching, and scoring before connecting the hardware.

#### Live Mode

Live mode uses color readings from the physical sensors. The manual selection buttons are disabled, and each station is controlled by its corresponding Pi.

Each participant presents a colored object to their sensor. The webpage receives the classified color and updates the ingredient selection and drink preview.

The interface also displays whether each station is online. If a station stops sending messages for five seconds, it is marked offline and its previous selection is excluded from order matching.

The group uses one shared browser as the game screen because orders and scores are currently managed within each browser.

### 3. Demo Screenshots

The following screenshots show the interface in Demo mode, using manual buttons to simulate participant selections.

<!-- Insert actual Demo-mode screenshots here. -->

**Step 1 — Selecting ingredients**

**Step 2 — Matching the order and completing the drink**

<img width="1376" height="717" alt="image" src="https://github.com/user-attachments/assets/0456c663-4883-4a3b-a558-0bca58cfae2d" />


### 4. Python Programs

#### `cocktail_sensor.py`

This program runs on each Raspberry Pi. It reads the APDS-9960 sensor, identifies the presented color, and publishes the result through MQTT.

We calibrated color recognition using readings from red, green, blue, and the background. Instead of selecting whichever raw RGB channel is largest, the program compares normalized RGB proportions with calibrated references.

This was necessary because the largest channel did not always match the object’s perceived color. For example, a blue object could produce a stronger green-channel reading.

The program requires three consecutive classifications before confirming a change, reducing flickering caused by movement or unstable readings. It publishes the current state approximately every 0.5 seconds.

Each station uses a separate topic:

| Station | MQTT Topic |
| --- | --- |
| A | `IDD/sw2486/cocktail/input/A` |
| B | `IDD/sw2486/cocktail/input/B` |
| C | `IDD/sw2486/cocktail/input/C` |

An example message is:

```json
{
  "station": "A",
  "color": "RED",
  "rgb": [131, 44, 36]
}
```

The same program supports all three stations through its station argument and individual calibration settings.

#### `cocktail_server.py`

This program runs on the host Pi and serves the HTML webpage through Flask.

It subscribes to the three stations’ MQTT topics, checks that incoming messages contain valid station identifiers and color states, and forwards the messages to the browser through Server-Sent Events.

The server connects the physical sensor inputs to the webpage. The browser then updates the drink illustration and performs order matching, timing, and scoring.


### 5. Actual Operation Screenshots

The following images document the physical setup and the interface during Live operation.

**Collaborative interaction**

<img width="761" height="600" alt="image" src="https://github.com/user-attachments/assets/30f4f758-074a-491f-889c-d83b6cf20d2d" />

<img width="762" height="617" alt="image" src="https://github.com/user-attachments/assets/56174d4f-23c6-4544-afb2-b197ca4ce06a" />


### 6. Reflection

#### What Worked Well?

Dividing the drink into base, flavor, and garnish gives each participant a clear role. Each person controls one part of the result, while the shared preview makes their combined choices visible.

Separating Demo and Live modes also helped development. We could check the interface and game rules before introducing sensor readings and network communication.

#### What Were the Challenges of Distributed Interaction?

The devices needed to agree on topic names, station identifiers, and message meanings. MQTT transported the messages, but we had to define how each message represented an ingredient selection.

Another challenge was distinguishing a current selection from an old value left by a disconnected device. Regular heartbeat messages and visible connection status helped address this issue.

#### How Did Sensor Events Work?

Each Pi classified its sensor readings locally and repeatedly published its current state. The webpage combined these independent inputs into one drink.

Color recognition depended on lighting, object position, and the sensor itself. Individual calibration and normalized RGB comparisons helped distinguish the tested colors. Requiring three consistent readings reduced brief, unwanted changes.

The two-second matching requirement made order completion more deliberate, although it also introduced a short delay between presenting the correct colors and completing an order.

#### What Would We Improve?

We would improve lighting consistency around the sensors and make the physical station labels more visible.

We would also move the order and score to the server so that participants could open the webpage on separate computers and see the same game session. Currently, the sensor selections are shared, but each browser manages its own order and score.

#### Where Did Computation Happen, and Why?

Color classification happened on each Pi because every sensor needed its own calibration.

The MQTT broker routed messages, and the Flask server validated and forwarded them to the browser.

The browser handled the visual preview, order generation, matching timer, and scoring. This allowed the interface to work independently in Demo mode and then use the same game logic with Live sensor inputs.

No language model was used during gameplay.



Before submitting:
- [ ] Delete prep/instructions above
- [ ] Add YOUR project documentation
- [ ] Include photos/videos/diagrams  
- [ ] Document user testing with non-team members
- [ ] Add reflection on learnings
- [ ] List team names at top

**Your README = story of what YOU built!**

---

Resources: [MQTT Guide](https://www.hivemq.com/mqtt-essentials/) | [Paho Python](https://www.eclipse.org/paho/index.php?page=clients/python/docs/index.php) | [Flask-SocketIO](https://flask-socketio.readthedocs.io/)
