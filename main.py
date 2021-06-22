from curses_tools import draw_frame, read_controls, get_frame_size
from physics import update_speed
from obstacles import Obstacle, show_obstacles
import time
import curses
import asyncio
import random
import os



COROUTINES = []
OBSTACLES = []
OBSTACLES_IN_LAST_COLLISIONS = []


async def sleep(tics=1):
    for _ in range(tics):
        await asyncio.sleep(0)


def get_new_coordinate(current_coordinate, max_coordinate, speed, frame_size):
    increment = current_coordinate + speed
    if speed < 0:
        if (increment <= 0) or (0 < increment <= 1):
            new_coordinate = 1
        else:
            new_coordinate = increment
    elif speed > 0:
        if (increment >= max_coordinate) or ((max_coordinate - frame_size - 1) <= increment < max_coordinate):
            new_coordinate = max_coordinate - frame_size - 1
        else:
            new_coordinate = increment
    else:
        new_coordinate = current_coordinate

    return new_coordinate


def get_star_coroutines(canvas, stars_number):
    star_coroutines = []
    max_row, max_column = canvas.getmaxyx()
    for _ in range(0, stars_number):
        row = random.randint(1, max_row - 2)
        column = random.randint(1, max_column - 2)
        star_symbol = random.choice('+*.:')
        star = blink(canvas, row, column, star_symbol)
        star_coroutines.append(star)

    return star_coroutines


def get_rocket_frames():
    with open('rocket/rocket_frame_1.txt', 'r') as file:
        rocket_frame_1 = file.read()

    with open('rocket/rocket_frame_2.txt', 'r') as file:
        rocket_frame_2 = file.read()

    return rocket_frame_1, rocket_frame_2


def get_garbage_frames(garbage_frames_dir):
    garbage_frames = []
    garbage_frames_name = os.listdir(garbage_frames_dir)
    for frame_name in garbage_frames_name:
        with open(os.path.join(garbage_frames_dir, frame_name)) as file:
            garbage_frame = file.read()

        garbage_frames.append(garbage_frame)

    return garbage_frames


async def blink(canvas, row, column, symbol='*'):
    initial_start = random.randint(0, 5)
    while True:
        while initial_start > 0:
            await asyncio.sleep(0)
            initial_start -= 1

        canvas.addstr(row, column, symbol, curses.A_DIM)
        await sleep(20)

        canvas.addstr(row, column, symbol)
        await sleep(3)

        canvas.addstr(row, column, symbol, curses.A_BOLD)
        await sleep(5)

        canvas.addstr(row, column, symbol)
        await sleep(3)


async def fire(canvas, start_row, start_column, rows_speed=-1, columns_speed=0):
    """Display animation of gun shot, direction and speed can be specified."""

    row, column = start_row, start_column

    canvas.addstr(round(row), round(column), '*')
    await asyncio.sleep(0)

    canvas.addstr(round(row), round(column), 'O')
    await asyncio.sleep(0)
    canvas.addstr(round(row), round(column), ' ')

    row += rows_speed
    column += columns_speed

    symbol = '-' if columns_speed else '|'

    rows, columns = canvas.getmaxyx()
    max_row, max_column = rows - 1, columns - 1

    curses.beep()

    while 0 < row < max_row and 0 < column < max_column:
        for obstacle in OBSTACLES:
            if obstacle.has_collision(row, column):
                OBSTACLES_IN_LAST_COLLISIONS.append(obstacle)
                return

        canvas.addstr(round(row), round(column), symbol)
        await asyncio.sleep(0)
        canvas.addstr(round(row), round(column), ' ')
        row += rows_speed
        column += columns_speed


async def animate_takt(canvas, start_row, start_column, space_pressed, frame):
    if space_pressed:
        fire_coroutine = fire(canvas, start_row, start_column+2)
        COROUTINES.append(fire_coroutine)
    draw_frame(canvas, start_row, start_column, frame)
    await asyncio.sleep(0)
    draw_frame(canvas, start_row, start_column, frame, True)


async def animate_spaceship(canvas, start_row, start_column, frame_1, frame_2):
    row, column = start_row, start_column
    row_size, column_size = get_frame_size(frame_1)
    max_row, max_column = canvas.getmaxyx()
    row_speed = column_speed = 0
    while True:
        rows_direction, columns_direction, space_pressed = read_controls(canvas)
        row_speed, column_speed = update_speed(row_speed, column_speed, rows_direction, columns_direction)
        start_row = get_new_coordinate(start_row, max_row, row_speed, row_size)
        start_column = get_new_coordinate(start_column, max_column, column_speed, column_size)
        await animate_takt(canvas, start_row, start_column, space_pressed, frame_1)

        rows_direction, columns_direction, space_pressed = read_controls(canvas)
        row_speed, column_speed = update_speed(row_speed, column_speed, rows_direction, columns_direction)
        start_row = get_new_coordinate(start_row, max_row, row_speed, row_size)
        start_column = get_new_coordinate(start_column, max_column, column_speed, column_size)
        await animate_takt(canvas, start_row, start_column, space_pressed, frame_2)


async def fly_garbage(canvas, column, garbage_frame, speed=0.5):
    """Animate garbage, flying from top to bottom. Сolumn position will stay same, as specified on start."""
    rows_number, columns_number = canvas.getmaxyx()

    column = max(column, 0)
    column = min(column, columns_number - 1)

    row = 0

    frame_row_size, frame_column_size = get_frame_size(garbage_frame)
    garbage_frame_obstacle = Obstacle(row, column, frame_row_size, frame_column_size)
    OBSTACLES.append(garbage_frame_obstacle)

    while row < rows_number:
        for obstacle in OBSTACLES_IN_LAST_COLLISIONS:
            if garbage_frame_obstacle is obstacle:
                OBSTACLES.remove(garbage_frame_obstacle)
                OBSTACLES_IN_LAST_COLLISIONS.remove(obstacle)
                return

        draw_frame(canvas, row, column, garbage_frame)
        await asyncio.sleep(0)
        draw_frame(canvas, row, column, garbage_frame, negative=True)
        row += speed
        garbage_frame_obstacle.row = row


async def fill_orbit_with_garbage(canvas):
    garbage_frames = get_garbage_frames('./garbage')
    max_column = canvas.getmaxyx()[1]
    frame_height = 0
    while True:
        if frame_height > 0:
            frame_height -= 1
            await asyncio.sleep(0)
        else:
            column = random.randint(0, max_column)
            frame = random.choice(garbage_frames)
            frame_height = get_frame_size(frame)[0]
            garbage_coroutine = fly_garbage(canvas, column, frame)
            COROUTINES.append(garbage_coroutine)
            await asyncio.sleep(0)



def draw(canvas):
    canvas.nodelay(True)
    curses.curs_set(False)
    canvas.border()

    max_row, max_column = canvas.getmaxyx()

    star_number = 200
    star_coroutines = get_star_coroutines(canvas, star_number)
    COROUTINES.extend(star_coroutines)

    rocket_frame_1, rocket_frame_2 = get_rocket_frames()
    start_row, start_column = max_row // 2, max_column // 2
    animate_spaceship_coroutine = animate_spaceship(
        canvas, start_row, start_column,
        rocket_frame_1, rocket_frame_2
        )
    COROUTINES.append(animate_spaceship_coroutine)

    COROUTINES.append(fill_orbit_with_garbage(canvas))

    COROUTINES.append(show_obstacles(canvas, OBSTACLES))

    while True:
        for coroutine in COROUTINES.copy():
            try:
                coroutine.send(None)
                canvas.refresh()
            except StopIteration:
                COROUTINES.remove(coroutine)

        time.sleep(0.1)


if __name__ == '__main__':
    curses.update_lines_cols()
    curses.wrapper(draw)
