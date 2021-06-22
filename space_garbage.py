from curses_tools import draw_frame, get_frame_size
from obstacles import Obstacle
import asyncio
import main


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
        draw_frame(canvas, row, column, garbage_frame)
        await asyncio.sleep(0)
        draw_frame(canvas, row, column, garbage_frame, negative=True)
        row += speed
        garbage_frame_obstacle.row = row
