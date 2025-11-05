import subprocess
import sys
import time
import os, subprocess, sys, time

# force UTF-8 for the subprocess
env = os.environ.copy()
env["PYTHONUTF8"] = "1"
env["PYTHONIOENCODING"] = "utf-8"

proc = subprocess.Popen(
    [sys.executable, "main_minimal.py"],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True,
    env=env,
)

def test_time_command():
    # spawn assistant in subprocess
    proc = subprocess.Popen(
        [sys.executable, "main_minimal.py"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    try:
        # wait for prompt
        while True:
            line = proc.stdout.readline()
            print(line, end="")
            if "Say 'hey jarvis'" in line:
                break
        # fake wake + question
        proc.stdin.write("hey jarvis\n")
        proc.stdin.flush()
        time.sleep(0.5)
        proc.stdin.write("what time is it\n")
        proc.stdin.flush()
        # collect until we see HH:MM
        for _ in range(30):  # 3 s timeout
            out = proc.stdout.readline()
            print(out, end="")
            if ":" in out and len(out.strip()) == 5:
                return  # success
        raise AssertionError("No time returned")
    finally:
        proc.kill()


if __name__ == "__main__":
    test_time_command()
    print("✅ end-to-end pass")
