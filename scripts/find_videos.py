"""Builds data/workouts.json by picking a YouTube tutorial for each workout.

For every workout below it fetches the YouTube search results page, keeps
tutorial-length results whose title mentions the exercise, and picks the most
viewed one. Re-run to refresh the video picks:

    python scripts/find_videos.py
"""
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "data" / "workouts.json"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
}

MIN_SECONDS = 45
MAX_SECONDS = 15 * 60
CANDIDATES = 12

# (name, group, equipment, level, secondary muscles, title keywords)
# A keyword may list alternatives separated by "|".
WORKOUTS = [
    ("Barbell bench press", "Chest", "Barbell", "Intermediate", "Triceps, front delts", ["bench press"]),
    ("Incline dumbbell press", "Chest", "Dumbbells", "Beginner", "Front delts, triceps", ["incline", "press"]),
    ("Push-up", "Chest", "Bodyweight", "Beginner", "Triceps, core", ["push-up|push up|pushup"]),
    ("Chest dip", "Chest", "Dip bars", "Intermediate", "Triceps, front delts", ["dip"]),
    ("Cable crossover", "Chest", "Cable machine", "Beginner", "Front delts", ["cable", "crossover|fly|flye"]),
    ("Dumbbell fly", "Chest", "Dumbbells", "Beginner", "Front delts", ["fly|flye|flies|flyes"]),
    ("Pull-up", "Back", "Pull-up bar", "Intermediate", "Biceps, rear delts", ["pull-up|pull up|pullup"]),
    ("Barbell row", "Back", "Barbell", "Intermediate", "Biceps, lower back", ["row"]),
    ("Lat pulldown", "Back", "Cable machine", "Beginner", "Biceps", ["pulldown|pull-down|pull down"]),
    ("Seated cable row", "Back", "Cable machine", "Beginner", "Biceps, rear delts", ["row"]),
    ("Single-arm dumbbell row", "Back", "Dumbbell", "Beginner", "Biceps, core", ["row"]),
    ("Deadlift", "Back", "Barbell", "Advanced", "Glutes, hamstrings", ["deadlift"]),
    ("T-bar row", "Back", "Barbell", "Intermediate", "Biceps, rear delts", ["t-bar|t bar|tbar"]),
    ("Overhead press", "Shoulders", "Barbell", "Intermediate", "Triceps, upper chest", ["overhead press|ohp|military press|shoulder press"]),
    ("Dumbbell shoulder press", "Shoulders", "Dumbbells", "Beginner", "Triceps", ["shoulder press|overhead press"]),
    ("Lateral raise", "Shoulders", "Dumbbells", "Beginner", "Traps", ["lateral raise"]),
    ("Face pull", "Shoulders", "Cable machine", "Beginner", "Rear delts, traps", ["face pull"]),
    ("Reverse fly", "Shoulders", "Dumbbells", "Beginner", "Upper back", ["reverse|rear delt"]),
    ("Arnold press", "Shoulders", "Dumbbells", "Intermediate", "Triceps", ["arnold press"]),
    ("Barbell curl", "Biceps", "Barbell", "Beginner", "Forearms", ["curl"]),
    ("Hammer curl", "Biceps", "Dumbbells", "Beginner", "Forearms", ["hammer curl"]),
    ("Incline dumbbell curl", "Biceps", "Dumbbells", "Intermediate", "Forearms", ["incline", "curl"]),
    ("Preacher curl", "Biceps", "EZ bar", "Beginner", "Forearms", ["preacher"]),
    ("Chin-up", "Biceps", "Pull-up bar", "Intermediate", "Lats", ["chin-up|chin up|chinup"]),
    ("Triceps pushdown", "Triceps", "Cable machine", "Beginner", "None", ["pushdown|push-down|push down|pressdown"]),
    ("Skull crusher", "Triceps", "EZ bar", "Intermediate", "None", ["skull crusher|skullcrusher"]),
    ("Close-grip bench press", "Triceps", "Barbell", "Intermediate", "Chest, front delts", ["close grip|close-grip"]),
    ("Overhead triceps extension", "Triceps", "Dumbbell", "Beginner", "None", ["overhead", "extension"]),
    ("Bench dip", "Triceps", "Bench", "Beginner", "Chest, front delts", ["dip"]),
    ("Back squat", "Legs", "Barbell", "Advanced", "Glutes, core", ["squat"]),
    ("Front squat", "Legs", "Barbell", "Advanced", "Core, upper back", ["front squat"]),
    ("Romanian deadlift", "Legs", "Barbell", "Intermediate", "Glutes, lower back", ["romanian|rdl"]),
    ("Leg press", "Legs", "Machine", "Beginner", "Glutes", ["leg press"]),
    ("Walking lunge", "Legs", "Dumbbells", "Beginner", "Glutes", ["lunge"]),
    ("Leg extension", "Legs", "Machine", "Beginner", "None", ["leg extension"]),
    ("Lying leg curl", "Legs", "Machine", "Beginner", "Calves", ["leg curl|hamstring curl"]),
    ("Standing calf raise", "Legs", "Machine", "Beginner", "None", ["calf raise"]),
    ("Hip thrust", "Glutes", "Barbell", "Beginner", "Hamstrings", ["hip thrust"]),
    ("Glute bridge", "Glutes", "Bodyweight", "Beginner", "Hamstrings", ["glute bridge"]),
    ("Bulgarian split squat", "Glutes", "Dumbbells", "Intermediate", "Quads", ["bulgarian"]),
    ("Cable kickback", "Glutes", "Cable machine", "Beginner", "Hamstrings", ["kickback"]),
    ("Sumo deadlift", "Glutes", "Barbell", "Advanced", "Quads, back", ["sumo"]),
    ("Step-up", "Glutes", "Bench", "Beginner", "Quads", ["step-up|step up|stepup"]),
    ("Plank", "Core", "Bodyweight", "Beginner", "Shoulders", ["plank"]),
    ("Hanging leg raise", "Core", "Pull-up bar", "Intermediate", "Hip flexors", ["leg raise"]),
    ("Cable crunch", "Core", "Cable machine", "Beginner", "None", ["cable crunch"]),
    ("Russian twist", "Core", "Bodyweight", "Beginner", "Hip flexors", ["russian twist"]),
    ("Ab wheel rollout", "Core", "Ab wheel", "Advanced", "Lats, shoulders", ["ab wheel|rollout|roll out|roll-out"]),
    ("Bicycle crunch", "Core", "Bodyweight", "Beginner", "Obliques", ["bicycle"]),
    ("Dead bug", "Core", "Bodyweight", "Beginner", "Hip flexors", ["dead bug|deadbug"]),
]


def search(query):
    url = "https://www.youtube.com/results?search_query=" + urllib.parse.quote_plus(query)
    req = urllib.request.Request(url, headers=HEADERS)
    html = urllib.request.urlopen(req, timeout=30).read().decode("utf-8", "replace")
    match = re.search(r"var ytInitialData = (\{.*?\});</script>", html, re.S)
    if not match:
        return []
    results = []
    collect(json.loads(match.group(1)), results)
    return results


def collect(node, results):
    if isinstance(node, dict):
        video = node.get("videoRenderer")
        if video:
            results.append(video)
        for value in node.values():
            collect(value, results)
    elif isinstance(node, list):
        for value in node:
            collect(value, results)


def text_of(field):
    if not field:
        return ""
    if "simpleText" in field:
        return field["simpleText"]
    return "".join(run.get("text", "") for run in field.get("runs", []))


def seconds_of(length):
    parts = [int(p) for p in length.split(":") if p.isdigit()]
    total = 0
    for part in parts:
        total = total * 60 + part
    return total


def views_of(view_text):
    digits = re.sub(r"[^\d]", "", view_text)
    return int(digits) if digits else 0


def matches(title, keywords):
    title = title.lower()
    return all(any(alt in title for alt in keyword.split("|")) for keyword in keywords)


def pick(name, keywords):
    best = None
    for video in search(f"how to {name} proper form")[:CANDIDATES]:
        title = text_of(video.get("title"))
        seconds = seconds_of(text_of(video.get("lengthText")))
        if not MIN_SECONDS <= seconds <= MAX_SECONDS or not matches(title, keywords):
            continue
        candidate = {
            "videoId": video["videoId"],
            "videoTitle": title,
            "channel": text_of(video.get("ownerText")),
            "views": views_of(text_of(video.get("viewCountText"))),
        }
        if best is None or candidate["views"] > best["views"]:
            best = candidate
    return best


def main():
    workouts, missing = [], []
    for name, group, equipment, level, secondary, keywords in WORKOUTS:
        video = pick(name, keywords)
        if video is None:
            missing.append(name)
            video = {"videoId": "", "videoTitle": "", "channel": "", "views": 0}
        print(f"{name}: {video['videoId']} | {video['channel']} | {video['videoTitle']} | {video['views']:,}")
        workouts.append(
            {
                "id": re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-"),
                "name": name,
                "group": group,
                "equipment": equipment,
                "level": level,
                "secondary": secondary,
                **video,
            }
        )
        time.sleep(1)
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps(workouts, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"\nWrote {len(workouts)} workouts to {OUT}")
    if missing:
        print("No video found for: " + ", ".join(missing))
        sys.exit(1)


if __name__ == "__main__":
    main()
