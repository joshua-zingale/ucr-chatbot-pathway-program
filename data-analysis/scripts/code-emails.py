"""Anonymize email addresses in a large SQL dump while maintaining consistency. Uses standard IO.


Expected usage: python3 code-emails.py < sql-dump.sql > sql-dump-with-names-coded.sql
"""

import sys
import re
import argparse
import random

MAX_RAND_INT = 999999


def anonymize_sql():
    """Reads an sql dump from standard input and replaces all <name>@ucr.edu email addresses with random user ID's,
    outputing to standard output."""
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawTextHelpFormatter
    )
    _ = parser.parse_args()

    email_regex = re.compile(r"([\w\.-]+)@ucr\.edu")

    user_mapping = {}

    used_numbers: set[int] = set()

    for line in sys.stdin:

        def replace_email(match: re.Match[str]):
            username = match.group(1)

            if username not in user_mapping:
                while True:
                    new_num = random.randint(0, MAX_RAND_INT)
                    if new_num not in used_numbers:
                        used_numbers.add(new_num)
                        user_mapping[username] = f"user{new_num}"
                        break

            return f"{user_mapping[username]}@ucr.edu"

        new_line = email_regex.sub(replace_email, line)

        sys.stdout.write(new_line)


if __name__ == "__main__":
    try:
        anonymize_sql()
    except KeyboardInterrupt:
        sys.stderr.write("\nProcess interrupted by user.\n")
        sys.exit(1)
