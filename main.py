import pygame
import random
import math
from array import array
import os
import sys

pygame.init()
pygame.mixer.init()

sample_rate = 44100
frequency = 440
duration = 0.2
samples = array('h')
for i in range(int(sample_rate * duration)):
    sample = int(32767 * math.sin(2 * math.pi * frequency * i / sample_rate))
    samples.append(sample)
    samples.append(sample)
beep_sound = pygame.mixer.Sound(buffer=samples)

pygame.display.set_caption("Chipper, Chip8 Emulator")
screen = pygame.display.set_mode((640, 320))

display = [[0 for x in range(64)] for y in range(32)]

running = True

cpu_speed = 10

memory = bytearray(4096)

fontset = [
    0xF0, 0x90, 0x90, 0x90, 0xF0, #0
    0x20, 0x60, 0x20, 0x20, 0x70, #1
    0xF0, 0x10, 0xF0, 0x80, 0xF0, #2
    0xF0, 0x10, 0xF0, 0x10, 0xF0, #3
    0x90, 0x90, 0xF0, 0x10, 0x10, #4
    0xF0, 0x80, 0xF0, 0x10, 0xF0, #5
    0xF0, 0x80, 0xF0, 0x90, 0xF0, #6
    0xF0, 0x10, 0x20, 0x40, 0x40, #7
    0xF0, 0x90, 0xF0, 0x90, 0xF0, #8
    0xF0, 0x90, 0xF0, 0x10, 0xF0, #9
    0xF0, 0x90, 0xF0, 0x90, 0x90, #A
    0xE0, 0x90, 0xE0, 0x90, 0xE0, #B
    0xF0, 0x80, 0x80, 0x80, 0xF0, #C
    0xE0, 0x90, 0x90, 0x90, 0xE0, #D
    0xF0, 0x80, 0xF0, 0x80, 0xF0, #E
    0xF0, 0x80, 0xF0, 0x80, 0x80, #F
]

for i in range(len(fontset)):
    memory[0x50 + i] = fontset[i]

rom_path = os.path.join(
    getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__))),
    "pong.rom"
)

with open(rom_path, "rb") as rom_file:
    rom_data = rom_file.read()

for i in range(len(rom_data)):
    memory[0x200 + i] = rom_data[i]

registers = bytearray(16)

keys = [0] * 16

keys_mapping = {
    pygame.K_1: 0x1,
    pygame.K_2: 0x2,
    pygame.K_3: 0x3,
    pygame.K_4: 0xC,

    pygame.K_q: 0x4,
    pygame.K_w: 0x5,
    pygame.K_e: 0x6,
    pygame.K_r: 0xD,

    pygame.K_a: 0x7,
    pygame.K_s: 0x8,
    pygame.K_d: 0x9,
    pygame.K_f: 0xE,

    pygame.K_z: 0xA,
    pygame.K_x: 0x0,
    pygame.K_c: 0xB,
    pygame.K_v: 0xF
}

index = 0

stack = []

pc = 0x200

delay_timer = 0

sound_timer = 0

clock = pygame.time.Clock()

last_timer_tick = pygame.time.get_ticks()

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key in keys_mapping:
                keys[keys_mapping[event.key]] = 1
        elif event.type == pygame.KEYUP:
            if event.key in keys_mapping:
                keys[keys_mapping[event.key]] = 0
    current_ticks = pygame.time.get_ticks()
    if current_ticks - last_timer_tick >= 1000 / 60:
        if delay_timer > 0:
            delay_timer -= 1
        if sound_timer > 0:
            sound_timer -= 1
            if sound_timer == 0:
                beep_sound.stop()
        last_timer_tick += 1000 / 60
    for cycle in range(cpu_speed):
        if pc < 0 or pc >= len(memory) -1:
            print("Error! counter out of memory: ", hex(pc))
            running = False
            break
        opcode = (memory[pc] << 8) | memory[pc + 1]
        x = (opcode & 0x0F00) >> 8
        nn = opcode & 0x00FF
        y = (opcode & 0x00F0) >> 4
        n = opcode & 0x000F
        if (opcode & 0xF000) == 0xB000:
            pc = (opcode & 0x0FFF) + registers[0]
        elif (opcode & 0xF000) == 0x1000:
            pc = opcode & 0x0FFF
        elif (opcode & 0xF00F) == 0x8004:
            total = registers[x] + registers[y]
            registers[x] = total & 0xFF
            registers[0xF] = 1 if total > 0xFF else 0
        elif (opcode & 0xF00F) == 0x8005:
            result = registers[x] - registers[y]
            registers[x] = result & 0xFF
            registers[0xF] = 1 if result >= 0 else 0
        elif (opcode & 0xF00F) == 0x8001:
            registers[x] = registers [x] | registers[y]
        elif (opcode & 0xF00F) == 0x8002:
            registers[x] = registers [x] & registers[y]
        elif (opcode & 0xF00F) == 0x8003:
            registers[x] = registers [x] ^ registers[y]
        elif (opcode & 0xF00F) == 0x8006:
            result = registers[x]
            registers[x] = result >> 1
            registers[0xF] = result & 0x1
        elif (opcode & 0xF00F) == 0x800E:
            result = registers[x]
            registers[x] = (result << 1) & 0xFF
            registers[0xF] = 1 if result & 0x80 else 0
        elif (opcode & 0xF000) == 0x3000:
            if registers[x] == nn:
                pc += 2
        elif (opcode & 0xF000) == 0x4000:
            if registers[x] != nn:
                pc += 2
        elif (opcode & 0xF00F) == 0x5000:
            if registers[x] == registers[y]:
                pc += 2
        elif (opcode & 0xF00F) == 0x9000:
            if registers[x] != registers[y]:
                pc += 2
        elif (opcode & 0xF000) == 0x7000:
            registers[x] = (registers[x] + nn) & 0xFF
        elif (opcode & 0xF00F) == 0x8000:
            registers[x] = registers[y]
        elif (opcode & 0xF00F) == 0x8007:
            result = registers[y] - registers[x]
            registers[x] = result & 0xFF
            registers[0xF] = 1 if result >= 0 else 0
        elif opcode == 0x00E0:
            for row in range(32):
                for col in range(64):
                    display[row][col] = 0
        elif (opcode & 0xF000) == 0xA000:
            index = opcode & 0x0FFF
        elif (opcode & 0xF000) == 0x2000:
            if len(stack) >= 16:
                print("Error! Stack overflow")
                running = False
                break
            stack.append(pc + 2)
            pc = opcode & 0x0FFF
        elif opcode == 0x00EE:
            if stack:
                pc = stack.pop()
            else:
                print("Error: Return instruction with empty stack")
                running = False
                break
        elif (opcode & 0xF000) == 0xC000:
            registers[x] = random.randint(0, 255) & nn
        elif (opcode & 0xF000) == 0xD000:
            if index + n > len(memory):
                print("Error: Sprite extends beyond memory")
                running = False
                break
            registers[0xF] = 0
            for row in range(n):
                sprite_byte = memory[index + row]
                for col in range(8):
                    if sprite_byte & (0x80 >> col):
                        pixel_x = (registers[x] + col) % 64
                        pixel_y = (registers[y] + row) % 32
                        if display[pixel_y][pixel_x] == 1:
                            registers[0xF] = 1
                        display[pixel_y][pixel_x] ^= 1
        elif (opcode & 0xF000) == 0x6000:
            registers[x] = nn
        elif (opcode & 0xF0FF) == 0xF01E:
            index += registers[x]
        elif (opcode & 0xF0FF) == 0xF007:
            registers[x] = delay_timer
        elif (opcode & 0xF0FF) == 0xF015:
            delay_timer = registers[x]
        elif (opcode & 0xF0FF) == 0xF018:
            sound_timer = registers[x]
            if sound_timer > 0:
                beep_sound.play(-1)
            else:
                beep_sound.stop()
        elif (opcode & 0xF0FF) == 0xF033:
            if index + 3 > len(memory):
                print("error: BCD operation exceeds memory bounds!")
                running = False
                break
            memory[index] = registers[x] // 100
            memory[index + 1] = (registers[x] // 10) % 10
            memory[index + 2] = registers[x] % 10
        elif (opcode & 0xF0FF) == 0xF055:
            if index + x + 1 > len(memory):
                print("ERROR: Fx55 operation exceeds memory")
                running = False
                break
            for i in range(x + 1):
                memory[index + i] = registers[i]
        elif (opcode & 0xF0FF) == 0xF065:
            if index + x + 1 > len(memory):
                print("Error: Fx65 exceedds memory")
                running = False
                break
            for i in range(x + 1):
                registers[i] = memory[index + i]
        elif (opcode & 0xF0FF) == 0xE09E:
            if registers[x] > 0xF:
                print("Error! Invalid keyboard key: ", registers[x])
                running = False
                break
            if keys[registers[x]] == 1:
                pc += 2
        elif (opcode & 0xF0FF) == 0xE0A1:
            if registers[x] > 0xF:
                print("Error! Invalid keyboard key: ", registers[x])
                running = False
                break
            if keys[registers[x]] == 0:
                pc += 2
        elif (opcode & 0xF0FF) == 0xF00A:
            pressed_key = None
            for key in range(16):
                if keys[key] == 1:
                    pressed_key = key
                    break
            if pressed_key is not None:
                registers[x] = pressed_key
            else:
                pc -= 2
        elif (opcode & 0xF0FF) == 0xF029:
            if registers[x] > 0xF:
                print("Error! Invalid font character: ", registers[x])
                running = False
                break
            index = 0x50 + (registers[x] * 5)
        elif (opcode & 0xF000) == 0x0000:
            pass
        else:
            print("Error! Invalid opcode: ", hex(opcode))
            running = False
            break
        if (opcode & 0xF000) not in (0x1000, 0x2000, 0xB000) and opcode != 0x00EE:
            pc += 2

    screen.fill((0, 0, 0))

    for y in range(32):
        for x in range(64):
            if display[y][x] == 1:
                pygame.draw.rect(screen, (255, 255, 255), (x * 10, y * 10, 10, 10))

    pygame.display.flip()
    clock.tick(60)

pygame.quit()