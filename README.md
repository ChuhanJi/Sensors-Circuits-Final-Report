# Tilt Whack! – A Motion-Controlled Whac-a-Mole Game  
*A 90s-style motion-reaction handheld game powered by ESP32-C3 & CircuitPython*

---

## 🎮 Overview

**Tilt Whack!** is a retro-inspired motion-controlled handheld game where players tilt, aim, and press to “whack” randomly appearing moles on a **4×4 grid**.  
Developed as a final embedded systems project, the device incorporates multiple sensors and outputs to recreate a nostalgic 90s electronic toy experience.

Gameplay centers around:
- **Tilting** the device to move a cursor  
- **Pressing** the encoder button to whack  
- **Racing against time** to clear each level  
- **Progressing through 10 increasingly challenging stages**

---

## 🕹️ How the Game Works

### Game Loop
1. **Splash Screen** → “Start Game”
2. **Difficulty Select**  
   - Easy  
   - Normal  
   - Hard  
3. **Gameplay (10 Levels)**  
   - Random moles appear on a **4×4 grid**  
   - Players move the cursor by **tilting**:
     - Tilt Up → move cursor up  
     - Tilt Down → move cursor down  
     - Tilt Left → move cursor left  
     - Tilt Right → move cursor right  
   - **Press encoder button** to whack the selected cell  
4. **Feedback**  
   - Correct hit → NeoPixel flashes green  
   - Miss or timeout → NeoPixel flashes red  
5. Clear all scheduled moles → next level  
6. Complete all 10 levels → **Game Win Screen**

---

## 🔧 Input Mapping

| Action | Device Input | Effect |
|--------|--------------|--------|
| Move cursor up | Tilt toward top | Cursor row – 1 |
| Move cursor down | Tilt backward | Cursor row + 1 |
| Move cursor left | Tilt left | Cursor col – 1 |
| Move cursor right | Tilt right | Cursor col + 1 |
| Whack / Select | Press encoder button | Hits mole if present |

---

## ⭐ Difficulty & Level Design

The game features **3 selectable difficulty modes**:

- **Easy**
- **Normal**
- **Hard**

Difficulty affects:
- **Number of moles per level**  
- **Time limit per level**  
- **Scaling rate of difficulty**

### Level Progression (10 Stages)
Each level includes:
- A set number of moles (increasing with level)
- A time limit that grows **tighter each level**
- Difficulty mode that influences mole count
- Instant-fail miss detection (Normal / Hard)

Together, these satisfy all course gameplay requirements:
✔ Multi-level  
✔ Increasing difficulty  
✔ Time-based challenges  
✔ Multi-input game logic  
✔ Motion + button interaction

---

## 🧠 Score System (Extra Credit ✓)

This project includes a **score counter** that increases based on:
- Successful mole hits  
- Level completions  

The final score is displayed on the **Game Result Screen**.

*(Meets the extra credit requirement for scoring: +2 pts)*

---

## 🔌 Hardware Used

- **Xiao ESP32-C3 Microcontroller**  
- **SSD1306 128×64 OLED Display** (I2C)  
- **ADXL345 3-Axis Accelerometer** (I2C)  
- **Rotary Encoder with Push Button**  
- **NeoPixel RGB LED**  
- **LiPo Battery (JST)**  
- **On/Off Power Switch**  
- **Perfboard + Female Headers**  
- **3D Printed Enclosure**

> All required course hardware fully integrated and used in gameplay.

---

## 📡 System Diagram

The device consists of one microcontroller (Xiao ESP32-C3) connected to
motion sensors, human inputs, visual outputs, and a battery power system.

**Power System**
- LiPo Battery → Power Switch → ESP32-C3 BAT
- 3.7V regulated to 3.3V for all components

**Microcontroller (ESP32-C3)**
- Runs game logic (Tilt Whack!)
- Reads sensors + inputs
- Drives OLED + NeoPixel

**Sensors & Inputs**
- ADXL345 (I2C): tilt → cursor movement  
- Rotary Encoder + Button (GPIO): user click → “whack” action

**Outputs**
- SSD1306 OLED (I2C): 4×4 grid, score, timer  
- NeoPixel LED (GPIO): hit/miss feedback

**Data Flow**
- Tilt / Button → ESP32-C3 → Game Logic → OLED + NeoPixel


---

## ⚡ Circuit Diagram

Xiao ESP32-C3
GND, 3V3, BAT, D0, D1, D2, D3, D4 (SDA), D5(SCL), D6

SSD1306 OLED Display
I²C bus — SDA (to D4), SCL (to D5)

ADXL345 Accelerometer
I²C bus — SDA (to D4), SCL (to D5)

Rotary Encoder + Push Button
Phase A/B → D0 / D1
Switch → D2

NeoPixel LED
DIN → D6, powered from 3V3 and GND

LiPo Battery + Power Switch
Battery routed to ESP32-C3 BAT pin through a SPST slide switch

---

## 🧱 Enclosure Design Thought Process

The enclosure was fully **3D printed** and inspired by **90s handheld gaming devices**, with a focus on tilt-based ergonomics.
Key considerations:

### 💡 Design Goals

* **Small, compact form** to support tilt gameplay
* **Comfortable to grip** during fast movement
* **Retro visual style** to match the 90s theme
* Ensure **all components are securely fixed** while remaining serviceable

### 🔧 Engineering Constraints & Solutions

* The enclosure uses a **single outer shell** with hardware mounted inside via **screw-based fixtures**, allowing full disassembly and maintenance.
* All openings were precisely modeled:

  * OLED window
  * Rotary encoder opening
  * Power switch cutout
  * Type-C charging port
  * NeoPixel **direct light aperture**
* Internal cavities were shaped to fit:

  * LiPo battery slot
  * ESP32-C3 + perfboard mount
  * Wire routing channels

### 🛠 Iteration Process

The enclosure underwent **three rounds of print-test-refine** cycles:

1. Adjusting hardware alignment
2. Correcting OLED frame tolerance
3. Increasing wall thickness
4. Refining screw pillars for clean assembly

The final design achieves:

* Accurate alignment between hardware & openings
* Ease of assembly
* Reliable durability during tilt gameplay

---

## 📁 Repository Structure

```
SENSORS-CIRCUITS-PROJECT/
│
├── Documentation/
│ ├── Circuit Diagrams.kicad_sch → Full circuit schematic
│ └── System Diagram.jpg → System block diagram
│
├── src/
│ ├── code.py → Main game logic (Tilt Whack!)
│ └── Library/
│ └── rotary_encoder.py → Custom rotary encoder driver
│
└── README.md → Project overview & documentation
```

---

## 🚀 Running the Game

1. Flash CircuitPython onto Xiao ESP32-C3
2. Copy dependencies into `/lib/`
3. Copy `code.py` to device root
4. Plug in battery and flip power switch
5. Play Tilt Whack!

---

# 🎉 End of README
