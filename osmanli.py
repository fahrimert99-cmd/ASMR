"""Geriye uyumluluk: `python osmanli.py ...` == `python harita.py --senaryo osmanli ...`"""
import sys

from harita import main

if __name__ == "__main__":
    sys.argv = [sys.argv[0], "--senaryo", "osmanli"] + sys.argv[1:]
    sys.exit(main())
