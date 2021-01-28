import random
import time
import alsamidi
import alsaseq
from queue import Queue, Empty

def clear():
    print("\033[2J")

def printat(x, y, char):
    print(f"\033[{y};{x}f{char}")

def eraseline(y, width):
    print(f"\033[{y};0f" + " " * width)
    print(f"\033[2K")

def message(text):
    eraseline(10, 100)
    printat(1, 10, text)


# clear()
# for i in range(10):
#     printat(i + 1, 1, i)

# for i in range(40):
#     printat((i % 10)+1, 2, "*")
#     time.sleep(0.05)
#     printat((i % 10)+1, 2, " ")

# eraseline(1, 100)
# print("\033[15;15fDone")
MINOR_SCALE = [0, 2, 3, 5, 7, 9, 11]
class Sequencer:

    def __init__(self):
        clear()
        self.root = 62
        self.length = 8
        self.prob = [100] * 8
        self.vel = [127] * 8
        self.idx = 0
        self.scale = []
        self.notes = [self.root] * 8
        self.print_note_width = 4
        self.set_scale(MINOR_SCALE)
    
    def set_scale(self, scale):
        self.scale = scale
        self.printnotes()

    def printnotes(self):
        eraseline(1, 100)
        for idx, note in enumerate(self.notes):
            printat(idx * self.print_note_width + 1, 1, note)
    
    def playnote(self, note_idx):
        dur = 100
        printat(note_idx * self.print_note_width + 2, 2, "_")
        if random.randint(0, 99) > self.prob[note_idx]:
            printat(note_idx * self.print_note_width + 2, 2, ".")
            time.sleep(dur * 2 / 1000)
            printat(note_idx * self.print_note_width + 2, 2, " ")
        else:
            chosen = self.notes[note_idx]
            vel = self.vel[note_idx]
            note = (0, chosen, vel)
            noteon = alsamidi.noteonevent(*note)
            noteoff = alsamidi.noteoffevent(*note)
            alsaseq.output(noteon)
            printat(note_idx * self.print_note_width + 2, 2, "*")
            time.sleep(dur / 1000)
            alsaseq.output(noteoff)
            printat(note_idx * self.print_note_width + 2, 2, " ")
            time.sleep(dur / 1000)
    
    def getnote(self, value):
        note = self.root
        temp_scale = self.scale[:]
        possible = []
        while note < 127:
            possible.append(note)
            interval = temp_scale.pop(0)
            note = self.root + interval
            temp_scale.append(interval + 12)
        note = self.root
        temp_scale = self.scale[:]
        while note > 0:
            possible.append(note)
            interval = temp_scale.pop()
            note = self.root + interval
            temp_scale.insert(0, interval - 12)
        possible = sorted(list(set(possible)))
        message(possible)
        chosen = int(value * (len(possible) - 1) / 127)
        return possible[chosen]
    
    def handleQueue(self, q):
        while True:
            try:
                msg = q.get_nowait()
            except Empty:
                pass
            else:
                ctrl, idx, value = msg
                if ctrl == "root":
                    old_root = self.root
                    self.root = value
                    transposed = self.root - old_root
                    for idx in range(len(self.notes)):
                        self.notes[idx] += transposed
                    message(f"Root note changed to {self.root}")
                    self.printnotes()
                elif ctrl == "prob":
                    self.prob[idx] = value / 127 * 100
                    message(f"Probability {idx} changed to {self.prob[idx]}")
                elif ctrl == "note":
                    self.notes[idx] = self.getnote(value)
                    # message(f"Note {idx} changed to {self.notes[idx]}")
                    self.printnotes()
                elif ctrl == "vel":
                    self.vel[idx] = value
                    message(f"Velocity {idx} changed to {self.vel[idx]}")

    def emit(self):
        while True:
            self.idx += 1
            note_idx = self.idx % len(self.notes)
            # if note_idx == 0:
            #     chosen = random.randint(0, len(self.notes))
            #     self.notes[chosen] = self.getnote()
            #     self.printnotes()
                # message(f"Randomly change one of the notes {chosen}")

                # self.set_scale(self.scale)
            self.playnote(note_idx)
