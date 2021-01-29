# pysec

MIDI Sequencer written in python

# What?

Inspired by machines like the [Five12 Vector Sequencer](http://www.five12.com/) or
the [Per|Former](https://westlicht.github.io/performer/), I wanted to write a simple sequencer
that could be driven by a MIDI controler like the novation LaunchControl

# How?

It uses the alsa sequencer to send/receive MIDI events. Two threads are running: one
listening to MIDI events and the other one sending out MIDI notes.

# Install

```
virtualenv .venv
. ./.venv/bin/activate
pip install py-midi alsaseq
python main.py
```

# Configuration

For now there is now configuration, you'll have to edit the `main.py` file to change MIDI
channels and controls, depending on your MIDI controller. If you have a LaunchControl XL,
you have nothing to change, just set your controler to factory preset 1.

# Usage

The sequencer runs a 8 steps sequence that is constrained to a specific scale (Minor for now).

MIDI controls are used to change the pitch of each note within the scale, the velocity of each
note and the probablity of each note being played.

When receiving a MIDI note event, the whole sequence is transposed to that root note.
