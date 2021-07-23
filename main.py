from curses_tools import draw_frame, read_controls, get_frame_size
from physics import update_speed
from obstacles import Obstacle, show_obstacles
from explosion import explode
import time
import curses
import asyncio
import random
import os


STAR_NUMBER = 200
COROUTINES = []
OBSTACLES = []
OBSTACLES_IN_LAST_COLLISIONS = []
YEAR = 1957
PHRASES = {
    1957: "First Sputnik",
    1961: "Gagarin flew!",
    1969: "Armstrong got on the moon!",
    1971: "First orbital space station Salute-1",
    1981: "Flight of the Shuttle Columbia",
    1998: 'ISS start building',
    2011: 'Messenger launch to Mercury',
    2020: "Take the plasma gun! Shoot the garbage!",
}


def get_garbage_delay_tics(year):
    if year < 1961:
        return None
    elif year < 1969:
        return 20
    elif year < 1981:
        return 14
    elif year < 1995:
        return 10
    elif year < 2010:
        return 8
    elif year < 2020:
        return 6
    else:
        return 2


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


def get_frames(frames_dir):
    frames = []
    frame_names = os.listdir(frames_dir)
    for frame_name in frame_names:
        with open(os.path.join(frames_dir, frame_name)) as f:
            frame = f.read()

        frames.append(frame)

    return frames


async def sleep(tics=1):
    for _ in range(tics):
        await asyncio.sleep(0)


async def change_year():
    global YEAR
    while True:
        await sleep(15)
        YEAR += 1


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


async def show_gameover(canvas, max_row, max_column):
    game_over_frame = get_frames('./game_over_frame')[0]
    row_size, column_size = get_frame_size(game_over_frame)
    start_row, start_column = ((max_row - row_size) // 2), ((max_column - column_size) // 2)
    while True:
        draw_frame(canvas, start_row, start_column, game_over_frame)
        await sleep()


async def show_phrase(canvas):
    while True:
        phrase = f'{YEAR}. {PHRASES.get(YEAR, "")}'
        await animate_takt(canvas, 1, 1, phrase)


async def animate_takt(canvas, row, column, frame):
    draw_frame(canvas, row, column, frame)
    await sleep()
    draw_frame(canvas, row, column, frame, True)


async def animate_spaceship(canvas, max_row, max_column):
    frame_1, frame_2 = get_frames('./rocket_frames')
    start_row, start_column = max_row // 2, max_column // 2
    row_size, column_size = get_frame_size(frame_1)
    row_speed = column_speed = 0
    while True:
        for obstacle in OBSTACLES:
            if obstacle.has_collision(start_row, start_column):
                game_over_coroutine = show_gameover(canvas, max_row, max_column)
                COROUTINES.append(game_over_coroutine)
                return

        rows_direction, columns_direction, space_pressed = read_controls(canvas)
        if YEAR >= 2020 and space_pressed:
            fire_coroutine = fire(canvas, start_row, start_column+2)
            COROUTINES.append(fire_coroutine)
        row_speed, column_speed = update_speed(row_speed, column_speed, rows_direction, columns_direction)
        start_row = get_new_coordinate(start_row, max_row, row_speed, row_size)
        start_column = get_new_coordinate(start_column, max_column, column_speed, column_size)
        await animate_takt(canvas, start_row, start_column, frame_1)

        rows_direction, columns_direction, space_pressed = read_controls(canvas)
        if YEAR >= 2020 and space_pressed:
            fire_coroutine = fire(canvas, start_row, start_column+2)
            COROUTINES.append(fire_coroutine)
        row_speed, column_speed = update_speed(row_speed, column_speed, rows_direction, columns_direction)
        start_row = get_new_coordinate(start_row, max_row, row_speed, row_size)
        start_column = get_new_coordinate(start_column, max_column, column_speed, column_size)
        await animate_takt(canvas, start_row, start_column, frame_2)


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
                center_row = row + (frame_row_size // 2)
                center_column = column + (frame_column_size // 2)
                await explode(canvas, center_row, center_column)
                return

        await animate_takt(canvas, row, column, garbage_frame)
        row += speed
        garbage_frame_obstacle.row = row

    OBSTACLES.remove(garbage_frame_obstacle)


async def fill_orbit_with_garbage(canvas, max_column):
    garbage_frames = get_frames('./garbage_frames')
    while True:
        garbage_delay_tics = get_garbage_delay_tics(YEAR)
        if garbage_delay_tics:
            column = random.randint(0, max_column)
            frame = random.choice(garbage_frames)
            garbage_coroutine = fly_garbage(canvas, column, frame)
            COROUTINES.append(garbage_coroutine)
            await sleep(garbage_delay_tics)
        else:
            await sleep()



def draw(canvas):
    canvas.nodelay(True)
    curses.curs_set(False)
    canvas.border()
    max_row, max_column = canvas.getmaxyx()
    phrase_canvas = canvas.derwin(max_row-3, max_column-55)

    star_coroutines = get_star_coroutines(canvas, STAR_NUMBER)
    COROUTINES.extend(star_coroutines)

    animate_spaceship_coroutine = animate_spaceship(canvas, max_row, max_column)
    COROUTINES.append(animate_spaceship_coroutine)

    COROUTINES.append(fill_orbit_with_garbage(canvas, max_column))

    COROUTINES.append(change_year())

    COROUTINES.append(show_phrase(phrase_canvas))

    while True:
        for coroutine in COROUTINES.copy():
            try:
                coroutine.send(None)
                canvas.refresh()
                phrase_canvas.refresh()
            except StopIteration:
                COROUTINES.remove(coroutine)

        time.sleep(0.1)


if __name__ == '__main__':
    curses.update_lines_cols()
    curses.wrapper(draw)
