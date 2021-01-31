import threading
import alsamidi
import alsaseq
import logging
from queue import Queue, Empty

from pyseq.events import parse_event
from pyseq.midiin import MidiInCtrl
from pyseq.model import SequencerModel
from pyseq.view import SequencerView


FROM = [(28, 0), (32, 0)]
TO = [(129, 0), (32, 0)]


alsaseq.client("pyseq", 1, 1, 0)

for midiin in FROM:
    alsaseq.connectfrom(0, midiin[0], midiin[1])

for midiout in TO:
    alsaseq.connectto(1, midiout[0], midiout[1])



def main():
    logging.basicConfig(filename="debug.log", level=logging.DEBUG)
    midi_receiver = MidiInCtrl()
    view = SequencerView()
    sequencer = SequencerModel()

    # MidiIN -> Sequencer
    # MidiIN -> View
    midi_receiver.subscribe(sequencer.in_q)
    midi_receiver.subscribe(view.in_q)
    # Keyboard -> Sequencer
    # Keyboard -> MidiIn
    view.subscribe(sequencer.in_q)
    view.subscribe(midi_receiver.in_q)
    # Sequencer -> View
    sequencer.subscribe(view.in_q)

    midiin_thread = threading.Thread(target=midi_receiver.receive)
    midiin_thread.start()
    emitter = threading.Thread(target=sequencer.emit)
    emitter.start()
    sequencer_thread = threading.Thread(target=sequencer.handleQueue)
    sequencer_thread.start()
    view_thread = threading.Thread(target=view.run)
    view_thread.start()


if __name__ == "__main__":
    main()
