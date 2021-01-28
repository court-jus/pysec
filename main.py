import threading
import alsamidi
import alsaseq
from queue import Queue, Empty

from pyseq.sequencer import Sequencer

alsaseq.client("pyseq", 1, 1, 0)
# Connect to midi monitor
# alsaseq.connectto(1, 129, 0)
# Connect to fluid
alsaseq.connectto(1, 128, 0)
# Connect from system.announce
alsaseq.connectfrom(0, 0, 1)
# Connect from system.timer
alsaseq.connectfrom(0, 0, 0)
# Connect from launchcontrol
alsaseq.connectfrom(0, 28, 0)
# Connect from vmpk
# alsaseq.connectfrom(0, 130, 0)

def receive(q, debug=False):
    while True:
        # Event types:
        # https://www.alsa-project.org/alsa-doc/alsa-lib/seq__event_8h_source.html
        if debug:
            print("run receiver")
        (evtype, flags, tag, queue, timestamp, source, destination, data) = alsaseq.input()
        if evtype == 6:  # NOTE
            if debug:
                print("note", data)
            note = data[1]
            q.put(("root", 0, note))
        elif evtype == 10:  # CONTROL
            if debug:
                print("10", data)
            channel, _, _, _, control, value = data
            if debug:
                print("channel", channel)
                print("control", control)
                print("value", value)
            if channel == 8:
                # Launchcontrol
                if 13 <= control <= 20:
                    q.put(("note", control - 13, value))
                if 29 <= control <= 36:
                    q.put(("vel", control - 29, value))
                if 77 <= control <= 84:
                    q.put(("prob", control - 77, value))
        if debug:
            if evtype == 66:  # PORT_SUBSCRIBED
                print((evtype, flags, tag, queue, timestamp, source, destination, data))
            elif evtype == 30:  # START
                print("start")
            elif evtype == 32:  # STOP
                print("stop")
            elif evtype == 35:  # TEMPO
                print("tempo")
            elif evtype == 36:  # CLOCK
                print("clock")
            elif evtype == 37:  # TICK
                print("tick")
            print("received", evtype)



def main():
    q = Queue()
    debug = False
    receiver = threading.Thread(target=receive, args=(q, debug))
    receiver.start()
    if not debug:
        sequencer = Sequencer()
        emitter = threading.Thread(target=sequencer.emit)
        handler = threading.Thread(target=sequencer.handleQueue, args=(q, ))
        emitter.start()
        handler.start()

if __name__ == "__main__":
    main()