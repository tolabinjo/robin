import numpy as np
from scipy.signal import chirp

def pulse_source_from_dict(d):
	def get_from_device(device):
		if d.get("type") == "tone":
			return Tone(
				device,
				1000 * d.get("khzStart"),
				d.get("usDuration"),
				d.get("isSquare")
			)
		elif d.get("type") == "chirp":
			return Chirp(
				device,
				1000 * d.get("khzStart"),
				1000 * d.get("khzEnd"),
				d.get("usDuration"),
				"logarithmic" if d.get("isLogarithmic") else "linear",
				d.get("isSquare")
			)
		elif d.get("type") == "click":
			return Click(
				device,
				d.get("usDuration")
			)
		else:
			raise Exception("Unable to parse Pulse from dict")
	return get_from_device

def dict_from_pulse(p):
	d = {
		"type": "click" if type(p) is Click else (
			"chirp" if type(p) is Chirp else (
				"tone" if type(p) is Tone else "?"
			)
		),
		"usDuration": p.us_duration
	}
	if type(p) is Tone:
		d["khzStart"] = p.frequency / 1000
		d["isSquare"] = p.square
	elif type(p) is Chirp:
		d["khzStart"] = p.f0 / 1000
		d["khzEnd"] = p.f1 / 1000
		d["isLogarithmic"] = p.method == "logarithmic"
		d["isSquare"] = p.square
	return d

def default_pulse_source():
	return pulse_source_from_dict({
		'type': 'chirp',
		'usDuration': 5e3,
		'khzStart': 50,
		'khzEnd': 25
	})

class Pulse(object):
	def __init__(self, device, us_duration, square=False):
		self.us_duration = us_duration
		self.device = device
		self.square = square
		self.__t_axis = None
		self.__rendered = None

	def t_axis(self):
		if not self.__t_axis is None:
			return self.__t_axis
		self.__t_axis = np.linspace(
			0,
			1e-6 * self.us_duration,
			1e-6 * self.us_duration * self.device.rate
		)
		return self.__t_axis

	def band(self):
		return (0, self.device.rate / 2)

	def render(self):
		if not self.__rendered is None:
			return self.__rendered
		r = self._render()
		if self.square:
			r[r > 0] = 1
			r[r < 0] = -1
		if self.device.channels == 1:
			self.__rendered = r
		else: 
			self.__rendered = (
				32767 if self.device.np_format == np.int16 else 1 
			) * np.transpose(np.array(
				[r for _ in xrange(self.device.channels)]
			))
		return self.__rendered

	def _render(self):
		raise Exception("Pulse should not be instantiated directly")

class Silence(Pulse):
	def __init__(self, device, us_duration):
		super(Silence, self).__init__(device, us_duration)

	def _render(self):
		return np.zeros(len(self.t_axis()))

class Tone(Pulse):
	def __init__(self, device, frequency, us_duration, square=False):
		super(Tone,self).__init__(device, us_duration, square)
		self.frequency = frequency

	def __str__(self):
		return "tone-%sk-%sms%s" % (
			str(self.frequency / 1000),
			str(self.us_duration / 1000),
			"-square" if self.square else ""
		)

	def _render(self):
		return np.cos(2 * np.pi * self.frequency * self.t_axis())

	def band(self):
		leakage = 2500 # pretty arbitrary
		return (self.frequency - leakage, self.frequency + leakeage)

class Chirp(Pulse):
	def __init__(self, device, f0, f1, us_duration,
			method='linear', square=False):
		super(Chirp,self).__init__(device, us_duration, square)
		self.f0 = f0
		self.f1 = f1
		self.method = method

	def __str__(self):
		return "chirp-%sk-%sk-%sms-%s%s" % (
			str(self.f0 / 1000),
			str(self.f1 / 1000),
			str(self.us_duration / 1000),
			self.method,
			"-square" if self.square else ""
		)

	def _render(self):
		times = self.t_axis()
		t1 = times[-1]
		return chirp(
			t=self.t_axis(),
			f0=self.f0,
			f1=self.f1,
			t1=t1,
			method=self.method
		)

	def band(self):
		return (self.f0, self.f1)

class Click(Pulse):
	def __init__(self, device, us_duration):
		super(Click,self).__init__(device, us_duration)

	def __str__(self):
		return "click-%sms" % (str(self.us_duration / 1000))

	def _render(self):
		return np.random.normal(0, 1, size=len(self.t_axis()))

	def band(self):
		# This bad boy is very broadband but we probably can get rid of audible
		# sound anyway, since the tweeters are loudest at > 15k.
		return (1.5e4, self.device.rate / 2)
