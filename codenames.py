#!/usr/bin/env python

import os
import time
import re
import random
import pprint
import sys
import argparse
import hashlib
import secrets


def get_wordlists():
    my_path = os.path.dirname(os.path.realpath(__file__))
    adjectives = [row.strip() for row in open(os.path.join(my_path, "adjectives.txt"))]
    nouns = [row.strip() for row in open(os.path.join(my_path, "nouns.txt"))]
    return adjectives, nouns


def strip_hyphens(words):
    new_words = []
    for word in words:
        new_words += word.split("-")
    return new_words


def get_seed(seed):
    if not seed:
        seed = secrets.token_hex()
    m = hashlib.sha256()
    m.update(seed.encode("utf-8"))
    return int(m.hexdigest(), base=16)


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Codename creator")
    parser.add_argument(
        "--number", "-n", default=8, type=int, help="number of codenames"
    )
    parser.add_argument(
        "--max_length", "-m", default=11, type=int, help="maximum length"
    )
    parser.add_argument(
        "--upper_case", "-u", action="store_true", help="uppercase codenames"
    )
    parser.add_argument(
        "--lower_case", "-l", action="store_true", help="lowercase codenames"
    )
    parser.add_argument("--join", "-j", default="", help="Join character")
    parser.add_argument("--words", "-w", default=2, help="Number of words", type=int)
    parser.add_argument(
        "--variable_sizes",
        "-v",
        action="store_true",
        help="variable number of words (up to number specified in --words)",
    )
    parser.add_argument("--seed", "-s", help="random seed")
    args = parser.parse_args()

    random.seed(get_seed(args.seed))

    adjectives, nouns = get_wordlists()

    sample_size = min(len(adjectives), len(nouns))

    codenames = []
    failures = 0
    while len(codenames) < args.number and failures < 10000:
        word_set = []
        for i in range(0, args.words - 1):
            word_set.append(random.sample(adjectives, sample_size))

        word_set.append(random.sample(nouns, sample_size))
        seeds = zip(*word_set)
        for words in seeds:
            if args.variable_sizes:
                n = len(words) - 1
                r = random.sample(range(0, n), 1)[0]
                words = words[r:]

            words = strip_hyphens(words)

            if args.lower_case:
                codename = args.join.join([x.lower() for x in words])
            elif args.upper_case:
                codename = args.join.join([x.upper() for x in words])
            else:
                codename = args.join.join([x.capitalize() for x in words])

            if (
                len(words) <= args.words
                and len(codename) < args.max_length
                and codename not in codenames
            ):
                codenames.append(codename)
                failures = 0
            else:
                failures += 1
            if len(codenames) >= args.number:
                break

    if len(codenames) < args.number:
        print("Failed: Parameters too strict")

    for codename in codenames:
        print("{}".format(codename))
