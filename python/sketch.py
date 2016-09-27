import time
import numpy as np

import signal
import sys

from config import *
from data import *
from emit import *
from record import *
from pulse import *

def signal_handler(signal, frame):
	sys.exit(0)
signal.signal(signal.SIGINT, signal_handler)

output_device = choose_output()
input_device = choose_input()
print input_device.info

settings = Settings(device=output_device, np_format=np.float32)

e = Emitter(settings, output_device)
r = Recorder(settings, input_device)

tone = Chirp(settings, 10000, 1000, 2e5)
tone2 = Chirp(settings, 1000, 10000, 1e4)

while True:
	r.start()
	time.sleep(2)
	r.stop()
	for s in r.buffer.queue:
		e.emit(s)
	r.buffer.queue = []
	e.start()
	time.sleep(2)
	e.stop()
