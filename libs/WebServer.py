#
'''
  Web Server
'''
from M5 import *
import machine
import time
import os
import comm
import json

import M5

import util

from Gtts import Gtts
from Gasr import Gasr
from Gemini import Gemini
from echobox import *

#####################
#
class WebServer:
  #
  #
  def __init__(self, port=80, top="/flash/html"):
    if type(port) == str: port = int(port)
    self.port = port
    self.reader = comm.HttpReader(top)
    self.server = comm.SocketServer(self.reader, "Web", "", port)
    self.started = False
    self.wlan=None
    
    self.talk_sec = 4
    self.label=None
    self.info_label=None
    self.msg_label=None

    self.tts = Gtts()
    self.asr = Gasr()
    self.llm = Gemini()

    self.llm.set_prompt("あなたは、スーパー物知りロボットです。応答は30字以内でお願いします")
    self.registerCommand("/get_file", self.get_content)
    self.registerCommand("/save_file", self.save_content)
    self.registerCommand("/get_file_list", self.get_file_list)
    self.registerCommand("/terminate", self.toggle_state)
    self.registerCommand("/rm_file", self.remove_file)
  
    self.registerCommand("/tts", self.tts)
    self.registerCommand("/talk_str", self.talk_str)
    self.registerCommand("/set_prompt", self.set_prompt)
    self.registerCommand("/asr", self.asr)
    self.registerCommand("/talk", self.talk)
  #
  #
  def renew(self):
    self.server.terminate()
    self.server=comm.SocketServer(self.reader, "Web", "", self.port)
    self.started=False
    return
  #
  #
  def registerCommand(self, name, func):
    if type(func) is str:
      try:
        func = eval(func)
      except:
        print("ERROR to register:", func)
        return

    self.server.reader.registerCommand(name, func)
    return
  
  def connect_wlan(self):
    self.wlan = util.connect_wlan()
    if self.wlan:
      self.show_info(self.wlan.ifconfig()[0])

  def is_connected(self):
    if self.wlan: return True
    return False
  
  def get_ip_addr(self):
    if self.wlan:
      return self.wlan.ifconfig()[0]
    return ""
  #
  # REST-API
  def get_content(self, data):
    param = json.loads(data)
    response = {}
    with open(param['file_name'], 'r') as file:
      response['data'] = file.read()
    return response
  
  def save_content(self, data):
    param = json.loads(data)
    res = False
    with open(param['file_name'], 'w') as file:
      file.write(param['data'])
      res = True
    return res
  
  def remove_file(self, data):
    param = json.loads(data)
    os.remove(param['file_name'])
    return True
  
  def get_file_list(self, data):
    param = json.loads(data)
    dirname=param['dir_name']
    dir_list=os.listdir(param['dir_name'])
    flst=[]
    dlst=[]

    for x in dir_list:
        if (os.stat(f"{dirname}/{x}")[0] & 0x8000) == 0:
            dlst.append(x)
        else:
            flst.append(x)
    response = {'dir_list': dlst, "file_list": flst}
    return response
  
  def talk_str(self, data):
    response = self.llm.request(data)
    print("LLM:",response)
    if data in ['さようなら', 'ありがとう']:
      self.llm.reset_chat()
    self.tts.set_request(response.replace("*", ""))
    #self.tts.talk(response)
    return {'response': response}
  
  def talk(self, data):
    param=json.loads(data)
    tone(2000, 200)
    self.set_talk_sec(param['max_seconds'])
    res=self.asr.do_process(param['max_seconds'], param['threshold'], param['max_count'])
    response = self.llm.request(res['result'])
    print("LLM:",response)
    self.show_info(response)
    if response in ['さようなら', 'ありがとう']:
      self.llm.reset_chat()
    self.tts.set_request(response.replace("*", ""))
    #self.tts.talk(response)
    self.show_info("応答中...")
    return {'response': response}

  def set_talk_sec(self, sec):
    self.talk_sec=sec
    if self.label:
      self.label.setText(str(self.talk_sec))

  def show_info(self, msg=""):
    if self.info_label:
      self.info_label.setText(msg)
      if msg == "---":
        self.show_msg(msg)
      M5.update()

  def show_msg(self, msg=""):
    if self.msg_label:
      self.msg_label.setText(msg)
      M5.update()

  def set_prompt(self, data):
    self.llm.set_prompt(data)
    return True
  #
  #
  def is_started(self):
    return self.started
  #
  #
  def start(self):
    self.server.start()
    self.started=True
    return
  #
  #
  def stop(self):
    try:
      self.server.terminate()
      self.started=False
    except:
      pass
    return
  #
  #
  def update(self, timeout=0.1):
    if self.started:
      self.server.spin_once(timeout)
    return
  
  def toggle_state(self):
    if self.started:
      self.started = False
      return "Web Off"
    else:
      self.started = True
      return "Web On"
    
  def spin(self, timeout=1):
    self.started=True
    while self.started:
      M5.update()
      self.server.spin_once(timeout)
      if self.tts:
        self.tts.check_request()
        self.show_info("---")

  def talk_once(self):
    self.show_info("話して")
    tone(2000, 200)
    res=self.asr.do_process(self.talk_sec, 63, 0)
    self.show_info(res['result'])
    response = self.llm.request(res['result'])
    print("LLM:",response)
    #self.show_info(response)
    if response in ['さようなら', 'ありがとう']:
      self.llm.reset_chat()
    self.tts.set_request(response.replace("*", ""))
    self.show_msg(response)
    return {'response': response}
  
  def toggle_sec(self):
    if self.talk_sec == 4:
      self.talk_sec = 8
      tone(2400, 100)
      time.sleep_ms(50)
      tone(2400, 100)
    else:
      tone(2000, 100)
      self.talk_sec = 4
    if self.label:
      self.label.setText(str(self.talk_sec))
