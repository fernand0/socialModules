#!/usr/bin/env python3
"""Test DEBUG level logging."""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.abspath("src"))

from socialModules.configMod import logMsg, thread_local

def test_debug_logging():
    print("Testing DEBUG level logging...")
    print("=" * 60)
    
    thread_local.nameA = "[TestDebug]"
    
    # Test different log levels
    logMsg("This is an INFO message", log=1, print_to_console=False)
    logMsg("This is a DEBUG message", log=2, print_to_console=False)
    logMsg("This is a WARNING message", log=3, print_to_console=False)
    
    print("=" * 60)
    print("\nCheck console output above and log file:")
    print("  tail -5 /home/ftricas/usr/var/log/rssSocial.log")

if __name__ == "__main__":
    test_debug_logging()
