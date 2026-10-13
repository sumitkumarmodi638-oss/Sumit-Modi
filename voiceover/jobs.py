"""Track Higgsfield TTS jobs for the voiceover lines (jobs.json).

  python3 jobs.py add 3=<job_id> 4=<job_id> ...   record submitted jobs
  python3 jobs.py url 7=<result_url> ...          record finished results
  python3 jobs.py ingest < result.json             record a batch/wait result (job ids + urls)
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
    elif cmd == "ingest":  # paste a generate_audio_batch / jobs_wait JSON result on stdin
        data = json.load(sys.stdin)
        for job in data.get("jobs", []):
            if job.get("job_id"):
                rec = j.setdefault(str(job["index"]), {})
                rec["job_id"] = job["job_id"]
                if job.get("result_url"):
                    rec["url"] = job["result_url"]
        save(j)
        pending = [{"index": int(k), "job_id": v["job_id"]} for k, v in j.items() if "url" not in v]
        print("pending:", json.dumps(pending))
    elif cmd == "next":
        todo = [r for r in all_requests() if str(r["index"]) not in j]
        print(json.dumps(todo[: int(args[0]) if args else 5]))
    elif cmd == "status":
        reqs = all_requests()
        print(f"{len(reqs)} unique lines | submitted {len(j)} | finished {sum('url' in v for v in j.values())} | "
              f"downloaded {sum(any(os.path.exists(os.path.join(HERE, take_path(int(k)) + e)) for e in ('.wav', '.mp3')) for k in j)}")
    elif cmd == "download":
        import shutil
        for k, v in sorted(j.items(), key=lambda kv: int(kv[0])):
            ext = os.path.splitext(v.get("url", ".wav"))[1] or ".wav"
            dst = os.path.join(HERE, take_path(int(k)) + ext)
            if "url" in v and not os.path.exists(dst):
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                r = subprocess.run(["curl", "-sS", "-f", "--max-time", "60", "-o", dst, v["url"]])
                print(("ok  " if r.returncode == 0 else "FAIL") + f" {k} -> {dst}")
            if os.path.exists(dst):  # reuse the take wherever the same line is spoken
                for p in paths_for(int(k)):
                    q = os.path.join(HERE, p + ext)
                    if not os.path.exists(q):
                        os.makedirs(os.path.dirname(q), exist_ok=True)
                        shutil.copy(dst, q)
