from __future__ import unicode_literals
import json
import os
import subprocess
from queue import Queue
from bottle import route, run, Bottle, request, static_file, redirect
from threading import Thread
import youtube_dl
from pathlib import Path
from collections import ChainMap
import requests
from requests.utils import requote_uri



app = Bottle()


app_defaults = {
    'YDL_FORMAT': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]',
    'YDL_EXTRACT_AUDIO_FORMAT':'mp3',
    'YDL_EXTRACT_AUDIO_QUALITY': '192',
    'YDL_RECODE_VIDEO_FORMAT': None,
    #'YDL_OUTPUT_TEMPLATE': './youtube-dl/%(title)s.%(ext)s',
    #'YDL_OUTPUT_TEMPLATE': './youtube-dl/%(id)s.%(ext)s',
    'YDL_OUTPUT_TEMPLATE': './youtube-dl/out.mp3',
    'YDL_ARCHIVE_FILE': None,
    'YDL_SERVER_HOST': '0.0.0.0',
    'YDL_SERVER_PORT': 8080,
    'YDL_SONOS_API': 'http://192.168.0.5:5005',
    'YDL_SONOS_SHARE': 'http://192.168.0.5:8666'
}

def callSonos(speaker,mp3File):
    ydl_vars = ChainMap(os.environ, app_defaults)
    node = ydl_vars['YDL_SONOS_API']
    url = ydl_vars['YDL_SONOS_SHARE'] + "/" + mp3File
    print("URL:" + url)
    url = requote_uri(url)
    print("URL(encode):" + url)

    #setavtransporturi/http%3A%2F%2F192.168.0.5%3A8455%2F$1

    #logger.debug("callSonos:"+speaker+", "+event)
    if speaker is None or mp3File is None:
        return
     
    url = node + "/" +speaker + "/setavtransporturi/" + url
    print("sending: "+url)
    #logger.debug ("sending: "+url)
    r = None
    r = requests.get(url)
    if r is not None:
        print ("Sonos API")
        print (r.status_code)
        print (r.text)
        #writeClientlog("Fehler in Sonos-API: Code "+r.status_code)
    else:
        print ("RESPONSE IS NONE!")
    if r is not None and 200 == r.status_code:
        print(r.text)
        result = r.text
        return result
    return None


@app.route('/')
def redirectRoot():
    return redirect('/youtube-dl', code=302)

@app.route('/youtube-dl')
def dl_queue_list():
    return static_file('index.html', root='./')


@app.route('/youtube-dl/static/:filename#.*#')
def server_static(filename):
    return static_file(filename, root='./static')


@app.route('/youtube-dl/q', method='GET')
def q_size():
    return {"success": True, "size": json.dumps(list(dl_q.queue))}


@app.route('/youtube-dl/q', method='POST')
def q_put():
    url = request.forms.get("url")
    options = {
        'format': request.forms.get("format"),
        'speaker': request.forms.get("speaker")
    }

    if not url:
        return {"success": False, "error": "/q called without a 'url' query param"}

    dl_q.put((url, options))
    print("Added url " + url + " to the download queue")
    return {"success": True, "url": url, "options": options}

@app.route("/youtube-dl/update", method="GET")
def update():
    command = ["pip", "install", "--upgrade", "youtube-dl"]
    proc = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    output, error = proc.communicate()
    return {
        "output": output.decode('ascii'),
        "error":  error.decode('ascii')
    }

def dl_worker():
    while not done:
        url, options = dl_q.get()
        download(url, options)
        dl_q.task_done()

        speaker = options.get('speaker')
        callSonos(speaker, "out.mp3")


def get_ydl_options(request_options):
    request_vars = {
        'YDL_EXTRACT_AUDIO_FORMAT': None,
        'YDL_RECODE_VIDEO_FORMAT': None,
    }

    requested_format = request_options.get('format', 'bestvideo')

    if requested_format in ['aac', 'flac', 'mp3', 'm4a', 'opus', 'vorbis', 'wav']:
        request_vars['YDL_EXTRACT_AUDIO_FORMAT'] = requested_format
    elif requested_format == 'bestaudio':
        request_vars['YDL_EXTRACT_AUDIO_FORMAT'] = 'best'
    elif requested_format in ['mp4', 'flv', 'webm', 'ogg', 'mkv', 'avi']:
        request_vars['YDL_RECODE_VIDEO_FORMAT'] = requested_format

    ydl_vars = ChainMap(request_vars, os.environ, app_defaults)

    postprocessors = []

    if(ydl_vars['YDL_EXTRACT_AUDIO_FORMAT']):
        postprocessors.append({
            'key': 'FFmpegExtractAudio',
            'preferredcodec': ydl_vars['YDL_EXTRACT_AUDIO_FORMAT'],
            'preferredquality': ydl_vars['YDL_EXTRACT_AUDIO_QUALITY'],
        })

    if(ydl_vars['YDL_RECODE_VIDEO_FORMAT']):
        postprocessors.append({
            'key': 'FFmpegVideoConvertor',
            'preferedformat': ydl_vars['YDL_RECODE_VIDEO_FORMAT'],
        })

        #https://salsa.debian.org/debian/youtube-dl/blob/532a08904ffbacc5e5ccf99edb660c5f37ddb213/youtube_dl/YoutubeDL.py

    return {
        'format': ydl_vars['YDL_FORMAT'],
        'postprocessors': postprocessors,
        'outtmpl': ydl_vars['YDL_OUTPUT_TEMPLATE'],
        'download_archive': ydl_vars['YDL_ARCHIVE_FILE'],
        'restrictfilenames': True
    }


def download(url, request_options):
    with youtube_dl.YoutubeDL(get_ydl_options(request_options)) as ydl:
        ydl.download_with_info_file([url], "test.txt")


dl_q = Queue()
done = False
dl_thread = Thread(target=dl_worker)
dl_thread.start()

print("Updating youtube-dl to the newest version")
updateResult = update()
print(updateResult["output"])
print(updateResult["error"])

print("Started download thread")

app_vars = ChainMap(os.environ, app_defaults)

app.run(host=app_vars['YDL_SERVER_HOST'], port=app_vars['YDL_SERVER_PORT'], debug=True)
done = True
dl_thread.join()
