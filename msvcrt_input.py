import msvcrt, sys

inputs = []
lines = [['', 0]]
line = 0
prev_line = None
prev_pos = 0
prefix = ''

def do_input():
    global prev_line
    global line
    if prev_line is None:
        print(prefix, end='')
        prev_line = ''
        sys.stdout.flush()
    while msvcrt.kbhit(): # maybe replace with while
        raw_ch = msvcrt.getch()
        #print(raw_ch)
        try:
            ch = raw_ch.decode('utf-8')
        except UnicodeDecodeError:
            ch = raw_ch

        if isinstance(ch, bytes):
            if ch == b'\xe0':
                raw_ch = msvcrt.getch()
                try:
                    next_ch = raw_ch.decode('utf-8')
                except UnicodeDecodeError:
                    next_ch = raw_ch

                if next_ch == 'K': # left
                    lines[-1][1] = max(0, lines[-1][1] - 1)
                elif next_ch == 'M': # right
                    lines[-1][1] = min(len(lines[-1][0]), lines[-1][1] + 1)
                elif next_ch == 'H': # up
                    line = max(0, line - 1)
                    lines[-1][:] = lines[line][:]
                elif next_ch == 'P': # down
                    line = min(len(lines) - 1, line + 1)
                    if line == len(lines) - 1 and lines[-1][0] != '':
                        lines[line] = ['', 0]
                    else:
                        lines[-1][:] = lines[line][:]
                elif next_ch == 'G': # home
                    lines[-1][1] = 0
                elif next_ch == 'O': # end
                    lines[-1][1] = len(lines[-1][0])
                elif next_ch == 'S': # delete
                    lines[-1][0] = lines[-1][0][:lines[-1][1]] + lines[-1][0][lines[-1][1] + 1:]
                elif next_ch == 'I': # page up
                    line = 0
                    lines[-1][:] = lines[line][:]
                elif next_ch == 'Q': # page down
                    line = len(lines) - 1
                    lines[-1] = ['', 0]
                elif next_ch == 'R': # insert
                    pass
                #elif next_ch == 
                else:
                    print(next_ch)
            elif ch == b'\x93': # shift+delete
                lines[-1][0] = lines[-1][0][:lines[-1][1]] + lines[-1][0][lines[-1][1] + 1:]
            else:
                print(ch)
        elif isinstance(ch, str):
            if ch == '\r': # enter
                lines[-1][1] = len(lines[-1][0])
                do_output()
                print()
                inputs.append(lines[-1][0])
                line = len(lines)
                lines.append(['', 0])
                prev_line = None
                # TODO: find a way to determine when to print prefix
            elif ch == '\b': # backspace
                # print('\b \b', end='')
                lines[-1][0] = lines[-1][0][:max(0, lines[-1][1] - 1)] + lines[-1][0][lines[-1][1]:]
                lines[-1][1] = max(0, lines[-1][1] - 1)
            elif ch == '\x1b': # escape
                lines[-1] = ['', 0]
            else:
            #     print(ch, end='')
                lines[-1][0] = lines[-1][0][:lines[-1][1]] + ch + lines[-1][0][lines[-1][1]:]
                lines[-1][1] += 1
    do_output()

def do_output(text=None):
    global prev_line
    global prev_pos
    if prev_line != lines[-1][0] or text or prev_pos != lines[-1][1]:
        if prev_line is None:
            if text is None:
                return
            else:
                prev_line = ''
        else:
            chars_to_delete = len(prefix) + len(prev_line)
            print(' ' * (len(prev_line) - prev_pos) + '\b' * chars_to_delete + ' ' * chars_to_delete + '\b' * chars_to_delete, end='')
        if text:
            print(text)
        print(prefix + lines[-1][0] + '\b' * (len(lines[-1][0]) - lines[-1][1]), end='')
        prev_line = lines[-1][0]
        prev_pos = lines[-1][1]
        sys.stdout.flush()

def get_input():
    if inputs:
        return inputs.pop()
    return None

if __name__ == '__main__':
    while True:
        do_input()
        do_output()