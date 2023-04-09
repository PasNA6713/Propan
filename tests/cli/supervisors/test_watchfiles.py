import os
import signal
from pathlib import Path
from unittest.mock import patch, Mock
import time

import pytest

from propan.cli.supervisors.watchfiles import WatchReloader


DIR = Path(__file__).resolve().parent


def exit(parent_id):  # pragma: no-cover
    os.kill(parent_id, signal.SIGINT)


def test_base():
    processor = WatchReloader(target=exit, args=(), reload_dirs=[DIR])

    processor._args = (processor.pid,)
    processor.run()

    assert processor._process.exitcode == signal.SIGTERM.value * -1


def touch_file(file: Path):  # pragma: no-cover
    while True:
        time.sleep(0.1)
        with file.open("a") as f:
            f.write("hello")


@pytest.mark.slow
def test_restart(mock: Mock):
    file = DIR / "file.py"

    processor = WatchReloader(
        target=touch_file,
        args=(file,),
        reload_dirs=[DIR]
    )

    mock.side_effect = lambda: os.kill(processor.pid, signal.SIGINT)

    with patch.object(processor, "restart", mock):
        processor.run()

    mock.assert_called_once()
    file.unlink()
