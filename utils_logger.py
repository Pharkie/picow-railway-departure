"""
Author: Adam Knowles
Version: 0.1
Name: utils_logger.py
Description: Logging utils.

GitHub Repository: https://github.com/Pharkie/AdamGalactic/
License: GNU General Public License (GPL)
"""
import os
import utime
import config

def log_message(message, level="INFO"):
    """
    Logs a message with a given level.

    This function logs a message if the level is equal to or higher than the configured log level.
    The message is prefixed with a timestamp and the level. The log is written to a file, and if
    the file exceeds a certain size, it is rotated.

    Parameters:
    message (str): The message to log.
    level (str): The level of the message. Must be one of "DEBUG", "INFO", or "ERROR".
                 Defaults to "INFO".

    Raises:
    ValueError: If the level is not one of "DEBUG", "INFO", or "ERROR".
    OSError: If there is an error opening, writing to, or rotating the log file.
    """
    levels = ["DEBUG", "INFO", "ERROR"]
    if levels.index(level) >= levels.index(config.LOG_LEVEL):
        max_log_size = 100 * 1024
        max_log_files = 2
        timestamp = utime.localtime(utime.time())
        formatted_timestamp = (
            f"{timestamp[0]:04d}-{timestamp[1]:02d}-{timestamp[2]:02d} "
            + f"{timestamp[3]:02d}:{timestamp[4]:02d}:{timestamp[5]:02d}"
        )
        log_message_str = f"{formatted_timestamp} [{level}]: {message}\n"

        print(log_message_str)

        log_filename = "rail_data_log.txt"
        try:
            if os.stat(log_filename)[6] > max_log_size:
                # If the log file is too big, rotate it.
                rotate_message = f"Rotating log file {log_filename}. " + \
                f"Max log size: {max_log_size} bytes, max rotated log files: {max_log_files}\n"

                with open(log_filename, "a", encoding="utf-8") as log_file:
                    log_file.write(rotate_message)

                try:
                    os.remove(f"{log_filename}.{max_log_files}")
                except OSError:
                    pass
                for i in range(max_log_files - 1, 0, -1):
                    try:
                        os.rename(f"{log_filename}.{i}", f"{log_filename}.{i+1}")
                    except OSError:
                        pass
                os.rename(log_filename, f"{log_filename}.1")
        except OSError:
            print(f"Error rotating log file: {e}")

        try:
            with open(log_filename, "a", encoding="utf-8") as log_file:
                log_file.write(log_message_str)
        except OSError as e:
            print(f"Error writing to log file: {e}")
            