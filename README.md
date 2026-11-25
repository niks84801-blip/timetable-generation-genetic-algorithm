# Timetable Generation Using a Genetic Algorithm

A small Python reference implementation that generates a weekly academic timetable using a Genetic Algorithm (GA).

## Requirements
- Python 3.9 or newer
- No third-party packages are required.

## Run
From this folder, run:

```bash
python src/timetable_ga.py
```

Optional settings:

```bash
python src/timetable_ga.py --generations 300 --population 80 --seed 7
```

The generated timetable is saved to `outputs/timetable.csv`.

## Project structure
- `src/timetable_ga.py` — chromosome creation, fitness evaluation, tournament selection, crossover, mutation, elitism and output.
- `data/sample_data.json` — example courses, faculty, rooms, days and periods. Replace this with your institution's data.
- `outputs/` — generated timetable CSV.
- `tests/` — reserved for additional test cases.

## Important note
This is a reference implementation using sample academic data, not verified institutional data. The Genetic Algorithm searches for a good candidate; it does not guarantee a globally optimal timetable. Review the generated CSV and conflict report before using it. Add actual project screenshots and test results after running it.

## GitHub
Create a new public repository, upload the contents of this folder, and copy the repository URL into Section 5.5 of the project report.
