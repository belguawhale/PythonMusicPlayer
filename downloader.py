import youtube_dl
import msvcrt_input

msvcrt_input.prefix = "> "

class MyLogger(object):
    def debug(self, msg):
        pass

    def warning(self, msg):
        msvcrt_input.do_output(msg)

    def error(self, msg):
        msvcrt_input.do_output(msg)

ytdl_opts = {
    # 'format': 'bestaudio/best', # old, ytdl uses format_id
    'format_id' : 'bestaudio/best', # 'bestaudio[asr=44100]/best[asr=44100]/mp3[asr=44100]', \
                                    # goddamnit ffmpeg defaulting to 48000 Hz sample rate and screwing up pygame
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
        'preferredquality': '192'
    }],
    'preferffmpeg': True,
    'postprocessor_args': ['-ar', '44100'], # finally fixed the sample rate problems
    'extractaudio' : True,
    'audioformat' : 'mp3',
    #'logger': MyLogger(),
    'noplaylist': True,
    'nocheckcertificate': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0',
    # 'progress_hooks': [my_hook],
    'outtmpl' : './downloaded/%(title)s-%(id)s.%(ext)s',
    'restrictfilenames' : True,
    'quiet' : True,
    #'no_warnings': True,
    #'ignoreerrors': True
}
# ytdl_opts = {
#     'format': 'bestaudio/best',
#     'extractaudio': True,
#     'audioformat': 'mp3',
#     'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
#     'restrictfilenames': True,
#     'noplaylist': True,
#     'nocheckcertificate': True,
#     'ignoreerrors': False,
#     'logtostderr': False,
#     'quiet': True,
#     'no_warnings': True,
#     'default_search': 'auto',
#     'source_address': '0.0.0.0'
# }

class Downloader():
    def __init__(self):
        self.ytdl = youtube_dl.YoutubeDL(ytdl_opts)
    
    def extract_info(self, *args, **kwargs):
        return self.ytdl.extract_info(*args, **kwargs)
    