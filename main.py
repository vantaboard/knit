import re
import signal
import sys
import os
from blessed import Terminal

term = Terminal()

def parse_row(stitch_count, line):
    row = []

    stitches = [stitch.strip() for stitch in line.split(" ")]

    start = []
    repeating = False
    stitch_decrease = 0

    for stitch in stitches:
        if stitch[0] == "*":
            stitch = stitch[1:]
            start = row
            row = []
            repeating = True

        k = re.search(r"k(\d+)?", stitch)
        p = re.search(r"p(\d+)?", stitch)
        k2tog = re.search(r"k2tog(\d+)?", stitch)

        if k2tog:
            row += ["k2tog"] * int(k2tog.group(1) or 1)
            stitch_decrease += int(k2tog.group(1) or 1)
        elif p:
            row += ["p"] * int(p.group(1) or 1)
        elif k:
            row += ["k"] * int(k.group(1) or 1)
        else:
            row.append(stitch)

    if repeating:
        temp = row
        row = start
        new_row = []
        for i in range(stitch_count - len(start)):
            new_row.append(temp[i % len(temp)])

        row += new_row

    return row, stitch_count - stitch_decrease

def parse_pattern(filename):
    with open(filename, "r") as f:
        lines = f.readlines()

    stitch_count = int(lines[0])
    rows = []
    for line in lines[1:]:
        row, stitch_count = parse_row(stitch_count, line)
        rows.append(row)

    return rows

def parse_progress(filename):
    with open(filename, "r") as f:
        lines = f.readlines()

    row = int(lines[0].split(": ")[1])
    stitch = int(lines[1].split(": ")[1])

    return row, stitch


def save_progress(filename, row, stitch):
    print(term.home + term.clear)

    with open(filename, "w") as f:
        f.write("row: {}\nstitch: {}".format(row, stitch))

    print(term.center(term.bold(term.fuchsia("Progress saved!"))))

    sys.exit()

def print_progress(rows, row, stitch, key = ''):
    print(term.home + term.clear)

    if (term.height < 10 or term.width < 80):
        print(term.center(term.bold(term.fuchsia("Please resize your terminal to be at least 30x10"))))
        return

    with term.location(0, 2):
        row_str = term.deepskyblue("  Row{} {} / {}".format(" " * (len(str(len(rows))) - len(str(row + 1))), row + 1, len(rows)))
        stitch_str = term.deepskyblue("Stitch{} {} / {}".format(" " * (len(str(len(rows[row]))) - len(str(stitch + 1))), stitch + 1, len(rows[row])))

        print(term.center(row_str + " " * (term.width - 40) +  stitch_str))

    if row == len(rows) - 1:
        print(' | ' + term.deepskyblue('Cast Off'), end="")

    print('\n')

    prespace = 0
    for i in range(stitch):
        prespace += len(rows[row][i])

    postspace = 0
    for i in range(stitch + 1, len(rows[row])):
        postspace += len(rows[row][i])

    previous_row = rows[row - 1] if row > 0 else []
    next_row = rows[row + 1] if row < len(rows) - 1 else []

    with term.location(0, term.height // 2 - 2):
        print(term.center(term.gray32(" ".join(previous_row))))
        print(term.center(" " * (stitch + prespace) + term.bold(term.fuchsia("↓")) + " " * (len(rows[row]) - stitch - 1 + postspace)))
        prefix = " ".join(rows[row][:stitch])
        print(term.center((prefix + " " if len(prefix) else "") + " ".join(rows[row][stitch:])))
        print()
        print(term.center(term.gray32(" ".join(next_row))))

    with term.location(0, term.height - 1):
        print(term.center('b ' + term.bold('back') + ', f ' + term.bold('forward') + ', ← ' + term.bold('back one stitch') + ', → ' + term.bold('forward one stitch') + ', q ' + term.bold('quit')))

def main():
    if len(sys.argv) < 3:
        print("Usage: python main.py <pattern_file> <progress_file>")
        return

    pattern_file = sys.argv[1]
    progress_file = sys.argv[2]

    if not os.path.isfile(pattern_file):
        print("Error: {} is not a file".format(pattern_file))
        return

    if not os.path.isfile(progress_file):
        with open(progress_file, "w") as f:
            f.write("row: 0\nstitch: 0")
        return

    rows = parse_pattern(pattern_file)
    row, stitch = parse_progress(progress_file)

    print_progress(rows, row, stitch)
    signal.signal(signal.SIGINT, lambda sig, data: save_progress(progress_file, row, stitch))

    signal.signal(signal.SIGWINCH, lambda sig, data: print_progress(rows, row, stitch))

    forward = True
    while True:
        with term.cbreak(), term.hidden_cursor():
            key = term.inkey()

            if key == "b":
                forward = False

            if key == "f":
                forward = True

            if key == "h" or repr(key) == "KEY_LEFT":
                forward = False
                key = " "

            if key == "l" or repr(key) == "KEY_RIGHT":
                forward = True
                key = " "

            if key == " ":
                stitch += 1 if forward else -1
                if (stitch >= len(rows[row]) and forward) or (stitch < 0 and not forward):
                    stitch = 0 if forward else len(rows[row]) - 1
                    row += 1 if forward else -1
                    if row >= len(rows):
                        print("You're done!")
                        save_progress(progress_file, 0, 0)
                        return
                    if (row < 0):
                        row = 0

            elif key == "q":
                save_progress(progress_file, row, stitch)

            print_progress(rows, row, stitch, key)

if __name__ == "__main__":
    main()
