# This is just for testing with laptop without raspberrypi

class FakeGPIO:
    # GPIO modes
    BCM = 11
    BOARD = 10
    
    # Pin modes
    IN = 1
    OUT = 0
    
    # Pull up/down resistors
    PUD_OFF = 20
    PUD_DOWN = 21
    PUD_UP = 22
    
    # Edge detection
    RISING = 31
    FALLING = 32
    BOTH = 33
    
    # PWM frequency
    LOW = 0
    HIGH = 1
    
    @staticmethod
    def setmode(mode):
        print(f"[MOCK] GPIO.setmode({mode})")
    
    @staticmethod
    def setwarnings(flag):
        print(f"[MOCK] GPIO.setwarnings({flag})")
    
    @staticmethod
    def setup(channel, mode, pull_up_down=PUD_OFF):
        print(f"[MOCK] GPIO.setup({channel}, {mode}, pull_up_down={pull_up_down})")
    
    @staticmethod
    def output(channel, state):
        print(f"[MOCK] GPIO.output({channel}, {state})")
    
    @staticmethod
    def input(channel):
        print(f"[MOCK] GPIO.input({channel}) -> 0")
        return 0
    
    @staticmethod
    def cleanup():
        print("[MOCK] GPIO.cleanup()")
    
    @staticmethod
    def PWM(channel, frequency):
        return MockPWM(channel, frequency)
    
    @staticmethod
    def add_event_detect(channel, edge, callback=None, bouncetime=None):
        print(f"[MOCK] GPIO.add_event_detect({channel}, {edge})")
    
    @staticmethod
    def remove_event_detect(channel):
        print(f"[MOCK] GPIO.remove_event_detect({channel})")
    
    @staticmethod
    def event_detected(channel):
        print(f"[MOCK] GPIO.event_detected({channel}) -> False")
        return False

class FakePWM:
    def __init__(self, channel, frequency):
        self.channel = channel
        self.frequency = frequency
        print(f"[MOCK] PWM created on channel {channel} with frequency {frequency}")
    
    def start(self, duty_cycle):
        print(f"[MOCK] PWM.start({duty_cycle}) on channel {self.channel}")
    
    def stop(self):
        print(f"[MOCK] PWM.stop() on channel {self.channel}")
    
    def ChangeDutyCycle(self, duty_cycle):
        print(f"[MOCK] PWM.ChangeDutyCycle({duty_cycle}) on channel {self.channel}")
    
    def ChangeFrequency(self, frequency):
        print(f"[MOCK] PWM.ChangeFrequency({frequency}) on channel {self.channel}")
        self.frequency = frequency

# Create the mock GPIO instance
GPIO = FakeGPIO()