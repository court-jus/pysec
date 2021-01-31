import alsaseq
import time

from queue import Queue, Empty

from pyseq.events import parse_event

CTRL_CHANNEL = 8

# Main controller notes
PAGE_UP = 41
PAGE_DN = 73
SCALE_UP = 42
SCALE_DN = 74
SPEED_UP = 43
SPEED_DN = 75
ORDER_UP = 44
ORDER_DN = 76
CHANNEL_CHANGE = 105
RATCHETS = [57, 58, 59, 60, 89, 90, 91, 92]
EXIT = 106


class MidiInCtrl:

    def __init__(self):
        self.in_q = Queue()
        self.queues = []

    def subscribe(self, q):
        self.queues.append(q)
    
    def publish(self, message):
        for q in self.queues:
            q.put(message)

    def receive(self, debug=False):
        self.running = True
        if debug:
            print("run receiver")
        while self.running:
            # Read the queue
            try:
                msg = self.in_q.get_nowait()
            except Empty:
                pass
            else:
                ctrl, idx, value = msg
                if ctrl == "exit":
                    self.running = False

            # Read Midi events input
            # Event types:
            # https://www.alsa-project.org/alsa-doc/alsa-lib/seq__event_8h_source.html
            evt = parse_event(*alsaseq.input(), debug=debug)
            if evt["channel"] == CTRL_CHANNEL:
                # Main controller event
                if evt["control"]:
                    control = evt["control"]["control"]
                    value = evt["control"]["value"]
                    if debug:
                        print("control", evt)
                    if 13 <= control <= 20:
                        self.publish(("cc1", control - 13, value))
                    if 29 <= control <= 36:
                        self.publish(("cc2", control - 29, value))
                    if 49 <= control <= 56:
                        self.publish(("cc3", control - 49, value))
                    if 77 <= control <= 84:
                        self.publish(("cc4", control - 77, value))
                elif evt["note"]:
                    note = evt["note"]["note"]
                    if debug:
                        print(evt)
                    if note == PAGE_UP:
                        self.publish(("pagechange", 0, 1))
                    elif note == PAGE_DN:
                        self.publish(("pagechange", 0, -1))
                    elif note == SCALE_UP:
                        self.publish(("scalechange", 0, 1))
                    elif note == SCALE_DN:
                        self.publish(("scalechange", 0, -1))
                    elif note == SPEED_UP:
                        self.publish(("speedchange", 0, 10))
                    elif note == SPEED_DN:
                        self.publish(("speedchange", 0, -10))
                    elif note == ORDER_UP:
                        self.publish(("orderchange", 0, 1))
                    elif note == ORDER_DN:
                        self.publish(("orderchange", 0, -1))
                    elif note == CHANNEL_CHANGE:
                        self.publish(("channelchange", 0, 1))
                    elif note in RATCHETS:
                        idx = note - 57 if note < 89 else note - 85
                        self.publish(("ratchetchange", idx, 1))

                    if note == EXIT:
                        self.publish(("exit", 0, 0))
                        self.running = False
                    self.publish(("message", None, str(evt)))
            elif evt["note"]:
                # Root note change from another controller
                if debug:
                    print("note", evt)
                self.publish(("root", 0, evt["note"]["note"]))

