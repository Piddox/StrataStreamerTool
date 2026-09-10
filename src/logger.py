import threading
from datetime import datetime


CONSOLE_LOCK = threading.Lock()


def log(message=None, timestamp=True):
    """
    Print a thread-safe console message.

    Parameters:
        message:
            Message to print. If None, prints a blank line.

        timestamp:
            Whether to add a timestamp.
    """

    with CONSOLE_LOCK:

        if message is None:
            print()
            return

        if timestamp:

            current_time = (
                datetime.now()
                .strftime("%H:%M:%S")
            )

            print(
                f"[{current_time}] {message}"
            )

        else:

            print(message)

def log_block(lines, timestamp=False):
    """
    Print multiple lines while holding the console lock.

    This prevents another thread from writing between lines.
    """

    with CONSOLE_LOCK:

        for line in lines:

            if line is None:
                print()
                continue

            if timestamp:

                current_time = (
                    datetime.now()
                    .strftime("%H:%M:%S")
                )

                print(
                    f"[{current_time}] {line}"
                )

            else:

                print(line)