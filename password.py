#!/usr/bin/env conda run -n mysql python

import os
import sys
import string
import random
import secrets
import argparse

import arrow
from dotenv import load_dotenv

PUNCTUATION = "!@-_%."
MY_PATH = os.path.dirname(os.path.realpath(__file__))
load_dotenv(os.path.join(MY_PATH, ".env"))

sys.path.append(os.getenv("MYSQL_INSTALL_PATH"))
from my import MySQL
from helpers import display, get_wordlists


def get_random_alphanumeric_string(length, special_characters=False):
    seed_characters = string.ascii_letters + string.digits
    if special_characters:
        seed_characters += PUNCTUATION
    result = []
    while len(result) < length:
        result.append(secrets.choice(seed_characters))
    return "".join(result)

def get_memorable_string(length, special_characters=False):
    if special_characters:
        punct = PUNCTUATION
    else:
        punct = "-."
    bundle = get_wordlists()
    words = list(set(bundle[0]).union(set(bundle[1])))
    results = []
    while len("".join(results)) < length:
        panel = []
        if secrets.choice(range(0, 2)) == 0:
            panel.append(secrets.choice(words))
        else:
            panel.append(secrets.choice(words).capitalize())
        panel.append(str(secrets.choice(list(range(0, 100)))))
        panel.append(secrets.choice(punct))
        random.shuffle(panel)
        results += panel
        if len("".join(results)) > length:
            results = []

    pw = "".join(results)
    
    l = list(pw)
    while l[0] in punct:
        l = l[1:]
    while l[-1] in punct:
        l = l[:-1]

    pw = "".join(l)
    while pw == pw.lower():        
        i = secrets.choice(range(0, len(l)))
        if l[i] in string.ascii_letters:
            l[i] = l[i].upper()
            pw = "".join(l)           

    return pw 


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Password generator")
    parser.add_argument("description", nargs="*", help="Password description")
    parser.add_argument(
        "--max_length", "-max", default=24, type=int, help="maximum length"
    )
    parser.add_argument(
        "--min_length", "-min", default=16, type=int, help="maximum length"
    )
    parser.add_argument(
        "--special_chars", "-s", action="store_true", help="special characters"
    )
    parser.add_argument(
        "--random_characters", "-r", action="store_true", help="Use random characters instead of a memorable password"
    )
    parser.add_argument("--nosave", "-n", action="store_true", help="Don't save")
    parser.add_argument("--length", "-l", type=int, help="fixed length setting")
    args = parser.parse_args()


def create(args):
    if args.length:
        length = args.length
    else:
        if args.random_characters:
            length = secrets.choice(range(args.min_length, args.max_length))
        else:
            length = secrets.choice(range(args.min_length * 2, args.max_length * 2))
            

    if args.random_characters:
        pw = get_random_alphanumeric_string(length, args.special_chars)
    else:
        pw = get_memorable_string(length, args.special_chars)

    data = {
        "stamp": arrow.get().to("US/Eastern").format(),
        "description": " ".join(args.description),
        "password": pw,
    }

    if not args.nosave:
        with MySQL() as conn:
            conn.insert("passwords", data)
    print(data["password"])


def search(args):
    qry = ["SELECT * FROM passwords"]
    query_terms = []
    stmt = []
    for term in args.description[1:]:
        stmt.append("description LIKE %s")
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


def delete(args):
    with MySQL() as conn:
        for id in args.description[1:]:
            print("Deleting #{}".format(id))
            query = "DELETE FROM passwords WHERE id = %s"
            conn.execute(query, (id,))


def fetch(args):
    search(args)


def main(args):
    if len(args.description) == 0 or args.description[0] in ["list", "lsit"]:
        fetch(args)
    elif args.description[0] in ["find", "search"]:
        search(args)
    elif args.description[0] in ["del", "delete", "rm", "remove"]:
        delete(args)
    elif args.description[0] == "create":
        args.description.pop(0)
        if len(args.description) > 0:
            create(args)
        else:
            print("Must specify password description")
    else:        
        print("Must specify action: list, find, delete, create")


if __name__ == "__main__":

    main(args)
