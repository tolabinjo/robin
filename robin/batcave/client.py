import logging
import time
import threading

from socketIO_client import SocketIO
from protocol import *

# logging.getLogger('socketIO-client').setLevel(logging.DEBUG)
# logging.basicConfig()

io = None

def emit(*args):
	io.emit(*args)

def client(batcave_host, get_device_status, get_device_info, 
		callbacks, app_running):
	global io
	io = SocketIO(*batcave_host)

	for c in callbacks:
		io.on(c, callbacks.get(c))

	def handshake():
		io.emit(Message.HANDSHAKE_DEVICE, get_device_info())
	io.on(Message.RECONNECT, handshake)
	handshake()

	while app_running():
		io.wait(seconds=2)
		io.emit(Message.DEVICE_STATUS, {
			'status': get_device_status(),
			'info': get_device_info()
		})

def run_client(*args):
	t = threading.Thread(target=client,args=args)
	t.daemon = False
	t.start()

