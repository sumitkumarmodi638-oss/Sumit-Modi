"""Track Higgsfield TTS jobs for the voiceover lines (jobs.json).

  python3 jobs.py add 3=<job_id> 4=<job_id> ...   record submitted jobs
  python3 jobs.py url 7=<result_url> ...          record finished results
  python3 jobs.py next 5                          next pending requests as JSON
  python3 jobs.py status                          summary
  python3 jobs.py download                        fetch finished results into takes/ (needs network access)
"""
import json
import os
import subprocess
import sys

from tts_requests import all_requests, paths_for, take_path

HERE = os.path.dirname(os.path.abspath(__file__))
PATH = os.path.join(HERE, "jobs.json")


def load():
    return json.load(open(PATH)) if os.path.exists(PATH) else {}


def save(j):
    json.dump(j, open(PATH, "w"), indent=1, sort_keys=True)


if __name__ == "__main__":
    cmd, args = sys.argv[1], sys.argv[2:]
    j = load()
    if cmd in ("add", "url"):
        for a in args:
            k, v = a.split("=", 1)
            j.setdefault(k, {})["job_id" if cmd == "add" else "url"] = v
        save(j)
    elif cmd == "next":
        todo = [r for r in all_requests() if str(r["index"]) not in j]
        print(json.dumps(todo[: int(args[0]) if args else 5]))
    elif cmd == "status":
        reqs = all_requests()
        print(f"{len(reqs)} unique lines | submitted {len(j)} | finished {sum('url' in v for v in j.values())} | "
              f"downloaded {sum(os.path.exists(os.path.join(HERE, take_path(int(k)) + '.wav')) for k in j)}")
    elif cmd == "download":
        import shutil
        for k, v in sorted(j.items(), key=lambda kv: int(kv[0])):
            dst = os.path.join(HERE, take_path(int(k)) + ".wav")
            if "url" in v and not os.path.exists(dst):
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                r = subprocess.run(["curl", "-sS", "-f", "--max-time", "60", "-o", dst, v["url"]])
                print(("ok  " if r.returncode == 0 else "FAIL") + f" {k} -> {dst}")
            if os.path.exists(dst):  # reuse the take wherever the same line is spoken
                for p in paths_for(int(k)):
                    q = os.path.join(HERE, p + ".wav")
                    if not os.path.exists(q):
                        os.makedirs(os.path.dirname(q), exist_ok=True)
                        shutil.copy(dst, q)
