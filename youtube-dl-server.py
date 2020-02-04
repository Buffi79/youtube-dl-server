from __future__ import unicode_literals
import json
import os
import subprocess
from queue import Queue
from bottle import route, run, Bottle, request, static_file, redirect, view, template
from threading import Thread
import youtube_dl
from pathlib import Path
from collections import ChainMap
import urllib.parse
import requests
#from requests.utils import requote_uri

_trackurl = None
_trackname = None
_params = None

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
    url = urllib.parse.quote_plus(url)
    print("URL(encode):" + url)

    #setavtransporturi/http%3A%2F%2F192.168.0.5%3A8455%2F$1

    if speaker is None or trackurl is None:
        return "Error: Lautsprecher oder URL fehlt"
     
    url = node + "/" +speaker + "/setavtransporturi/" + url
    r = None
    r = requests.get(url)
    if r is not None:
        return "Error:" + r.status_code+ ": "+r.text
    else:
        return "Error: RESPONSE IS NONE!"
        #return "OK"
    if r is not None and 200 == r.status_code:
        requests.get(node + "/" +speaker + "/play")
        return "OK"
    return "Error:"

@app.route('/')
def redirectRoot():
    return redirect('/youtube-dl', code=302)

@app.route('/youtube-dl')
def dl_queue_list():
    global _params
    speakerlist = ["Bastelzimmer", "Elena", "Dario", "Wohnzimmer", "Bad"]
    _params = {'title': 'so', 'status': "", 'speakerlist': speakerlist}
    return template('./template/index.tpl', _params)

@app.route('/youtube-dl/static/:filename#.*#')
def server_static(filename):
    return static_file(filename, root='./static')

@app.route('/youtube-dl', method='POST')
def q_put():
    global _params
    url = request.forms.get("url")
    speaker = request.forms.get("speaker")
    _params.update({'url': url, 'speaker': speaker})

    if _trackname is None:
        if 'replay' in _params:
            del _params['replay']

    if request.forms.get('buttonaction') == 'refreshspeaker':
        speakerlist = ["Bastelzimmer", "Elena", "Dario", "Wohnzimmer", "Bad", "Küche", "Garten"]
        _params.update({'status': "Lautsprecher aktualisiert", 'speaker': "Sonos", 'speakerlist': speakerlist})
        return template('./template/index.tpl', _params)
   
    if request.forms.get('buttonaction') == 'replay':
           _params.update({'status': "Replay: " + _trackname})
           callSonos(speaker, _trackurl)
           return template('./template/index.tpl', _params)

    if not url:
        _params.update({'status': "URL nicht gesetzt"})
        return template('./template/index.tpl', _params)

    if not speaker or 'Sonos' in speaker:
        _params.update({'status': "Lautsprecher nicht gesetzt", 'speaker': "Sonos"})
        return template('./template/index.tpl', _params)

    options = {
        'format': request.forms.get("format"),
        'speaker': speaker
    }
    status = download(url, options, speaker)

    _params.update({'status': status, 'replay': 'yes'})
    return template('./template/index.tpl', _params)

@app.route("/youtube-dl/update", method="GET")
def update():
    command = ["pip", "install", "--upgrade", "youtube-dl"]
    proc = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    output, error = proc.communicate()
    return {
        "output": output.decode('ascii'),
        "error":  error.decode('ascii')
    }

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

def download(url, request_options, speaker):
    with youtube_dl.YoutubeDL(get_ydl_options(request_options)) as ydl:
        info = ydl.extract_info(url, download=True)
        global _trackurl
        global _trackname
        trackurl = None
        if info.get('requested_formats') is not None:
            for f in info['requested_formats']:
                if 'audio' in f['format']:
                    trackurl = f['url'] + f.get('play_path', '')

        _trackurl = trackurl
        if trackurl is not None:
            songname = info.get('title', None)
            _trackname = songname
            id  = info.get('id', None)
            status = callSonos(speaker, trackurl)
            if 'OK' == status:
                return "Playing: " +songname
            return status

print("Updating youtube-dl to the newest version")
updateResult = update()
print(updateResult["output"])
print(updateResult["error"])

app_vars = ChainMap(os.environ, app_defaults)
app.run(host=app_vars['YDL_SERVER_HOST'], port=app_vars['YDL_SERVER_PORT'], debug=True)

