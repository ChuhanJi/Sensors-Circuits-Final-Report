import board
import busio
import displayio
import terminalio
from adafruit_display_text import label
import i2cdisplaybus
import adafruit_displayio_ssd1306
import time
from rotary_encoder import RotaryEncoder
import digitalio
import adafruit_adxl34x
import math
from rainbowio import colorwheel
import neopixel
import random

# 初始化显示
displayio.release_displays()
i2c = busio.I2C(board.SCL, board.SDA)
display_bus = i2cdisplaybus.I2CDisplayBus(i2c, device_address=0x3C)
display = adafruit_displayio_ssd1306.SSD1306(display_bus, width=128, height=64)

# 初始化旋转编码器（CLK=D0, DT=D1）
encoder = RotaryEncoder(board.D0, board.D1, pulses_per_detent=1)

# 初始化按钮（D2引脚）
button = digitalio.DigitalInOut(board.D2)
button.direction = digitalio.Direction.INPUT
button.pull = digitalio.Pull.UP

# 初始化加速度计
accelerometer = adafruit_adxl34x.ADXL345(i2c)

# 初始化NeoPixel (D6引脚)
pixel_pin = board.D6
num_pixels = 1
pixels = neopixel.NeoPixel(pixel_pin, num_pixels, brightness=0.3, auto_write=False)

# 游戏状态
STATE_SPLASH = 0
STATE_DIFFICULTY_SELECT = 1
STATE_GAME_START = 2
STATE_GAME_PLAYING = 3
STATE_GAME_RESULT = 4

current_state = STATE_SPLASH
selected_difficulty = 0
difficulties = ["EASY", "NORMAL", "HARD"]

# 游戏变量
score = 0
current_level = 1
total_levels = 10
moles_in_level = 0
remaining_moles = 0  # 跟踪剩余土拨鼠数量
selected_cell = [0, 0]  # 当前选中的单元格 [row, col]
game_grid = [[0 for _ in range(4)] for _ in range(4)]  # 4x4网格，0=空，1=土拨鼠

# 时间限制相关变量
base_time_limit = 30  # 基础时间限制30秒
time_increment = 5    # 每关增加5秒
level_start_time = 0  # 关卡开始时间
time_remaining = 0    # 剩余时间

# 编码器位置跟踪
encoder_position = 0
last_encoder_position = 0
last_encoder_time = 0
encoder_debounce_ms = 80

# 方向检测相关变量
angle_threshold = 15  # 降低阈值提高灵敏度
duration_threshold = 0.2  # 缩短维持时间
cooldown_time = 0.3  # 缩短冷却时间提高游戏响应
direction_start_time = {
    "up": None,
    "down": None, 
    "left": None,
    "right": None
}
last_direction_time = 0
direction_cooldown = 0.5  # 方向移动冷却时间

# 按钮状态
button_pressed = False
last_button_value = button.value

# 结果界面变量
result_selection = 0
game_success = False  # 记录游戏是否成功完成
game_time_out = False  # 记录是否因超时失败

# 选择冷却时间
last_selection_change = 0
selection_cooldown = 0.5  # 0.5秒冷却时间

# LED闪烁控制
led_flash_state = False
last_led_flash_time = 0
led_flash_interval = 0.3  # LED闪烁间隔

def calculate_angles(x, y, z):
    """计算X轴和Y轴的角度（相对于重力方向）"""
    angle_x = math.atan2(x, math.sqrt(y*y + z*z)) * 180 / math.pi
    angle_y = math.atan2(y, math.sqrt(x*x + z*z)) * 180 / math.pi
    return angle_x, angle_y

def check_direction(angle_x, angle_y, current_time):
    """检测四个方向是否满足条件"""
    # 检查方向移动冷却
    if current_time - last_direction_time < direction_cooldown:
        return None
    
    direction = None
    
    # 向上移动（X轴负方向）- 对应网格上移
    if angle_x < -angle_threshold:
        if direction_start_time["up"] is None:
            direction_start_time["up"] = current_time
        elif current_time - direction_start_time["up"] >= duration_threshold:
            direction = "UP"
    else:
        direction_start_time["up"] = None
    
    # 向下移动（X轴正方向）- 对应网格下移
    if angle_x > angle_threshold:
        if direction_start_time["down"] is None:
            direction_start_time["down"] = current_time
        elif current_time - direction_start_time["down"] >= duration_threshold:
            direction = "DOWN"
    else:
        direction_start_time["down"] = None
    
    # 向左移动（Y轴正方向）- 对应网格左移
    if angle_y > angle_threshold:
        if direction_start_time["left"] is None:
            direction_start_time["left"] = current_time
        elif current_time - direction_start_time["left"] >= duration_threshold:
            direction = "LEFT"
    else:
        direction_start_time["left"] = None
    
    # 向右移动（Y轴负方向）- 对应网格右移
    if angle_y < -angle_threshold:
        if direction_start_time["right"] is None:
            direction_start_time["right"] = current_time
        elif current_time - direction_start_time["right"] >= duration_threshold:
            direction = "RIGHT"
    else:
        direction_start_time["right"] = None
    
    return direction

def rainbow_cycle(wait):
    """彩虹色渐变效果"""
    for j in range(255):
        for i in range(num_pixels):
            rc_index = (i * 256 // num_pixels) + j
            pixels[i] = colorwheel(rc_index & 255)
        pixels.show()
        time.sleep(wait)

def show_rainbow_startup():
    """开机彩虹闪烁3秒"""
    start_time = time.monotonic()
    while time.monotonic() - start_time < 3:
        rainbow_cycle(0.02)

def set_led_color(color):
    """设置LED颜色"""
    pixels.fill(color)
    pixels.show()

def flash_led(color, times=3, duration=0.2):
    """LED闪烁效果"""
    for _ in range(times):
        set_led_color(color)
        time.sleep(duration)
        set_led_color((0, 0, 0))
        time.sleep(duration)

def update_led_flash(current_time):
    """更新LED闪烁状态"""
    global led_flash_state, last_led_flash_time
    
    if current_time - last_led_flash_time >= led_flash_interval:
        led_flash_state = not led_flash_state
        last_led_flash_time = current_time
        
        if game_success:
            # 成功时使用彩虹色闪烁
            if led_flash_state:
                rainbow_cycle(0.01)  # 短暂彩虹效果
            else:
                set_led_color((0, 0, 0))
        else:
            # 失败时使用红色闪烁
            if led_flash_state:
                set_led_color((255, 0, 0))
            else:
                set_led_color((0, 0, 0))

def calculate_time_limit():
    """计算当前关卡的时间限制"""
    return base_time_limit + (current_level - 1) * time_increment

def generate_moles():
    """根据当前关卡生成土拨鼠位置"""
    global moles_in_level, game_grid, remaining_moles, level_start_time, time_remaining
    
    # 根据难度和关卡决定土拨鼠数量
    base_moles = min(current_level, 5)  # 最大5个
    
    # 根据难度调整数量
    if difficulties[selected_difficulty] == "EASY":
        moles_in_level = max(1, base_moles - 1)
    elif difficulties[selected_difficulty] == "NORMAL":
        moles_in_level = base_moles
    else:  # HARD
        moles_in_level = min(5, base_moles + 1)
    
    # 重置网格
    game_grid = [[0 for _ in range(4)] for _ in range(4)]
    remaining_moles = moles_in_level
    
    # 设置关卡开始时间和时间限制
    level_start_time = time.monotonic()
    time_remaining = calculate_time_limit()
    
    # 随机放置土拨鼠
    positions = []
    for _ in range(moles_in_level):
        while True:
            row = random.randint(0, 3)
            col = random.randint(0, 3)
            if (row, col) not in positions:
                positions.append((row, col))
                game_grid[row][col] = 1
                break

def create_splash_screen():
    """创建开机画面"""
    group = displayio.Group()
    title_label = label.Label(terminalio.FONT, text="WHACK A MOLE", x=30, y=15, scale=1)
    group.append(title_label)
    version_label = label.Label(terminalio.FONT, text="DORIS", x=50, y=30, scale=1)
    group.append(version_label)
    hint_label = label.Label(terminalio.FONT, text="START GAME", x=35, y=45, scale=1)
    group.append(hint_label)
    return group

def create_difficulty_screen():
    """创建难度选择界面"""
    group = displayio.Group()
    title_label = label.Label(terminalio.FONT, text="SELECT MODE", x=30, y=10, scale=1)
    group.append(title_label)
    
    y_pos = 30
    for i, difficulty in enumerate(difficulties):
        prefix = "> " if i == selected_difficulty else "  "
        diff_label = label.Label(terminalio.FONT, text=f"{prefix}{difficulty}", x=35, y=y_pos, scale=1)
        group.append(diff_label)
        y_pos += 15
    
    return group

def create_game_start_screen():
    """创建游戏开始界面"""
    group = displayio.Group()
    difficulty_text = f"MODE: {difficulties[selected_difficulty]}"
    diff_label = label.Label(terminalio.FONT, text=difficulty_text, x=35, y=20, scale=1)
    group.append(diff_label)
    start_label = label.Label(terminalio.FONT, text="GAME START!", x=30, y=40, scale=1)
    group.append(start_label)
    back_label = label.Label(terminalio.FONT, text="PRESS TO MENU", x=25, y=55, scale=1)
    group.append(back_label)
    return group

def create_game_screen():
    """创建游戏界面"""
    group = displayio.Group()
    
    # 左侧：显示关卡和分数（使用缩写）
    level_text = f"Lv:{current_level}/{total_levels}"
    level_label = label.Label(terminalio.FONT, text=level_text, x=5, y=10, scale=1)
    group.append(level_label)
    
    score_text = f"Sc:{score}"
    score_label = label.Label(terminalio.FONT, text=score_text, x=5, y=25, scale=1)
    group.append(score_label)
    
    # 显示剩余土拨鼠数量
    moles_text = f"Left:{remaining_moles}"
    moles_label = label.Label(terminalio.FONT, text=moles_text, x=5, y=40, scale=1)
    group.append(moles_label)
    
    # 显示剩余时间
    time_text = f"Time:{int(time_remaining)}s"
    time_label = label.Label(terminalio.FONT, text=time_text, x=5, y=55, scale=1)
    group.append(time_label)
    
    # 右侧：绘制4x4网格
    cell_size = 10  # 格子大小
    start_x = 70   # 从屏幕中间偏右开始
    start_y = 10   # 从顶部开始
    
    for row in range(4):
        for col in range(4):
            x_pos = start_x + col * (cell_size + 4)  # 增加间距
            y_pos = start_y + row * (cell_size + 4)
            
            # 显示土拨鼠或空位 - 使用标准ASCII字符
            if game_grid[row][col] == 1:
                # 土拨鼠用'O'表示
                mole_label = label.Label(terminalio.FONT, text="O", x=x_pos+2, y=y_pos+6, scale=1)
                group.append(mole_label)
            else:
                # 空位用'.'表示
                empty_label = label.Label(terminalio.FONT, text=".", x=x_pos+2, y=y_pos+6, scale=1)
                group.append(empty_label)
            
            # 选中的单元格用方框表示
            if row == selected_cell[0] and col == selected_cell[1]:
                # 使用方括号作为选择框
                box_left = label.Label(terminalio.FONT, text="[", x=x_pos-1, y=y_pos+6, scale=1)
                box_right = label.Label(terminalio.FONT, text="]", x=x_pos+7, y=y_pos+6, scale=1)
                group.append(box_left)
                group.append(box_right)
    
    return group

def create_result_screen():
    """创建结果界面"""
    group = displayio.Group()
    
    if game_success:
        result_label = label.Label(terminalio.FONT, text="GAME WIN!", x=35, y=15, scale=1)
        group.append(result_label)
    else:
        if game_time_out:
            result_label = label.Label(terminalio.FONT, text="TIME OUT!", x=35, y=15, scale=1)
        else:
            result_label = label.Label(terminalio.FONT, text="GAME OVER!", x=35, y=15, scale=1)
        group.append(result_label)
    
    score_label = label.Label(terminalio.FONT, text=f"SCORE: {score}", x=40, y=35, scale=1)
    group.append(score_label)
    
    # 选项 - 调整位置确保完全显示
    options = ["RESTART", "MAIN MENU"]
    
    for i, option in enumerate(options):
        prefix = "> " if i == result_selection else "  "
        # 调整Y位置，确保两个选项都在屏幕内
        option_label = label.Label(terminalio.FONT, text=f"{prefix}{option}", x=25, y=50 + i*10, scale=1)
        group.append(option_label)
    
    return group

def move_selection(direction):
    """移动选择框"""
    global last_direction_time
    row, col = selected_cell
    
    if direction == "UP":
        selected_cell[0] = max(0, row - 1)
    elif direction == "DOWN":
        selected_cell[0] = min(3, row + 1)
    elif direction == "LEFT":
        selected_cell[1] = max(0, col - 1)
    elif direction == "RIGHT":
        selected_cell[1] = min(3, col + 1)
    
    last_direction_time = time.monotonic()
    print(f"Moved {direction} to [{selected_cell[0]}, {selected_cell[1]}]")

def check_hit():
    """检查是否击中土拨鼠"""
    row, col = selected_cell
    hit = game_grid[row][col] == 1
    return hit

def remove_mole(row, col):
    """移除土拨鼠"""
    global remaining_moles
    if game_grid[row][col] == 1:
        game_grid[row][col] = 0
        remaining_moles -= 1
        print(f"Mole removed at [{row}, {col}], {remaining_moles} left")
        return True
    return False

def advance_level():
    """进入下一关"""
    global current_level, score
    if current_level < total_levels:
        current_level += 1
        score += 10  # 每关10分
        return True
    else:
        return False

def reset_game():
    """重置游戏"""
    global score, current_level, selected_cell, result_selection, last_selection_change
    score = 0
    current_level = 1
    selected_cell = [0, 0]
    result_selection = 0  # 重置结果选择
    last_selection_change = 0  # 重置选择冷却时间

# 初始显示开机画面
splash_group = create_splash_screen()
display.root_group = splash_group

# 开机彩虹闪烁
show_rainbow_startup()
set_led_color((0, 0, 0))  # 关闭LED

print("Game Starting...")
print("Current state: SPLASH")
print("Press button to enter difficulty selection")

# 主游戏循环
last_display_update = 0
while True:
    current_time = time.monotonic()
    current_time_ms = current_time * 1000
    
    # 检查旋转编码器
    encoder_changed = encoder.update()
    
    # 更新编码器位置（带滤波）
    if encoder_changed:
        if current_time_ms - last_encoder_time > encoder_debounce_ms:
            encoder_position = encoder.position
            last_encoder_time = current_time_ms
    
    # 按钮检测
    current_button_value = button.value
    if last_button_value and not current_button_value:
        button_pressed = True
        print("Button pressed!")
    last_button_value = current_button_value
    
    # 状态机处理
    if current_state == STATE_SPLASH:
        if button_pressed:
            current_state = STATE_DIFFICULTY_SELECT
            encoder_position = 0
            last_encoder_position = 0
            last_encoder_time = current_time_ms
            display.root_group = create_difficulty_screen()
            print("State changed: SPLASH -> DIFFICULTY_SELECT")
            button_pressed = False
    
    elif current_state == STATE_DIFFICULTY_SELECT:
        # 处理编码器旋转选择难度
        if encoder_position != last_encoder_position:
            selected_difficulty = (selected_difficulty + 1) % len(difficulties)
            display.root_group = create_difficulty_screen()
            print(f"Difficulty selected: {difficulties[selected_difficulty]}")
            last_encoder_position = encoder_position
        
        # 处理按钮确认
        if button_pressed:
            current_state = STATE_GAME_START
            display.root_group = create_game_start_screen()
            print(f"State changed: DIFFICULTY_SELECT -> GAME_START")
            print(f"Confirmed difficulty: {difficulties[selected_difficulty]}")
            button_pressed = False
    
    elif current_state == STATE_GAME_START:
        if button_pressed:
            current_state = STATE_GAME_PLAYING
            reset_game()
            generate_moles()
            display.root_group = create_game_screen()
            print("State changed: GAME_START -> GAME_PLAYING")
            print(f"Level {current_level}, Moles: {moles_in_level}, Time limit: {calculate_time_limit()}s")
            button_pressed = False
    
    elif current_state == STATE_GAME_PLAYING:
        # 更新时间显示
        elapsed_time = current_time - level_start_time
        time_remaining = max(0, calculate_time_limit() - elapsed_time)
        
        # 每0.5秒更新一次显示，避免过于频繁的刷新
        if current_time - last_display_update > 0.5:
            display.root_group = create_game_screen()
            last_display_update = current_time
        
        # 检查时间是否用完
        if time_remaining <= 0:
            # 时间用完，游戏结束
            game_success = False
            game_time_out = True
            current_state = STATE_GAME_RESULT
            display.root_group = create_result_screen()
            print("Game over - time out!")
            continue
        
        # 获取加速度计数据并处理方向控制
        x, y, z = accelerometer.acceleration
        angle_x, angle_y = calculate_angles(x, y, z)
        direction = check_direction(angle_x, angle_y, current_time)
        
        # 处理方向移动
        if direction:
            move_selection(direction)
            display.root_group = create_game_screen()  # 更新显示
            print(f"Direction detected: {direction}, Angles: X={angle_x:.1f}, Y={angle_y:.1f}")
        
        # 处理按钮击打
        if button_pressed:
            if check_hit():
                # 击中土拨鼠，移除它
                row, col = selected_cell
                if remove_mole(row, col):
                    display.root_group = create_game_screen()  # 更新显示
                    print(f"Hit! {remaining_moles} moles remaining")
                    
                    # 检查是否所有土拨鼠都被击中
                    if remaining_moles == 0:
                        print("All moles hit! Advancing to next level...")
                        
                        # 闪烁LED三次表示关卡完成
                        flash_led((0, 255, 0), times=3, duration=0.2)  # 绿色闪烁
                        
                        if advance_level():
                            # 进入下一关
                            generate_moles()
                            display.root_group = create_game_screen()
                            print(f"Level advanced to {current_level}, Moles: {moles_in_level}, Time limit: {calculate_time_limit()}s")
                        else:
                            # 所有关卡完成
                            game_success = True
                            game_time_out = False
                            current_state = STATE_GAME_RESULT
                            display.root_group = create_result_screen()
                            print("Game completed successfully!")
            else:
                # 未击中，游戏结束
                game_success = False
                game_time_out = False
                current_state = STATE_GAME_RESULT
                display.root_group = create_result_screen()
                print("Game over - missed!")
            
            button_pressed = False
    
    elif current_state == STATE_GAME_RESULT:
        # 更新LED闪烁效果
        update_led_flash(current_time)
        
        # 处理结果界面的选项选择 - 添加冷却时间
        if encoder_position != last_encoder_position:
            # 检查是否在冷却时间内
            if current_time - last_selection_change >= selection_cooldown:
                # 计算旋转方向并更新选择
                delta = encoder_position - last_encoder_position
                if delta > 0:
                    result_selection = (result_selection + 1) % 2
                else:
                    result_selection = (result_selection - 1) % 2
                    
                # 确保结果选择在有效范围内
                if result_selection < 0:
                    result_selection = 1
                    
                display.root_group = create_result_screen()
                last_encoder_position = encoder_position
                last_selection_change = current_time  # 更新最后一次选择改变时间
                print(f"Result selection changed to: {result_selection}")
            else:
                # 在冷却时间内，忽略旋转但更新编码器位置
                last_encoder_position = encoder_position
                print(f"Ignored rotation during cooldown, time left: {selection_cooldown - (current_time - last_selection_change):.2f}s")
        
        # 处理按钮确认
        if button_pressed:
            if result_selection == 0:  # RESTART
                current_state = STATE_GAME_PLAYING
                reset_game()
                generate_moles()
                display.root_group = create_game_screen()
                set_led_color((0, 0, 0))  # 关闭LED
                print("Restarting game...")
            else:  # MAIN MENU
                current_state = STATE_SPLASH
                display.root_group = create_splash_screen()
                set_led_color((0, 0, 0))  # 关闭LED
                print("Returning to main menu...")
            
            button_pressed = False
    
    time.sleep(0.05)  # 缩短延迟提高响应速度

