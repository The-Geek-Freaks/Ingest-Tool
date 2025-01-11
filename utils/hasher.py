"""
Datei-Hash-Funktionalität.
"""
import os
import struct
from typing import Union, BinaryIO

class XXHash64:
    """Pure Python Implementation von xxHash64."""
    
    PRIME64_1 = 11400714785074694791
    PRIME64_2 = 14029467366897019727
    PRIME64_3 = 1609587929392839161
    PRIME64_4 = 9650029242287828579
    PRIME64_5 = 2870177450012600261
    
    def __init__(self, seed: int = 0):
        """Initialisiert den Hasher mit einem Seed."""
        self.seed = seed
        self.reset()
    
    def reset(self):
        """Setzt den internen Zustand zurück."""
        self.total_len = 0
        self.v1 = self.seed + self.PRIME64_1 + self.PRIME64_2
        self.v2 = self.seed + self.PRIME64_2
        self.v3 = self.seed
        self.v4 = self.seed - self.PRIME64_1
        self.memory = bytearray()
        
    def _rotate_left(self, x: int, r: int) -> int:
        """Führt eine Bitrotation nach links durch."""
        return ((x << r) | (x >> (64 - r))) & 0xFFFFFFFFFFFFFFFF
    
    def _mix_keys(self, h64: int, k1: int) -> int:
        """Mischt einen Key in den Hash."""
        k1 = (k1 * self.PRIME64_2) & 0xFFFFFFFFFFFFFFFF
        k1 = self._rotate_left(k1, 31)
        k1 = (k1 * self.PRIME64_1) & 0xFFFFFFFFFFFFFFFF
        h64 ^= k1
        h64 = self._rotate_left(h64, 27)
        h64 = (h64 * self.PRIME64_1 + self.PRIME64_4) & 0xFFFFFFFFFFFFFFFF
        return h64
    
    def _process_stripes(self, data: bytes, start: int, end: int):
        """Verarbeitet 32-Byte Streifen der Eingabedaten."""
        for i in range(start, end, 32):
            # Lade 32 Bytes in 4 Lanes
            k1 = struct.unpack_from("<Q", data, i)[0]
            k2 = struct.unpack_from("<Q", data, i + 8)[0]
            k3 = struct.unpack_from("<Q", data, i + 16)[0]
            k4 = struct.unpack_from("<Q", data, i + 24)[0]
            
            # Mische jede Lane
            self.v1 = (self.v1 * self.PRIME64_2) & 0xFFFFFFFFFFFFFFFF
            self.v1 = self._rotate_left(self.v1, 31)
            self.v1 = (self.v1 * self.PRIME64_1) & 0xFFFFFFFFFFFFFFFF
            self.v1 ^= k1
            
            self.v2 = (self.v2 * self.PRIME64_2) & 0xFFFFFFFFFFFFFFFF
            self.v2 = self._rotate_left(self.v2, 31)
            self.v2 = (self.v2 * self.PRIME64_1) & 0xFFFFFFFFFFFFFFFF
            self.v2 ^= k2
            
            self.v3 = (self.v3 * self.PRIME64_2) & 0xFFFFFFFFFFFFFFFF
            self.v3 = self._rotate_left(self.v3, 31)
            self.v3 = (self.v3 * self.PRIME64_1) & 0xFFFFFFFFFFFFFFFF
            self.v3 ^= k3
            
            self.v4 = (self.v4 * self.PRIME64_2) & 0xFFFFFFFFFFFFFFFF
            self.v4 = self._rotate_left(self.v4, 31)
            self.v4 = (self.v4 * self.PRIME64_1) & 0xFFFFFFFFFFFFFFFF
            self.v4 ^= k4
    
    def update(self, data: Union[bytes, bytearray, memoryview]):
        """Aktualisiert den Hash mit neuen Daten."""
        data = bytes(data)
        self.total_len += len(data)
        
        if self.memory:
            # Fülle den Memory-Buffer auf
            missing = 32 - len(self.memory)
            if len(data) < missing:
                self.memory.extend(data)
                return
            
            # Verarbeite den vollen Memory-Buffer
            self.memory.extend(data[:missing])
            self._process_stripes(self.memory, 0, 32)
            data = data[missing:]
            self.memory.clear()
        
        # Verarbeite volle Streifen
        stripes = len(data) // 32
        if stripes > 0:
            self._process_stripes(data, 0, stripes * 32)
        
        # Speichere übrige Bytes
        remainder = len(data) - (stripes * 32)
        if remainder > 0:
            self.memory.extend(data[-remainder:])
    
    def digest(self) -> int:
        """Berechnet den finalen Hash-Wert."""
        h64 = 0
        
        if self.total_len >= 32:
            h64 = self._rotate_left(self.v1, 1)
            h64 = (h64 + self._rotate_left(self.v2, 7)) & 0xFFFFFFFFFFFFFFFF
            h64 = (h64 + self._rotate_left(self.v3, 12)) & 0xFFFFFFFFFFFFFFFF
            h64 = (h64 + self._rotate_left(self.v4, 18)) & 0xFFFFFFFFFFFFFFFF
        else:
            h64 = self.seed + self.PRIME64_5
        
        h64 = (h64 + self.total_len) & 0xFFFFFFFFFFFFFFFF
        
        # Verarbeite übrige Bytes
        pos = 0
        while pos + 8 <= len(self.memory):
            k1 = struct.unpack_from("<Q", self.memory, pos)[0]
            h64 = self._mix_keys(h64, k1)
            pos += 8
        
        while pos < len(self.memory):
            h64 = (h64 ^ self.memory[pos]) & 0xFFFFFFFFFFFFFFFF
            h64 = (h64 * self.PRIME64_1) & 0xFFFFFFFFFFFFFFFF
            pos += 1
        
        h64 ^= h64 >> 33
        h64 = (h64 * self.PRIME64_2) & 0xFFFFFFFFFFFFFFFF
        h64 ^= h64 >> 29
        h64 = (h64 * self.PRIME64_3) & 0xFFFFFFFFFFFFFFFF
        h64 ^= h64 >> 32
        
        return h64

def calculate_file_hash(file_path: str, buffer_size: int = 8192) -> str:
    """Berechnet den xxHash64-Wert einer Datei."""
    hasher = XXHash64()
    
    with open(file_path, 'rb') as f:
        while True:
            data = f.read(buffer_size)
            if not data:
                break
            hasher.update(data)
    
    return format(hasher.digest(), '016x')

def calculate_string_hash(text: str) -> str:
    """Berechnet den xxHash64-Wert eines Strings."""
    hasher = XXHash64()
    hasher.update(text.encode('utf-8'))
    return format(hasher.digest(), '016x')
