"""
Timetable Generation Using a Genetic Algorithm
Reference implementation for a small academic timetable.

Run from the project root:
    python src/timetable_ga.py
Optional:
    python src/timetable_ga.py --generations 300 --population 80 --seed 7
"""
from __future__ import annotations
import argparse
import csv
import json
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_FILE = ROOT / "data" / "sample_data.json"
OUTPUT_DIR = ROOT / "outputs"

def load_data(path=DATA_FILE):
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    required = {"courses", "faculty", "rooms", "days", "periods"}
    missing = required - data.keys()
    if missing:
        raise ValueError(f"Missing data sections: {sorted(missing)}")
    if not data["courses"] or not data["faculty"] or not data["rooms"]:
        raise ValueError("Courses, faculty and rooms must not be empty.")
    return data

def assignments_for(data):
    """One gene per course: course, faculty, room, day and period."""
    faculty_by_id = {x["id"]: x for x in data["faculty"]}
    rooms_by_id = {x["id"]: x for x in data["rooms"]}
    genes = []
    for course in data["courses"]:
        eligible_faculty = [f for f in data["faculty"]
                            if course["subject"] in f["subjects"]]
        if not eligible_faculty:
            raise ValueError(f"No eligible faculty for {course['id']}")
        eligible_rooms = [r for r in data["rooms"]
                          if r["capacity"] >= course["students"]]
        if not eligible_rooms:
            raise ValueError(f"No room large enough for {course['id']}")
        f = random.choice(eligible_faculty)
        r = random.choice(eligible_rooms)
        genes.append({
            "course_id": course["id"], "faculty_id": f["id"],
            "room_id": r["id"], "day": random.choice(data["days"]),
            "period": random.choice(data["periods"])
        })
    return genes

def fitness(chromosome, data):
    """Higher is better. Hard clashes receive a large penalty."""
    courses = {c["id"]: c for c in data["courses"]}
    faculty = {f["id"]: f for f in data["faculty"]}
    rooms = {r["id"]: r for r in data["rooms"]}
    hard = 0
    soft = 0
    seen_faculty, seen_room, seen_group = set(), set(), set()
    for gene in chromosome:
        slot = (gene["day"], gene["period"])
        fkey = (gene["faculty_id"], *slot)
        rkey = (gene["room_id"], *slot)
        groupkey = (courses[gene["course_id"]]["group"], *slot)
        if fkey in seen_faculty: hard += 1
        if rkey in seen_room: hard += 1
        if groupkey in seen_group: hard += 1
        seen_faculty.add(fkey); seen_room.add(rkey); seen_group.add(groupkey)
        # Faculty availability is a hard constraint.
        available = faculty[gene["faculty_id"]].get("unavailable", [])
        if [gene["day"], gene["period"]] in available: hard += 1
    # Small soft penalty for placing a course in the last period.
    last_period = max(data["periods"])
    soft += sum(1 for g in chromosome if g["period"] == last_period)
    return 1.0 / (1 + 100 * hard + soft)

def tournament(population, scores, k=3):
    candidates = random.sample(range(len(population)), min(k, len(population)))
    winner = max(candidates, key=lambda i: scores[i])
    return population[winner]

def mutate(chromosome, data, rate=0.15):
    courses = {c["id"]: c for c in data["courses"]}
    faculty = {f["id"]: f for f in data["faculty"]}
    for gene in chromosome:
        if random.random() < rate:
            course = courses[gene["course_id"]]
            eligible = [f for f in data["faculty"] if course["subject"] in f["subjects"]]
            f = random.choice(eligible)
            room_options = [r for r in data["rooms"] if r["capacity"] >= course["students"]]
            r = random.choice(room_options)
            gene["faculty_id"] = f["id"]
            gene["room_id"] = r["id"]
            gene["day"] = random.choice(data["days"])
            gene["period"] = random.choice(data["periods"])
    return chromosome

def crossover(parent1, parent2):
    if len(parent1) < 2:
        return [dict(g) for g in parent1]
    point = random.randint(1, len(parent1)-1)
    return ([dict(g) for g in parent1[:point]] +
            [dict(g) for g in parent2[point:]])

def evolve(data, population_size=60, generations=250, mutation_rate=0.15):
    population = [assignments_for(data) for _ in range(population_size)]
    best = None
    best_score = -1
    for _ in range(generations):
        scores = [fitness(ch, data) for ch in population]
        idx = max(range(len(scores)), key=scores.__getitem__)
        if scores[idx] > best_score:
            best, best_score = [dict(g) for g in population[idx]], scores[idx]
        new_population = [[dict(g) for g in best]]  # elitism
        while len(new_population) < population_size:
            p1 = tournament(population, scores)
            p2 = tournament(population, scores)
            child = crossover(p1, p2)
            child = mutate(child, data, mutation_rate)
            new_population.append(child)
        population = new_population
    return best, best_score

def conflict_report(chromosome, data):
    courses = {c["id"]: c for c in data["courses"]}
    faculty, rooms, groups = set(), set(), set()
    conflicts = []
    for g in chromosome:
        slot = (g["day"], g["period"])
        checks = [
            (faculty, (g["faculty_id"], *slot), "Faculty clash"),
            (rooms, (g["room_id"], *slot), "Room clash"),
            (groups, (courses[g["course_id"]]["group"], *slot), "Student-group clash")
        ]
        for seen, key, label in checks:
            if key in seen:
                conflicts.append(f"{label}: {g['course_id']} at {slot}")
            seen.add(key)
    return conflicts

def save_timetable(chromosome, data, path=OUTPUT_DIR/"timetable.csv"):
    courses = {c["id"]: c for c in data["courses"]}
    faculty = {f["id"]: f for f in data["faculty"]}
    rooms = {r["id"]: r for r in data["rooms"]}
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Course", "Subject", "Group", "Faculty", "Room", "Day", "Period"])
        for g in sorted(chromosome, key=lambda x: (data["days"].index(x["day"]), x["period"])):
            c = courses[g["course_id"]]
            writer.writerow([c["id"], c["subject"], c["group"],
                             faculty[g["faculty_id"]]["name"],
                             rooms[g["room_id"]]["name"], g["day"], g["period"]])

def main():
    parser = argparse.ArgumentParser(description="Generate a weekly timetable using a Genetic Algorithm.")
    parser.add_argument("--generations", type=int, default=250)
    parser.add_argument("--population", type=int, default=60)
    parser.add_argument("--seed", type=int, default=7)
    args = parser.parse_args()
    random.seed(args.seed)
    data = load_data()
    best, score = evolve(data, args.population, args.generations)
    save_timetable(best, data)
    conflicts = conflict_report(best, data)
    print(f"Best fitness: {score:.6f}")
    print(f"Remaining clashes: {len(conflicts)}")
    for item in conflicts: print("-", item)
    print(f"Timetable saved to: {OUTPUT_DIR/'timetable.csv'}")

if __name__ == "__main__":
    main()
