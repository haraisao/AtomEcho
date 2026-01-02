#
# Google Speech-to-Text
import sys, os
from M5 import Mic
import time
import json
import binascii
import requests2
from comm import Command

import math
import struct
import util
from echobox import *

####################
#
class Gasr(Command):
  #
  #  Constructor
  def __init__(self, node=None, language='ja-JP'):
    self._endpoint = 'https://speech.googleapis.com/v1/speech:recognize'
    self.key_config = util.load_conf("/flash/apikey.txt")
    self._apikey = self.key_config.get('GOOGLE_SPEECH_KEY')

    self._lang=language

    self._buffer = b''
    self._audio = b''
    self.audio_segments = []

    self._sample_width=2
    self._frame_rate=16000
    self._channels=1

    self._prebuf= b''
    self.request=None
    self.parent = None
    self.response = None
    self.record_s = 3
  #
  def set_config(self, conf):
    self._lang = util.get_config(conf, "google/lang", "ja-JP")
    self._frame_rate = util.get_config(conf, "google/sampleRateHertz",8000)

    return

  #
  #  Request Google Voice Recognition
  def request_speech_recog(self, data):
    url = self._endpoint+"?key="+self._apikey
    headers = {  'Content-Type' : 'application/json; charset=utf-8' }

    audio_data = binascii.b2a_base64(data, newline=False)

    request_data = {
             "config" : { 'languageCode' : self._lang    # en-US, ja-JP, fr-FR
                          , 'encoding' : 'LINEAR16'
                          , 'sampleRateHertz' : self._frame_rate
                          },
             "audio"  : {
                        'content' : audio_data.decode('utf-8')
                          }
            }
    try:
      self.response = requests2.post(url, json=request_data, headers=headers)
      return self.response.text
    except:
      return ""
  #
  #
  def record_audio(self, tm=5, thr=63, max_count=1):
    record_echo(int(tm*1000))
    res = stereo2mono(get_echo_base().pcm_buffer)
    return res

  #
  #
  def do_process(self, seconds=None, thr=41, max_count=0):
    if not self._apikey :
      print("No API key")
      return
    print("---Recording...")
    if seconds: self.record_s = seconds
    data=self.record_audio(self.record_s, thr, max_count)
    tone(2400, 200)
    print("...end")
    if len(data) > 0:

      res_=self.request_speech_recog(data)
      try:
        response=json.loads(res_)
        res=response['results'][0]['alternatives'][0]['transcript']
        print("RESPONSE:", res)
        return { 'result': res , 'error': ''}
      except:
        print("==== Fail")
      return  { 'result': '', 'error': 'Fail to recoginze' }
    else:
      print("==== No sound")
      return None
  #
  #
  def execute(self, data):
    param=json.loads(data)
    tone(2000, 200)

    res=self.do_process(param['max_seconds'], param['threshold'], param['max_count'])
    return res
  
  #
  #
  def set_request(self, data):
    self.request = data
    return True
  #
  #
  def check_request(self):
    if self.request:
      param=json.loads(self.request)
      res=self.do_process(param['max_seconds'], param['threshold'], param['max_count'])
      if res is None:
        self.request=None
      if self.response:
        self.response.close()
        self.response=None
      return res
    return False
  
####################
#
def main():
   recog = Gasr()
   for n in range(5):
     print("==== Start speech...")
     recog.do_process()

if __name__ == '__main__':
  main()
