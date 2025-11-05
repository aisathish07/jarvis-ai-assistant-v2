#!/usr/bin/env python3
from core import Assistant

if __name__ == "__main__":
    try:
        Assistant().run()
    except KeyboardInterrupt:
        print("\n👋  bye")
