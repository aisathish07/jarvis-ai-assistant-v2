"""
═══════════════════════════════════════════════════════════════════════════════
FILE: jarvis_voice_input.py
DESCRIPTION: Voice input module with speech recognition and wake word detection
DEPENDENCIES: sounddevice, numpy, faster-whisper (optional)
═══════════════════════════════════════════════════════════════════════════════
"""

import os
import wave
import tempfile
import logging
import threading
from typing import Optional, Callable
import numpy as np
from jarvis_core_optimized import JarvisIntegrated
logger = logging.getLogger("Jarvis.Voice")

try:
    import sounddevice as sd
except ImportError:
    logger.error("sounddevice not installed. Run: pip install sounddevice")


# ═══════════════════════════════════════════════════════════════════════════
# AUDIO RECORDER
# ═══════════════════════════════════════════════════════════════════════════

class AudioRecorder:
    """Record audio from microphone"""
    
    def __init__(self, sample_rate: int = 16000, channels: int = 1):
        self.sample_rate = sample_rate
        self.channels = channels
        self.recording = False
        self.audio_data = []
    
    def start_recording(self):
        """Start recording audio"""
        self.recording = True
        self.audio_data = []
        logger.info("🎤 Recording started...")
    
    def stop_recording(self) -> Optional[str]:
        """Stop recording and save to WAV file"""
        self.recording = False
        
        if not self.audio_data:
            logger.warning("No audio data recorded")
            return None
        
        # Create temporary WAV file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
        temp_path = temp_file.name
        temp_file.close()
        
        # Convert to numpy array
        audio_array = np.concatenate(self.audio_data, axis=0)
        
        # Save as WAV
        with wave.open(temp_path, 'wb') as wf:
            wf.setnchannels(self.channels)
            wf.setsampwidth(2)  # 16-bit
            wf.setframerate(self.sample_rate)
            wf.writeframes((audio_array * 32767).astype(np.int16).tobytes())
        
        logger.info(f"✓ Audio saved to {temp_path}")
        return temp_path
    
    def record_chunk(self, indata, frames, time, status):
        """Callback for audio stream"""
        if self.recording:
            self.audio_data.append(indata.copy())
    
    def record_for_duration(self, duration: float = 5.0) -> Optional[str]:
        """Record audio for specified duration"""
        self.start_recording()
        
        with sd.InputStream(
            channels=self.channels,
            samplerate=self.sample_rate,
            callback=self.record_chunk
        ):
            sd.sleep(int(duration * 1000))
        
        return self.stop_recording()


# ═══════════════════════════════════════════════════════════════════════════
# WAKE WORD DETECTOR (Simple energy-based)
# ═══════════════════════════════════════════════════════════════════════════

class WakeWordDetector:
    """Simple energy-based wake word detection"""
    
    def __init__(self, threshold: float = 0.02, sample_rate: int = 16000):
        self.threshold = threshold
        self.sample_rate = sample_rate
        self.is_listening = False
        self.callback = None
    
    def set_callback(self, callback: Callable):
        """Set callback function for wake word detection"""
        self.callback = callback
    
    def calculate_energy(self, audio_chunk: np.ndarray) -> float:
        """Calculate RMS energy of audio chunk"""
        return np.sqrt(np.mean(audio_chunk ** 2))
    
    def audio_callback(self, indata, frames, time, status):
        """Process audio stream for wake word"""
        if not self.is_listening:
            return
        
        # Calculate energy
        energy = self.calculate_energy(indata)
        
        # Simple energy threshold detection
        if energy > self.threshold:
            logger.info("🎯 Wake word detected!")
            if self.callback:
                self.callback()
    
    def start_listening(self):
        """Start listening for wake word"""
        self.is_listening = True
        logger.info("👂 Listening for wake word...")
        
        with sd.InputStream(
            channels=1,
            samplerate=self.sample_rate,
            callback=self.audio_callback
        ):
            while self.is_listening:
                sd.sleep(100)
    
    def stop_listening(self):
        """Stop listening"""
        self.is_listening = False
        logger.info("Stopped listening for wake word")


# ═══════════════════════════════════════════════════════════════════════════
# VOICE INPUT MANAGER
# ═══════════════════════════════════════════════════════════════════════════

class VoiceInputManager:
    """Complete voice input system"""
    
    def __init__(self, whisper_model=None):
        self.recorder = AudioRecorder()
        self.wake_word = WakeWordDetector()
        self.whisper_model = whisper_model
        self.is_active = False
        self.on_speech_callback = None
    
    def set_speech_callback(self, callback: Callable[[str], None]):
        """Set callback for processed speech text"""
        self.on_speech_callback = callback
    
    def on_wake_word_detected(self):
        """Handle wake word detection"""
        logger.info("Processing voice input...")
        
        # Stop wake word detection temporarily
        self.wake_word.stop_listening()
        
        # Record user speech
        audio_file = self.recorder.record_for_duration(duration=5.0)
        
        if audio_file and self.whisper_model:
            # Transcribe using Whisper
            try:
                segments, info = self.whisper_model.transcribe(
                    audio_file,
                    beam_size=5
                )
                text = " ".join([segment.text for segment in segments]).strip()
                
                logger.info(f"Transcribed: {text}")
                
                # Call speech callback
                if self.on_speech_callback and text:
                    self.on_speech_callback(text)
                
                # Clean up temp file
                os.remove(audio_file)
                
            except Exception as e:
                logger.error(f"Transcription failed: {e}")
        
        # Resume wake word detection
        if self.is_active:
            threading.Thread(
                target=self.wake_word.start_listening,
                daemon=True
            ).start()
    
    def start(self):
        """Start voice input system"""
        self.is_active = True
        self.wake_word.set_callback(self.on_wake_word_detected)
        
        # Start wake word detection in background thread
        thread = threading.Thread(
            target=self.wake_word.start_listening,
            daemon=True
        )
        thread.start()
        
        logger.info("✓ Voice input system started")
    
    def stop(self):
        """Stop voice input system"""
        self.is_active = False
        self.wake_word.stop_listening()
        logger.info("Voice input system stopped")
    
    def manual_record(self) -> Optional[str]:
        """Manually trigger recording (for button press)"""
        logger.info("Manual recording triggered...")
        audio_file = self.recorder.record_for_duration(duration=5.0)
        
        if audio_file and self.whisper_model:
            try:
                segments, info = self.whisper_model.transcribe(
                    audio_file,
                    beam_size=5
                )
                text = " ".join([segment.text for segment in segments]).strip()
                
                # Clean up
                os.remove(audio_file)
                
                return text
                
            except Exception as e:
                logger.error(f"Transcription failed: {e}")
                return None
        
        return None


# ═══════════════════════════════════════════════════════════════════════════
# TESTING
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    # Test manual recording
    print("Voice Input Module")
    print("This module requires faster-whisper for transcription")
    print("Install: pip install faster-whisper")
    
    voice_manager = VoiceInputManager()
    
    print("\nPress Enter to test 5-second recording...")
    input()
    
    print("Recording for 5 seconds...")
    audio_file = voice_manager.recorder.record_for_duration(5.0)
    
    if audio_file:
        print(f"Audio saved to: {audio_file}")
        print("Note: Transcription requires Whisper model to be loaded")