import os


def display(rows):
    max_lens = {}
    for row in rows:
        for k, v in row.items():
            if len(str(v)) > max_lens.get(k, 0):
                max_lens[k] = len(str(v))

    for row in rows:
        output = []
        for k, v in row.items():
            output.append(str(v).ljust(max_lens[k] + 2))
        print(" | ".join(output))


def get_wordlists(args=None):
    my_path = os.path.dirname(os.path.realpath(__file__))
    adjectives = [row.strip() for row in open(os.path.join(my_path, "adjectives.txt"))]
    nouns = [row.strip() for row in open(os.path.join(my_path, "nouns.txt"))]
    if args is not None:
        if args.solar_system:
            nouns = [row.strip() for row in open(os.path.join(my_path, "extra.txt"))]

    return adjectives, nouns
