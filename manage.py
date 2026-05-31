#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""

from pathlib import Path
import os
import sys


def main() -> None:
    base_dir = Path(__file__).resolve().parent
    sys.path.append(str(base_dir))
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()

