import re
import sys
import subprocess
import os
import math
from typing import List, Optional
from pytube import Stream, YouTube, Playlist
from datetime import datetime
from multiprocessing import Pool
from random import randint

DownloadOptions = ['single', 'multiple', 'playlist']

class Subcommand:
    name: str
    signature: str
    description: str

    def __init__(self, name, signature, description):
        self.name = name
        self.signature = signature
        self.description = description

    def run(self, program: str, args: List[str]) -> int:
        assert False, "Not implemented yet"
        return 0

def is_valid_link(link: str) -> bool:
    return re.search(r"^(?:https?:\/\/)?(?:www\.)?(?:youtube\.com\/(?:watch\?(?=.*v=\w+)(?:\S+)?v=|playlist\?(?=.*list=\w+)(?:\S+)?list=|embed\/|v\/)|youtu\.be\/)([\w\-]+)(?:\S+)?$", link) is not None

def is_valid_option_type(option: str) -> bool:
    return option in DownloadOptions

def on_complete_callback(stream, file_path):
    print(f'Download was completed! File saved to: {file_path}')

def on_progress_callback(stream: Stream, chunk, bytes_remaining):
    print(f'{stream.title}:{stream.type} Progress: {math.floor((1 - (bytes_remaining / stream.filesize)) * 100)}%') 

class DownloadSubcommand(Subcommand):
    def __init__(self):
        super().__init__('download', 'single|multiple|playlist <url>', 'Downloads a single video, multiple videos or a playlist')

    def download_single(self, url):
        if not is_valid_link(url):
            print(f'ERROR: Invalid link: {url}')
            return 1

        yt = YouTube(url, on_progress_callback=on_progress_callback, on_complete_callback=on_complete_callback)
        audio_stream = yt.streams.get_audio_only()
        # video_stream = yt.streams.filter(only_video=True, res='1080p')[0]
        video_stream = yt.streams.get_highest_resolution()

        temp_file_name = 'out_' + str(datetime.now().timestamp() * 1000) + '_' + str(os.getpid()) + str(randint(1, 100000))
        output_file_name = yt.title.replace(' ', '').replace(':', '-').replace('|', '-').lower()

        print(f'Downloading Audio for {yt.title}...')
        audio_stream.download(filename=temp_file_name + '.mp3')
        print(f'Downloading Video for {yt.title}...')
        video_stream.download(filename=temp_file_name + '.mp4')

        print(f'Merging Audio and Video for {yt.title}...')
        proc = subprocess.run(['.\\ffmpeg\\bin\\ffmpeg.exe', '-i', temp_file_name + '.mp4', '-i', temp_file_name + '.mp3', '-c', 'copy', output_file_name + '.mp4'])

        if proc.returncode == 0:
            os.remove(temp_file_name + '.mp3')
            os.remove(temp_file_name + '.mp4')

        # rename the file to the title of the video
        print('Cleaning file name...')
        cleaned_filename = re.sub(r'[<>:"/\\|?*]', '-', yt.title)
        os.rename(output_file_name + '.mp4', cleaned_filename + '.mp4')

    def download_multiple(self, urls):
        # args should contain the remainder of the parameters that were passed in,
        # in this case, they should all be links to youtube videos.

        if len(urls) == 0:
            print(f'Usage: {self.name} {self.signature}')
            print(f'ERROR: Provide at least 1 valid youtube url!')
            return 1

        with Pool(len(urls)) as p:
            p.map(self.download_single, urls)

        # for url in urls:
        #   self.download_single(url)
        return 0

    def download_playlist(self, url):
        if len(url) == 0:
            print(f'Usage: {self.name} {self.signature}')
            print('ERROR: Missing playlist url!')

        if not is_valid_link(url):
            print(f'Usage: {self.name} {self.signature}')
            print('ERROR: Invalid url!')

        p = Playlist(url)

        print(f'Downloading: {p.title}')
        video_urls = p.video_urls
        self.download_multiple(video_urls)

    def run(self, program: str, args: List[str]) -> int:
        if len(args) == 0:
            print(f'Usage: {program} {self.name} {self.signature}')
            print(f'ERROR: !')
            return 1;

        option, *args = args

        if not is_valid_option_type(option):
            print(f'Usage: {program} {self.name} {self.signature}')
            print(f'ERROR: Invalid option: "{option}"')
            return 1

        if option == 'single':
            url, *args = args
            return self.download_single(url)
        elif option == 'multiple':
            return self.download_multiple(args)
        elif option == 'playlist':
            url, *args = args
            return self.download_playlist(url)
        return 0;

class ConvertSubcommand(Subcommand):
    def __init__(self):
        super().__init__('convert', '<url>', 'Converts youtube video to .mp3 and saves it as <out>')

    def run(self, program: str, args: List[str]) -> int:
        if len(args) == 0:
            print(f'Usage: {program} {self.name} {self.signature}')
            print(f'ERROR: No url provided!')
            return 1

        url, *args = args

        print(f'URL: {url}, ARGS: {args}')

        if not is_valid_link(url):
            print(f'ERROR: url provided is invalid!')
            return 1


        yt = YouTube(url, on_complete_callback=on_complete_callback) 

        print(f'Youtube Object: {yt}')

        default_filename = 'to_convert.mp3'
        new_filename = yt.title.replace(' ', '').replace('|', '-').lower() + '.mp3'

        audio_streams = yt.streams.filter(only_audio=True)
        audio_streams[0].download(filename=default_filename)

        # Run ffmpeg subprocess to convert audio stream mp4 -> mp3
        print(f'Converting: {default_filename} to {new_filename}...')
        # syscall = f'.\\ffmpeg\\bin\\ffmpeg.exe -i to_convert.mp4 {new_filename}'

        proc = subprocess.run(['.\\ffmpeg\\bin\\ffmpeg.exe', '-i', default_filename, '-ab', '320k', new_filename])
        print(f'{proc}')
        if proc.returncode == 0:
            os.remove('to_convert.mp4')
        return 0;

SUBCOMMANDS: List[Subcommand] = [
   DownloadSubcommand(),
   ConvertSubcommand(),
]

def usage(program):
    print(f'Usage: {program} <SUBCOMMAND>')
    for subcmd in SUBCOMMANDS:
        name = subcmd.name
        sig = subcmd.signature
        desc = subcmd.description
        print(f'    {name} {sig}    {desc}')

def find_subcommand(subcmd_name: str) -> Optional[Subcommand]:
    for subcmd in SUBCOMMANDS:
        if subcmd.name == subcmd_name:
            return subcmd

    return None

def main() -> int:
    assert len(sys.argv) > 0
    program, *args = sys.argv

    if len(args) == 0:
        usage(program)
        print(f"ERROR: No subcommand provided!")
        return 1

    subcmd_name, *args = args
    subcmd = find_subcommand(subcmd_name)
    if subcmd is not None:
        return subcmd.run(program, args)

    usage(program)
    print(f"ERROR: Unknown subcommand {subcmd}!")
    return 1

if __name__ == "__main__":
    exit(main())
