import logging
import colorlog


def setup_logging(log_filename: str, console_level=logging.DEBUG, file_level=logging.INFO):
    file_handler = logging.FileHandler(log_filename, mode='w')
    file_handler.setLevel(file_level)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(console_level)
    color_formatter = colorlog.ColoredFormatter(
        '%(log_color)s%(levelname)s - %(name)s - %(message)s'
    )
    console_handler.setFormatter(color_formatter)

    logging.basicConfig(
        level=logging.DEBUG,
        format='%(levelname)s - %(name)s - %(message)s',  # Log format
        handlers=[
            file_handler,
            console_handler
        ]
    )
