# Workout library

A static web app listing 50 workouts grouped by primary muscle, each linked to a YouTube form tutorial.

## Run locally

The app has no build step. Serve the folder with any static server:

```bash
python -m http.server 5173
```

Then open http://localhost:5173.

## Edit the workouts

The workouts live in `data/workouts.json`. To change the list or refresh the video picks, edit `WORKOUTS` in `scripts/find_videos.py` and run:

```bash
python scripts/find_videos.py
```

The script searches YouTube for each workout and keeps the most viewed tutorial-length result whose title names the exercise.
