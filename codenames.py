#!/Users/rob/Tresors/work/repos/codenames/.venv/bin/python

import os
import time
import re
import math
import random
import pprint
import sys
import argparse
import hashlib
import secrets

import arrow
import progressbar
from dotenv import load_dotenv

MY_PATH = os.path.dirname(os.path.realpath(__file__))
load_dotenv(os.path.join(MY_PATH, ".env"))
sys.path.append(os.getenv("MYSQL_INSTALL_PATH"))

from my import MySQL
from helpers import display, get_wordlists


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


def ingest(args):
    for filename in args.cmd[1:]:
        print(filename)
        with open(filename, "r") as f:
            for line in f:
                parts = line.strip().split(" ")
                codename = parts[0].strip()
                description = " ".join(parts[1:]).strip()
                print("{}: {}".format(codename, description))
                insert(codename, description)


def edit(args):
    id = lookup(args)
    print("New codename? ", end="")
    codename = input().strip()
    print("New description? ", end="")
    description = input().strip()
    stmt = []
    updates = []
    if len(codename) > 0:
        stmt.append("codename = %s")
        updates.append(codename)
    if len(description) > 0:
        stmt.append("description = %s")
        updates.append(description)
    if len(stmt) > 0:
        criteria = ", ".join(stmt)
        updates.append(id)
        qry = "UPDATE codenames SET {} WHERE id = %s".format(criteria)
        with MySQL() as conn:
            conn.execute(qry, (*updates,))
        lookup(args)


def main(args):
    if len(args.cmd) == 0 or args.cmd[0] in ["list", "lsit"]:
        fetch(args)
    elif args.cmd[0] in ["find", "search"]:
        search(args)
    elif args.cmd[0] == "create":
        create(args)
    elif args.cmd[0] in ["lookup", "lkp"]:
        lookup(args)
    elif args.cmd[0] in ["del", "delete", "rm", "remove"]:
        delete(args)
    elif args.cmd[0] in ["injest", "ingest", "import"]:
        ingest(args)
    elif args.cmd[0] in ["edit", "change"]:
        edit(args)


def delete(args):
    with MySQL() as conn:
        for id in args.cmd[1:]:
            print("Deleting #{}".format(id))
            query = "DELETE FROM codenames WHERE id = %s"
            conn.execute(query, (id,))


def search(args):
    qry = ["SELECT * FROM codenames"]
    query_terms = []
    stmt = []
    for term in args.cmd[1:]:
        stmt.append("codename LIKE %s")
        stmt.append("description LIKE %s")
        query_terms.append("%{}%".format(term))
        query_terms.append("%{}%".format(term))
    if len(stmt) > 0:
        qry.append("WHERE")
        qry.append(" OR ".join(stmt))
    query = " ".join(qry)
    rows = []
    with MySQL() as conn:
        for row in conn.select(query, query_terms):
            rows.append(row)

    display(rows)


def lookup(args):
    qry = ["SELECT * FROM codenames"]
    query_terms = []
    stmt = []
    if args.cmd[0] == "edit":
        if args.cmd[1].isnumeric():
            stmt.append("id = {}".format(args.cmd[1]))
        else:
            stmt.append("codename = '{}'".format(args.cmd[1]))
    else:
        for term in args.cmd[1:]:
            stmt.append("codename LIKE %s")
            query_terms.append("%{}%".format(term))
    if len(stmt) > 0:
        qry.append("WHERE")
        qry.append(" OR ".join(stmt))
    query = " ".join(qry)
    rows = []
    with MySQL() as conn:
        for row in conn.select(query, query_terms):
            rows.append(row)

    display(rows)
    if args.cmd[0] == "edit":
        return rows[0]["id"]


def get_used_codenames():
    query = "SELECT codename FROM codenames"
    codenames = []
    with MySQL() as conn:
        for row in conn.select(query):
            codenames.append(row["codename"].lower())
    return codenames


def fetch(args):
    search(args)


def create(args):
    random.seed(get_seed(args.seed))

    adjectives, nouns = get_wordlists(args)

    used_codenames = get_used_codenames()

    sample_size = min(len(adjectives), len(nouns))

    codenames = []
    failures = 0
    if args.progressbar:
        bar = progressbar.ProgressBar(max_value=args.number)
    else:
        bar = None
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

            cleared = True
            for c in used_codenames:
                if codename.lower().startswith(c) or codename.lower().endswith(c):
                    cleared = False

            if (
                len(words) <= args.words
                and len(codename) <= args.max_length
                and codename not in codenames
                and cleared
            ):
                codenames.append(codename)
                failures = 0
            else:
                failures += 1
            if len(codenames) >= args.number:
                break
        if bar:
            bar.update(len(codenames))
    if bar:
        bar.finish()

    if len(codenames) < args.number:
        print("Failed: Parameters too strict")

    i = 1
    end = len(codenames)
    print("")
    end_len = math.floor(math.log(end + 1) / math.log(10)) + 1
    if not args.exclude_prior:
        for codename in codenames:
            print("{} {}".format(i, codename))
            i += 1
    else:
        print("{} {}".format(end, codenames[-1]))

    print("")
    print("Selection? ", end="")
    selection = input().strip()
    if selection == "-1":
        return main(args)
    if len(selection) == 0:
        return False
    try:
        n = int(selection) - 1
        codename = codenames[n]
    except:
        codename = selection
    print("Selection: {}".format(codename))

    if len(args.cmd[1:]) == 0:
        print("Description? ", end="")
        desc = input().strip()
    else:
        desc = " ".join(args.cmd[1:])
        print("Description: {}".format(desc))
    insert(codename, desc)


def insert(codename, description):
    if len(codename) == 0:
        return False
    if len(description) == 0:
        return False
    data = {
        "stamp": arrow.get().to("US/Eastern").format(),
        "codename": codename,
        "description": description,
    }
    with MySQL() as conn:
        conn.insert("codenames", data)


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Codename creator")
    parser.add_argument("cmd", nargs="*", help="Action to take")
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
    parser.add_argument(
        "--exclude_prior", "-x", action="store_true", help="only display last codeword"
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
    parser.add_argument(
        "--progressbar", "-p", action="store_true", help="show progressbar"
    )
    parser.add_argument(
        "--solar_system",
        "-r",
        action="store_true",
        help="use solar system nouns",
    )
    args = parser.parse_args()
    main(args)
