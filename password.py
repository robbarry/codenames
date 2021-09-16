#!/usr/bin/env python

import os
import sys
import string
import secrets
import argparse


def get_random_alphanumeric_string(length, special_characters=False):
    seed_characters = string.ascii_letters + string.digits
    if special_characters:
        seed_characters += string.punctuation
    entropy = os.urandom(length)
    result = []
    for i in range(0, len(entropy)):
        c = entropy[i] % len(seed_characters)
        result.append(seed_characters[c])
    return "".join(result)


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Password generator")
    parser.add_argument(
        "--max_length", "-max", default=20, type=int, help="maximum length"
    )
    parser.add_argument(
        "--min_length", "-min", default=12, type=int, help="maximum length"
    )
    parser.add_argument(
        "--variable_length", "-v", action="store_true", help="variable length"
    )
    parser.add_argument(
        "--special_chars", "-s", action="store_true", help="special characters"
    )
    parser.add_argument("--length", "-l", type=int, help="fixed length setting")
    args = parser.parse_args()

if __name__ == "__main__":
    if args.length:
        length = args.length
    elif args.variable_length:
        length = secrets.choice(range(args.min_length, args.max_length))
    else:
        length = args.max_length

    print(get_random_alphanumeric_string(length, args.special_chars))
