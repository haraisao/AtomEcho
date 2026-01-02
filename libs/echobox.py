'''
  EchoBox
'''
from M5 import *

from hardware import I2C
from hardware import Pin
from base import AtomicEchoBase
import time
import _thread

g_base_echo=None
g_speaking=False

###################
#
def init_i2c():
    return I2C(1, scl=Pin(39), sda=Pin(38), freq=100000)

def init_audio_base():
  global g_base_echo
  if g_base_echo is None:
    i2c1 = I2C(1, scl=Pin(39), sda=Pin(38), freq=100000)
    if len(i2c1.scan() ) > 2:
      i2c1 = I2C(1, scl=Pin(39), sda=Pin(38), freq=100000)
    try:
      g_base_echo = AtomicEchoBase(i2c1, 0x18, 1, 16000, 8, 6, 7, 5)
    except:
      print("Error in init_audio_base")
      g_base_echo=None
  return g_base_echo

def record_echo(duration=3000):
    global g_base_echo
    if g_base_echo is None: init_audio_base()
    try:
      g_base_echo.record(rate=16000, bits=16, channel=1, duration=duration)
    except:
      print("Error in record_echo")
      g_base_echo = None

def play_audio(data, rate=16000, channel=1, volume=70, wait=True):
    global g_base_echo, g_speaking
    if g_base_echo is None: init_audio_base()
    while g_speaking:
      time.sleep_ms(100)
    try:
      g_base_echo.set_volume(volume)
      duration = int(len(data)/rate/2/channel * 1000)
      tm_s=time.time_ns() // 1000000
      g_speaking = True

      g_base_echo.play_raw(
          data, rate=rate, bits=16, channel=channel, duration=duration
      )
      if wait:
        wait_speaking(tm_s, duration)
      else:
        _thread.start_new_thread(wait_speaking, (tm_s, duration))
    except (Exception) as e:
      print("Error in play_audio")
      try:
        from utility import print_error_msg
        print_error_msg(e)
      except:
        pass
      g_base_echo = None
      g_speaking = False

#
#
def wait_speaking(tm_s, duration):
  global g_speaking
  if g_speaking :
    while ((time.time_ns() // 1000000) - tm_s) < duration :
      time.sleep_ms(100)
    g_speaking = False

def play(volume=70):
  global g_base_echo
  g_base_echo.mic.deinit()
  play_audio(g_base_echo.pcm_buffer, volume=volume)

def get_echo_base():
  global g_base_echo
  if g_base_echo is None: init_audio_base()
  return g_base_echo

def mic_is_running():
  return g_base_echo.mic.is_running()

def stereo2mono(buf):
  buf1=bytearray(len(buf)//2)
  for i in range(len(buf1)//2):
      buf1[i*2] = buf[i*4]
      buf1[i*2+1] = buf[i*4+1]
  return buf1

def st2m8(buf):
  buf1=bytearray(len(buf)//4)
  for i in range(len(buf1)//2):
      buf1[i*2] = buf[i*8]
      buf1[i*2+1] = buf[i*8+1]
  return buf1

import math
import struct
def calc_power(indata):
  indata2 = struct.unpack(f"{len(indata) / 2:.0f}h", indata)
  sqr_sum = sum([x*x for x in indata2])
  rms = math.sqrt(sqr_sum/len(indata2))
  power = 20 * math.log10(rms) if rms > 0.0 else -math.inf 
  return power

def tone(f, ms, volume=50):
  global g_base_echo
  if g_base_echo is None: init_audio_base()

  g_base_echo.set_volume(volume)
  g_base_echo.tone(f, ms)
  time.sleep_ms(ms)