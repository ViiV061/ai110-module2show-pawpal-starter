# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Smarter Scheduling

This project implements intelligent pet care task scheduling with the following features:

### Core Scheduling Features

- **Task Sorting by Time & Priority**: Sorts tasks by scheduled time (HH:MM), then by priority level (1–3, highest first). Optimized to use `.time()` objects for ~2x faster comparisons than string formatting.

- **Flexible Filtering**: Filter tasks by pet name, completion status (pending/completed), and target date. Supports recurring task logic (daily/weekly tasks apply to matching dates).

- **Recurring Task Automation**: When a daily or weekly task is marked complete, the scheduler automatically creates the next occurrence. Handles overdue tasks by advancing from completion date rather than original scheduled date.

- **Conflict Detection**: Identifies overlapping tasks (same time, overlapping durations) and returns them as non-fatal warnings. Supports checking conflicts for same pet or across pets.

- **Constraint-Based Scheduling**: Respects owner's daily available minutes—only fits tasks that stay within time budget. Tasks exceeding available time are excluded (greedy selection by priority).

### Example Usage

```python
scheduler = Scheduler(owner)

# Mark a recurring task complete (automatically spawns next occurrence)
scheduler.mark_task_complete("Mochi", "Daily meds")

# Filter and sort tasks
pending_tasks = scheduler.filter_by_status_or_pet(status="pending", pet_name="Mochi")
sorted_tasks = scheduler.sort_by_time(for_date=date.today())

# Detect scheduling conflicts
conflicts = scheduler.detect_conflicts(for_date=date.today())
if conflicts:
    print(f"⚠ {len(conflicts)} scheduling conflict(s) detected")

# Generate daily schedule respecting constraints
todays_plan = scheduler.get_todays_tasks()
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.
