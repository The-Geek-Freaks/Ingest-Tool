#!/usr/bin/env python3
# -*- coding: utf-8 -*-

def format_size(size):
    """Formatiert eine Größe in Bytes in eine lesbare Form."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} PB"

def get_drive_space(path):
    """Ermittelt den verfügbaren Speicherplatz eines Laufwerks."""
    try:
        import os
        total, used, free = os.statvfs(path) if os.name != 'nt' else (0, 0, 0)
        if os.name == 'nt':
            import ctypes
            free_bytes = ctypes.c_ulonglong(0)
            ctypes.windll.kernel32.GetDiskFreeSpaceExW(
                ctypes.c_wchar_p(path), None, None, ctypes.pointer(free_bytes)
            )
            return free_bytes.value
        return free * total.f_frsize
    except Exception:
        return None
