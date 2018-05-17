import os
import sys
import pygame
# import msvcrt
import msvcrt_input
import traceback
import fnmatch
import glob
import re
import random
import urllib.request
import youtube_dl.utils
import time

from threading import Thread
import downloader

from pygame.locals import *

pygame.mixer.pre_init(44100, -16, 2, 2048)
# pygame.mixer.pre_init(48000, -16, 2, 2048)

pygame.mixer.init()
pygame.init()

music = []
commands = {}

yt_downloader = downloader.Downloader()
msvcrt_input.prefix = '> '
clock = pygame.time.Clock()
pygame.mixer.music.set_volume(1)

def cmd(name, description, *aliases):
    def real_decorator(func):
        commands[name] = [func, description]
        for alias in aliases:
            if alias not in commands:
                commands[alias] = [func, description]
            else:
                pass
        return func
    return real_decorator

def play(file):
    global now_playing
    now_playing = file
    try:
        pygame.mixer.music.load(file)
        pygame.mixer.music.play()
        msvcrt_input.do_output("Now playing {}.".format(file))
        pygame.mixer.music.set_endevent(pygame.USEREVENT)
    except:
        msvcrt_input.do_output("Unable to open file {}".format(file))
        pygame.event.post(pygame.event.Event(pygame.USEREVENT))

def enqueue(songs):
    music.extend(songs)
    return '\n'.join("Successfully added {} to position {} in the queue.{}".format(
        song, len(music) - len(songs) + i + int(bool(now_playing)),
        ' Coming up next!' if len(music) - len(songs) + i == 0 and not now_playing else '')\
        for i, song in enumerate(songs))

def parse_command_string(text):
    with open('input.txt', 'a', encoding='utf-8') as f:
        f.write(text + '\n')
    command = text.split(' ')[0].lower()
    parameters = ' '.join(text.split(' ')[1:])
    parse_command(command, parameters)

def parse_command(command, parameters):
    if command in commands:
        try:
            output = commands[command][0](parameters)
            print(output)
        except Exception:
            traceback.print_exc()
    else:
        print("Invalid command.")

@cmd('ping', "ping takes no arguments\n\nReply pong.")
def cmd_ping(parameters):
    return "pong"

@cmd('eval', "eval <code>\n\nEvalulate arbitrary code.")
def cmd_eval(parameters):
    output = eval(parameters)
    return output

@cmd('exit', "exit takes no arguments\n\nQuits the program.", 'q', 'quit')
def cmd_exit(parameters):
    exit()

@cmd('play', "play <file>\n\nAdds a song to the queue.")
def cmd_play(parameters):
    response = cmd_search('-p ./downloaded/' + parameters)
    if response != "No files found.":
        return response
    return cmd_ytsearch(parameters)

@cmd('search', "search [<flags>] <pattern>\n\nSearches for song(s) to add to the queue. "
               "By default, it will search filename by glob and automatically append a file extension to the search query.\nFlags:\n"
               " -view    -v Returns the list of songs found without adding them to the queue.\n"
               " -case    -c Make matching case-sensitive.\n"
               " -exact   -e Matches the exact filename only.\n"
               " -regex   -r Treats <pattern> as a regexp.\n"
               " -path    -p Treats <pattern> as a path."
               " -shuffle -s Shuffles songs found before adding to queue")
def cmd_search(parameters):
    pygame.mixer.music.unpause()
    SEARCH_TYPE = ['exact', 'regex', 'path', 'default']
    def find(pattern, path, flags):
        found = []
        funcs = {'exact' : lambda name, pattern: name == pattern,
                 'regex' : lambda name, pattern: re.search(pattern, name),
                 'default' : fnmatch.fnmatchcase}
        for flag in ['exact', 'regex', 'default']:
            if flag in flags:
                func = funcs[flag]
                break
        else:
            func = None

        if func:
            for root, dirs, files in os.walk(path):
                for name in files:
                    if 'case' in flags:
                        lname = name
                    else:
                        lname = name.lower()
                        pattern = pattern.lower()
                    if func(lname, pattern):
                        found.append(os.path.join(root, name))
        elif 'path' in flags:
            found = glob.glob(os.path.join(path, pattern))
        return found

    flagmap = {'view' : ['view', 'v'],
               'case' : ['case', 'c'],
               'exact' : ['exact', 'e'],
               'regex' : ['regex', 'r'],
               'path' : ['path', 'p'],
               'shuffle' : ['shuffle', 's']}

    params = parameters.split(' ')
    flags = []
    for param in list(params):
        if param.startswith('-'):
            flags.append(param.strip('-'))
            params.remove(param)
        else:
            break
    
    parameters = ' '.join(params)

    for i, flag in enumerate(flags):
        for f, fs in flagmap.items():
            if flag in fs:
                flags[i] = f
                break
        else:
            flags[i] = None
    
    flags = list(set(filter(None, flags)))

    if len(set(flags) & set(SEARCH_TYPE)) == 0:
        flags.append('default')

    musicpath = os.path.join(os.path.expanduser("~"), "Music")
    youtubedlpath = os.path.join(os.path.expanduser("~"), "Documents\\!Temp\\youtube-dl")
    currentpath = os.path.abspath(".")
    pattern = parameters if '.' in parameters else parameters + '.[mwo][pag][3vg]'

    if 'path' in flags:
        songs = find(pattern, currentpath, flags)
    else:
        songs = find(pattern, currentpath, flags) + find(pattern, musicpath, flags) + find(pattern, youtubedlpath, flags)

    if len(songs) == 0:
        return "No files found."
    msg = "Found {} song{}:\n".format(len(songs), '' if len(songs) == 1 else 's')
    if 'shuffle' in flags:
        random.shuffle(songs)
    if 'view' in flags:
        return msg + '\n'.join(songs)
    else:
        return msg + enqueue(songs)

@cmd('pause', "pause takes no arguments\n\nPauses the player.")
def cmd_pause(parameters):
    if now_playing:
        pygame.mixer.music.pause()
        return "Paused player."
    else:
        return "No song is currently being played."

@cmd('unpause', "unpause takes no arguments\n\nUnpauses the player.", 'resume')
def cmd_unpause(parameters):
    if now_playing:
        pygame.mixer.music.unpause()
        return "Unpaused player."
    else:
        return "No song is currently being played."

@cmd('stop', "stop takes no arguments\n\nStops the player.")
def cmd_stop(parameters):
    if now_playing:
        music.clear()
        pygame.mixer.music.stop()
        return "Stopped player."
    else:
        return "No song is currently being played."

@cmd('clear', "clear takes no arguments\n\nClears the playlist.")
def cmd_clear(parameters):
    if len(music) > 0:
        music.clear()
        return "Cleared the playlist."
    else:
        return "The playlist is empty."

@cmd('queue', "queue takes no arguments\n\nDisplays the current queue.")
def cmd_queue(parameters):
    if len(music) == 0:
        return "The queue is empty."
    else:
        return '\n'.join("{:2}: {}".format(i + 1, music[i]) for i in range(len(music)))

@cmd('nowplaying', "nowplaying takes no arguments\n\nDisplays the song currently being played.", 'np')
def cmd_nowplaying(parameters):
    if now_playing:
        return now_playing
    else:
        return "No song is currently being played."

@cmd('skip', "skip takes no arguments\n\nSkips the current song.")
def cmd_skip(parameters):
    if now_playing:
        pygame.event.post(pygame.event.Event(pygame.USEREVENT))
        pygame.mixer.music.unpause()
        return "Skipped {}.".format(now_playing)
    else:
        return "No song is currently being played."

@cmd('shuffle', "shuffle takes no arguments\n\nShuffles the playlist.")
def cmd_shuffle(parameters):
    if len(music) == 0:
        return "The queue is empty."
    else:
        random.shuffle(music)
        return "Shuffled!"

@cmd('help', "help <command>\n\nReturns hopefully helpful information on <command>.")
def cmd_help(parameters):
    if parameters == '':
        parameters = 'help'
    if parameters in commands:
        return commands[parameters][1]
    else:
        return "Invalid command."

@cmd('list', "list takes no arguments\n\nReturns a list of commands.")
def cmd_list(parameters):
    return "Available commands: " + ', '.join(sorted(commands))

@cmd('volume', "volume <volume>\n\nSets volume to <volume> or returns the current volume.")
def cmd_volume(parameters):
    if parameters.isdigit() and int(parameters) in range(101):
        pygame.mixer.music.set_volume(int(parameters) / 100)
        return "Sucessfully set volume to {}%.".format(parameters)
    else:
        return "Volume is at {}%.".format(int(pygame.mixer.music.get_volume() * 100))

@cmd('ytsearch', "ytsearch <url | playlist url | search query>\n\nAdds song(s) from a youtube link/playlist or does a search.")
def cmd_ytsearch(parameters):
    if parameters:
        start_ytdl(parameters, result_queue)
        return "Started downloader for {}.".format(parameters)
    else:
        return commands['ytsearch'][1]

# lines = []
# lines.append(['', 0])
# line = 0
now_playing = ''
result_queue = []

def ytdl(query, result_queue):
    response = None
    try:
        result_queue.append(['extracting info'])
        query_type = None #"url"
        vid_urls = []
        # try:
        #     # query is a url
        #     urllib.request.urlopen(query)
        # except:
        #     query = "ytsearch:" + query
        #     query_type = 'search'

        while not query_type:
            response = yt_downloader.extract_info(url=query, download=False, process=False)
            if response.get('extractor', None) == 'youtube':
                query_type = 'url'
            elif response.get('extractor', None) == 'youtube:playlist':
                query_type = 'playlist'
            elif response.get('extractor', None) == 'youtube:search':
                query_type = 'search'
            else:
                query = response.get('url', None)

        if query_type == 'url' and response.get('_type', None) == 'playlist':
            query_type = 'playlist'
        if query_type == 'playlist' and response.get('_type', None) == 'url':
            query_type = 'url'

        if query_type == 'url':
            vid_urls.append(response['id'])
        elif query_type == 'search':
            entry = response['entries'][0]
            vid_urls.append(entry['id'])
        elif query_type == 'playlist':
            vid_urls.extend(filter(None, (x.get('id', None) for x in response['entries'])))
        
        bad_urls = []
        filenames = []

        result_queue.append(['downloading songs'])

        for url in vid_urls:
            try:
                info = yt_downloader.extract_info(url=url, download=False, process=True)
            except Exception as e:
                bad_urls.append(url)
                continue
            if not info:
                bad_urls.append(url)
                continue

            filename = '.'.join(youtube_dl.YoutubeDL(params=downloader.ytdl_opts).prepare_filename(info).split('.')[:-1]) + '.mp3'
            if not os.path.isfile(filename):
                try:
                    yt_downloader.extract_info(url=url, download=True, process=True)
                except Exception as e:
                    bad_urls.append(url)
                    continue
            result_queue.append(['downloaded song', filename])

            filenames.append(filename)

        result_queue.append(['finished', filenames, bad_urls])
    except Exception as e:
        result_queue.append(['error', sys.exc_info()])

def start_ytdl(query, result_queue):
    thread = Thread(target=ytdl, args=(query, result_queue))
    thread.start()

# def do_input():
#     if msvcrt.kbhit():
#         raw_ch = msvcrt.getch()
#         #print(raw_ch)
#         try:
#             ch = raw_ch.decode('utf-8')
#         except UnicodeDecodeError:
#             ch = raw_ch

#         if isinstance(ch, bytes):
#             if ch == b'\xe0':
#                 raw_ch = msvcrt.getch()
#                 try:
#                     next_ch = raw_ch.decode('utf-8')
#                 except UnicodeDecodeError:
#                     next_ch = raw_ch

#                 if next_ch == 'K': # left
#                     lines[-1][1] = max(0, lines[-1][1] - 1)
#                 elif next_ch == 'M': # right
#                     lines[-1][1] = min(len(lines[-1][0]), lines[-1][1] + 1)
#                 elif next_ch == 'H': # up
#                     line = max(0, line - 1)
#                     lines[-1][:] = lines[line][:]
#                 elif next_ch == 'P': # down
#                     line = min(len(lines) - 1, line + 1)
#                     if line == len(lines) - 1 and lines[-1][0] != '':
#                         lines[line] = ['', 0]
#                     else:
#                         lines[-1][:] = lines[line][:]
#                 elif next_ch == 'G': # home
#                     lines[-1][1] = 0
#                 elif next_ch == 'O': # end
#                     lines[-1][1] = len(lines[-1][0])
#                 elif next_ch == 'S': # delete
#                     lines[-1][0] = lines[-1][0][:lines[-1][1]] + lines[-1][0][lines[-1][1] + 1:]
#                 elif next_ch == 'I': # page up
#                     line = 0
#                     lines[-1][:] = lines[line][:]
#                 elif next_ch == 'Q': # page down
#                     line = len(lines) - 1
#                     lines[-1] = ['', 0]
#                 elif next_ch == 'R': # insert
#                     pass
#                 #elif next_ch == 
#                 else:
#                     print(next_ch)
#             elif ch == b'\x93': # shift+delete
#                 lines[-1][0] = lines[-1][0][:lines[-1][1]] + lines[-1][0][lines[-1][1] + 1:]
#             else:
#                 print(ch)
#         elif isinstance(ch, str):
#             if ch == '\r': # enter
#                 print()
#                 lines[-1][1] = len(lines[-1][0])
#                 command_string = lines[-1][0]

#                 line = len(lines)
#                 lines.append(['', 0])
#                 parse_command_string(command_string)
#             elif ch == '\b': # backspace
#                 lines[-1][0] = lines[-1][0][:lines[-1][1] - 1] + lines[-1][0][lines[-1][1]:]
#                 lines[-1][1] = max(0, lines[-1][1] - 1)
#             elif ch == '\x1b': # escape
#                 lines[-1] = ['', 0]
#             else:
#                 lines[-1][0] = lines[-1][0][:lines[-1][1]] + ch + lines[-1][0][lines[-1][1]:]
#                 lines[-1][1] += 1

# print("> ", end='')
while True:
    clock.tick(30)
    # msvcrt_input.do_output('' + ' ' * 100 + '\b' * 100 + "> " +
    #       lines[-1][0] + ' ' + '\b' * (len(lines[-1][0]) - lines[-1][1] + 1), end='')
    # sys.stdout.flush()
    # do_input()
    msvcrt_input.do_input()
    text = msvcrt_input.get_input()
    if text:
        parse_command_string(text)

    if result_queue:
        result = result_queue.pop()
        if result[0] == 'error':
            msvcrt_input.do_output('An error occurred:\n' + ''.join(traceback.format_exception(*result[1])))
        elif result[0] == 'extracting info':
            msvcrt_input.do_output('Getting song(s) information from youtube...')
        elif result[0] == 'downloading songs':
            msvcrt_input.do_output('Downloading song(s) from youtube...')
        elif result[0] == 'downloaded song':
            msvcrt_input.do_output("" + enqueue([result[1]]))
        elif result[0] == 'finished':
            msvcrt_input.do_output("Successfully downloaded {} song{}{}.".format(
                len(result[1]), '' if len(result[1]) == 1 else 's',
                '' if len(result[2]) == 0 else ", unable to download {} song{}".format(
                    len(result[2]), '' if len(result[2]) == 1 else 's')))

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            sys.exit()
        elif event.type == pygame.USEREVENT:
            if len(music) == 0:
                if now_playing:
                    now_playing = ''
                    pygame.mixer.music.stop()
                    msvcrt_input.do_output("End of queue.")
                continue
            song = music[0]
            music = music[1:]
            #msvcrt_input.do_output("pygame.USEREVENT play")
            play(song)


    if len(music) > 0 or now_playing:
        if not pygame.mixer.music.get_busy():
            #msvcrt_input.do_output("now_playing: {} busy: {}".format(now_playing, pygame.mixer.music.get_busy()))
            pygame.event.post(pygame.event.Event(pygame.USEREVENT))
    else:
        now_playing = ''

