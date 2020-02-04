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
import urllib.parse
#import requests
#from requests.utils import requote_uri

_speaker = None

app = Bottle()

app_defaults = {
    'YDL_FORMAT': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]',
    'YDL_EXTRACT_AUDIO_FORMAT':'mp3',
    'YDL_EXTRACT_AUDIO_QUALITY': '192',
    'YDL_RECODE_VIDEO_FORMAT': None,
    'YDL_OUTPUT_TEMPLATE': './youtube-dl/%(title)s.%(ext)s',
    'YDL_ARCHIVE_FILE': None,
    'YDL_SERVER_HOST': '0.0.0.0',
    'YDL_SERVER_PORT': 8080,
    'YDL_SONOS_API': 'http://192.168.0.5:5005',
}

def callSonos(speaker,trackurl):
    ydl_vars = ChainMap(os.environ, app_defaults)
    node = ydl_vars['YDL_SONOS_API']
    
    url = "x-rincon-mp3radio://"
    url = url + trackurl

    print("URL:" + url)
    #url = requote_uri(url)
    #url = urllib.parse.quote_plus(url)
    print("URL(encode):" + url)

    #setavtransporturi/http%3A%2F%2F192.168.0.5%3A8455%2F$1

    if speaker is None or mp3File is None:
        return
     
    url = node + "/" +speaker + "/setavtransporturi/" + url
    r = None
    #r = requests.get(url)
    if r is not None:
        print ("Sonos API")
        print (r.status_code)
        print (r.text)
    else:
        print ("RESPONSE IS NONE!")
    if r is not None and 200 == r.status_code:
        result = r.text
        print (result)
        requests.get(node + "/" +speaker + "/play")
        return result
    return None


@app.route('/share/:filename#.*#')
def getmp3(filename):
    return static_file(filename, root='./share')

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
    print ("get")
    return {"success": True, "size": json.dumps(list(dl_q.queue))}

@app.route('/youtube-dl/q', method='POST')
def q_put():
    print ("put")
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
        global _speaker 
        _speaker = options.get('speaker')
        download(url, options)
        dl_q.task_done()

def get_ydl_options(request_options):
    request_vars = {
        'YDL_EXTRACT_AUDIO_FORMAT': None,
        'YDL_RECODE_VIDEO_FORMAT': None,
    }
    requested_format = request_options.get('format', 'bestvideo')
    request_vars['YDL_EXTRACT_AUDIO_FORMAT'] = 'best'
    ydl_vars = ChainMap(request_vars, os.environ, app_defaults)


    #https://salsa.debian.org/debian/youtube-dl/blob/532a08904ffbacc5e5ccf99edb660c5f37ddb213/youtube_dl/YoutubeDL.py

    return {
        'format': ydl_vars['YDL_FORMAT'],
        'outtmpl': ydl_vars['YDL_OUTPUT_TEMPLATE'],
        'download_archive': ydl_vars['YDL_ARCHIVE_FILE'],
        'restrictfilenames': 'true', #gets rid of spaces in output name
        'simulate': 'true',
        'forceurl': 'true',
        'progress_hooks': [my_hook]
    }

def my_hook(d):
    if d['status'] == 'finished':
        print("Download Fertig, start Coverting")

def download(url, request_options):
    with youtube_dl.YoutubeDL(get_ydl_options(request_options)) as ydl:
        info = ydl.extract_info(url, download=True)
        trackurl = None
        if info.get('requested_formats') is not None:
            for f in info['requested_formats']:
                if 'audio' in f['format']:
                    trackurl = f['url'] + f.get('play_path', '')

        if trackurl is not None:
            songname = info.get('title', None)
            id  = info.get('id', None)
            sonosTh = Thread(target=callSonos, args = (_speaker, trackurl))
            sonosTh.start()

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
