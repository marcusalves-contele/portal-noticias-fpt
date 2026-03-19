#!/usr/bin/env python3
"""PRISM OS entry point. Runs auth_proxy from the correct directory."""
import os, subprocess, sys
os.chdir(os.path.join(os.path.dirname(__file__), "nutella-creator"))
sys.exit(subprocess.call([sys.executable, "auth_proxy.py"]))
