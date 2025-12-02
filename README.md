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

*(To be added as system_diagram.png once created)*

```text
        +------------------+
        |   Xiao ESP32-C3  |
        +------------------+
              |      |      
           I2C|      |GPIO
              |      |
   +----------------+----------------+
   |                                |
[SSD1306 OLED]                [ADXL345 Accelerometer]
                                      
         | GPIO
         v
   [Rotary Encoder + Button]

         | GPIO
         v
      [NeoPixel LED]

         | JST + Switch
         v
      [LiPo Battery]
