import threading
import alsamidi
import alsaseq
from queue import Queue, Empty

from pyseq.sequencer import Sequencer
from pyseq.events import parse_event

FROM = [(28, 0)]
TO = [(128, 0)]
CTRL_CHANNEL = 8
DEBUG = False

# Main controller notes
PAGE_UP = 41
PAGE_DN = 73
SCALE_UP = 42
SCALE_DN = 74
EXIT = 106


alsaseq.client("pyseq", 1, 1, 0)

for midiin in FROM:
    alsaseq.connectfrom(0, midiin[0], midiin[1])

for midiout in TO:
    alsaseq.connectto(1, midiout[0], midiout[1])


def receive(q, debug=False):
    running = True
    if debug:
        print("run receiver")
    while running:
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
                    q.put(("cc1", control - 13, value))
                if 29 <= control <= 36:
                    q.put(("cc2", control - 29, value))
                if 77 <= control <= 84:
                    q.put(("cc3", control - 77, value))
            elif evt["note"]:
                note = evt["note"]["note"]
                if debug:
                    print(evt)
                if note == PAGE_UP:
                    q.put(("pagechange", 0, 1))
                if note == PAGE_DN:
                    q.put(("pagechange", 0, -1))
                if note == SCALE_UP:
                    q.put(("scalechange", 0, 1))
                if note == SCALE_DN:
                    q.put(("scalechange", 0, -1))
                if note == EXIT:
                    q.put(("exit", 0, 0))
                    running = False
        elif evt["note"]:
            # Root note change from another controller
            if debug:
                print("note", evt)
            note = data[1]
            q.put(("root", 0, evt["note"]["note"]))



def main():
    q = Queue()
    debug = DEBUG
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
