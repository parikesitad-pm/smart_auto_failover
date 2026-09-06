import os
import platform
import subprocess
import threading
import time
from enum import Enum
from typing import Optional

try:
    import winsound
    HAS_WINSOUND = True
except ImportError:
    HAS_WINSOUND = False


class SoundType(Enum):
    CONNECT = "connect"
    DISCONNECT = "disconnect"
    FAILOVER = "failover"
    ACTION = "action"
    SUCCESS = "success"
    QOS_APPLIED = "qos_applied"
    CLEAN_COMPLETE = "clean_complete"


class SoundEngine:
    """
    Non-blocking sound synthesizer and audio alert dispatcher for MODULA.
    Supports Windows, macOS, and Linux with a global enable/disable mute toggle.
    """

    _enabled: bool = True
    _lock = threading.Lock()

    @classmethod
    def set_enabled(cls, enabled: bool):
        with cls._lock:
            cls._enabled = enabled

    @classmethod
    def is_enabled(cls) -> bool:
        with cls._lock:
            return cls._enabled

    @classmethod
    def play(cls, sound_type: SoundType):
        if not cls.is_enabled():
            return
        # Run asynchronously so UI never hangs
        threading.Thread(target=cls._play_worker, args=(sound_type,), daemon=True).start()

    @classmethod
    def _play_worker(cls, sound_type: SoundType):
        sys_name = platform.system()
        try:
            if sys_name == "Windows" and HAS_WINSOUND:
                cls._play_windows(sound_type)
            elif sys_name == "Darwin":
                cls._play_macos(sound_type)
            else:
                cls._play_linux(sound_type)
        except Exception:
            pass

    @classmethod
    def _play_windows(cls, sound_type: SoundType):
        if sound_type == SoundType.CONNECT:
            # Ascending melodic chime
            winsound.Beep(784, 90)   # G5
            winsound.Beep(1046, 140) # C6
        elif sound_type == SoundType.DISCONNECT:
            # Descending alert chime
            winsound.Beep(988, 90)   # B5
            winsound.Beep(523, 150)  # C5
        elif sound_type == SoundType.FAILOVER:
            # Urgent Zero-Drop failover alarm
            winsound.Beep(1318, 70)  # E6
            winsound.Beep(880, 70)   # A5
            winsound.Beep(1318, 100) # E6
        elif sound_type == SoundType.ACTION:
            # Soft click blip
            winsound.Beep(1175, 35)  # D6
        elif sound_type == SoundType.SUCCESS:
            # Harmonic success chord
            winsound.Beep(659, 60)   # E5
            winsound.Beep(830, 60)   # G#5
            winsound.Beep(1046, 110) # C6
        elif sound_type == SoundType.QOS_APPLIED:
            # High-tech Cyber pulse
            winsound.Beep(932, 50)
            winsound.Beep(1244, 90)
        elif sound_type == SoundType.CLEAN_COMPLETE:
            winsound.Beep(880, 60)
            winsound.Beep(1108, 100)

    @classmethod
    def _play_macos(cls, sound_type: SoundType):
        sound_map = {
            SoundType.CONNECT: "/System/Library/Sounds/Glass.aiff",
            SoundType.DISCONNECT: "/System/Library/Sounds/Basso.aiff",
            SoundType.FAILOVER: "/System/Library/Sounds/Sosumi.aiff",
            SoundType.ACTION: "/System/Library/Sounds/Tink.aiff",
            SoundType.SUCCESS: "/System/Library/Sounds/Ping.aiff",
            SoundType.QOS_APPLIED: "/System/Library/Sounds/Hero.aiff",
            SoundType.CLEAN_COMPLETE: "/System/Library/Sounds/Purr.aiff",
        }
        snd_file = sound_map.get(sound_type, "/System/Library/Sounds/Tink.aiff")
        if os.path.exists(snd_file):
            subprocess.run(["afplay", snd_file], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    @classmethod
    def _play_linux(cls, sound_type: SoundType):
        # Fallback to system bell
        print("\a", end="", flush=True)
