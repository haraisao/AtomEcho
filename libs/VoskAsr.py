#
'''
  Vosk: Speech-to-Text
'''
import sys, os
from M5 import Mic
import time
import json
import binascii
import requests2
from comm import Command

from echobox import *

###############
#
class VoskAsr(Command):
  #
  #  Constructor
  def __init__(self, host="192.168.0.100", language='ja-JP'):
    self.host = host
    self._endpoint = "http://%s:8000/vosk" % self.host
    self._lang=language

    self._buffer = b''
    self._audio = b''
    self.audio_segments = []

    self._sample_width=2
    self._frame_rate = 16000
    self._channels = 1

    self._prebuf = b''
    self.silent_power = 63
    self.silence = bytearray(self._frame_rate * 5)
    
    self.parent = None
    self.request = None
    init_audio_base()

  #
  #
  def get_silent_power(self, len=10):
    powers_=[]
    count=0
    for x in range(len):
      val=self.calc_power(self.record_audio_time(2))
      if val > 0:
        powers_.append(val)
        if count >= 5:
          break
    self.silent_power = sum(powers_)/count
    print(self.silent_power)
    return self.silent_power
  #
  #
  def record_silence(self, tm=5):
    self.silence=self.record_audio_time(tm)
    return
  #
  #  Request Google Voice Recognition
  def request_speech_recog(self, data):
    url = self._endpoint
    headers = {  'Content-Type' : 'application/json; charset=utf-8' }
    audio_data = binascii.b2a_base64(data, newline=False)
    request_data = audio_data.decode()
    #try:
    response = requests2.post(url, data=request_data, headers=headers)
    return response.text
    #except:
    #  print("Error in request")
    #  return None
  #
  #
  def record_audio(self, tm=5, thr=-1):
    record_echo(int(tm*1000))
    res = stereo2mono(get_echo_base().pcm_buffer)
    return res+self.silence

  #
  #
  def do_process(self, max_seconds=10, thr=-1):
    print("Start recording...")
    data=self.record_audio(max_seconds, thr)
    print("Reuqest ASR")
    if len(data) > 0:
      #self.show_message("音声認識中…")
      try:
        res=self.request_speech_recog(data)
        if res is None: return None
        print("RESPONSE:", res)
        return { 'result': res , 'error': ''}
      except:

        print("==== Fail")
        pass
      return { 'result': '', 'error': 'Fail to recoginze' }
    else:
      print("==== No sound")
    return None
  #
  #
  def run(self):
    while True:
      self.do_process()
  #
  #
  def execute(self, data):
    if isinstance(data, str):
      try:
        val = eval(data)
        return self.do_process(*val)
      except:
        return { 'result': '', 'error': 'Invalid params' }
    return False

  #
  #
  def set_request(self, data):
      self.request = data
      return True
  #
  #
  def check_request(self):
      if self.request:
          #self.show_message("音声入力…", 0x8888ff)
          param=json.loads(self.request)
          #print(param)
          res=self.do_process(param['max_seconds'], param['threshold'])
          if res is None:
            self.request=None
          #self.show_message("")
          return res
      return False
  