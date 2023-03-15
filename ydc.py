import re
import sys
import subprocess
import os
from pytube import YouTube


def is_valid_link(link: str) -> bool:
    return re.search(r"^(?:https?:\/\/)?(?:www\.)?(?:youtube\.com\/(?:watch\?(?=.*v=\w+)(?:\S+)?v=|embed\/|v\/)|youtu\.be\/)([\w\-]+)(?:\S+)?$", link) is not None

# expects:
# -- Youtube link
# in args.
def download_subcommand(program, args):
    if len(args) == 0:
        print(f'Usage: {program} download <url>')
        print(f'ERROR: No url provided!')


def on_complete_callback(stream, file_path):
    print(f'Download was completed! File saved to: {file_path}')

def convert_subcommand(program, args):
    if len(args) == 0:
        print(f'Usage: {program} convert <url>')
        print(f'ERROR: No url provided!')
        return 1

    url, *args = args

    if not is_valid_link(url):
        print(f'ERROR: url provided is invalid!')
        return 1


    yt = YouTube(url, on_complete_callback=on_complete_callback) 
    
    default_filename = 'to_convert.mp4'
    new_filename = yt.title.replace(' ', '-').lower() + '.mp3'

    audio_streams = yt.streams.filter(only_audio=True)
    audio_streams[0].download(filename=default_filename)

    # Run ffmpeg subprocess to convert audio stream mp4 -> mp3
    print(f'Converting: {default_filename} to {new_filename}...')
    # syscall = f'.\\ffmpeg\\bin\\ffmpeg.exe -i to_convert.mp4 {new_filename}'

    proc = subprocess.run(['.\\ffmpeg\\bin\\ffmpeg.exe', '-i', 'to_convert.mp4', new_filename])
    print(f'{proc}')
    if proc.returncode == 0:
        os.remove('to_convert.mp4')
    # os.system(syscall)


SUBCOMMANDS = {
    "download": {
        "run": download_subcommand,
        "signature": "<url>",
        "description": "Downloads the youtube video"
    },
    "convert": {
        "run": convert_subcommand,
        "signature": "<url>",
        "description": "Converts youtube video to .mp3 and saves it as <out>"
    }
}

def usage(program):
    print(f'Usage: {program} <SUBCOMMAND>')
    for (name, subcmd) in SUBCOMMANDS.items():
        sig = subcmd['signature']
        desc = subcmd['description']
        print(f'    {name} {sig}    {desc}')

if __name__ == "__main__":
    program, *args = sys.argv
    if len(args) == 0:
        usage(program)
        print(f'ERROR: No subcommand provided')
        exit(1)

    subcmd, *args = args

    if subcmd not in SUBCOMMANDS:
        print(f'ERROR: Invalid subcommand: {subcmd}')

    SUBCOMMANDS[subcmd]["run"](program, args)
    exit(0)
