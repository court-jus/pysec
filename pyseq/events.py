NOTE = 6
CONTROL = 10
PORT_SUBSCRIBED = 66
START = 30
STOP = 32
TEMPO = 35
CLOCK = 36
TICK = 37


def parse_event(evtype, flags, tag, queue, timestamp, source, destination, data, debug=False):
    if debug:
        print("Received", evtype, flags, tag, queue, timestamp, source, destination, data)
    result = {
        "channel": None,
        "note": None,
        "control": None,
    }
    if evtype in (NOTE, CONTROL):
        result["channel"] = data[0]
    if evtype == NOTE:
        if debug:
            print("note", data)
        result["note"] = {
            "note": data[1]
        }
    if evtype == CONTROL:
        result["control"] = {
            "control": data[4],
            "value": data[5],
        }
    return result
