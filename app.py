import M5
from M5 import *
from WebServer import *

web=None
label0=None
label1=None
label2=None
label3=None

def btnA_wasClicked_event(state):
  global web
  print("==", state)
  if web:
    if web.is_connected:
        web.talk_once()
    else:
        web.connect_wlan()
  return

def btnA_wasDoubleclicked_event(state):
  print("=DOUBLE=", state)

def btnA_wasHold_event(state):
  global web
  print("=HOLD=", state)
  if web:
    web.toggle_sec()


def setup():
    global web,label0,label1,label2,label3

    M5.begin()
    Widgets.fillScreen(0x222222)
    label0 = Widgets.Label("4", 27, 46, 1.0, 0xffffff, 0x222222, Widgets.FONTS.DejaVu40)
    label1 = Widgets.Label("秒", 64, 53, 1.0, 0xffffff, 0x222222, Widgets.FONTS.EFontJA24)
    label2 = Widgets.Label("---", 3, 6, 1.0, 0xffffff, 0x222222, Widgets.FONTS.EFontJA24)
    label3 = Widgets.Label("---", 3, 90, 1.0, 0xffffff, 0x222222, Widgets.FONTS.EFontJA24)

    label2.setSize(0.6)
    label3.setSize(0.5)
    BtnA.setCallback(type=BtnA.CB_TYPE.WAS_CLICKED, cb=btnA_wasClicked_event)
    BtnA.setCallback(type=BtnA.CB_TYPE.WAS_DOUBLECLICKED, cb=btnA_wasDoubleclicked_event)
    BtnA.setCallback(type=BtnA.CB_TYPE.WAS_HOLD, cb=btnA_wasHold_event)

    web=WebServer()
    web.label=label0
    web.info_label=label2
    web.msg_label=label3
    web.connect_wlan()    

def loop():
    global web,label0,label1,label2,label3
    M5.update()
    web.server.spin_once(0.01)
    if web.tts:
        if web.tts.check_request():
            web.show_info("---")

def main():
  try:
    setup()
    while True:
      loop()
  except (Exception, KeyboardInterrupt) as e:
    try:
      from utility import print_error_msg
      print_error_msg(e)
    except ImportError:
      print("please update to latest firmware")

if __name__=='__main__':
   main()