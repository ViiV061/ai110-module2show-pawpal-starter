from datetime import date, datetime, time

from pawpal_system import Owner, Pet, Scheduler, Task


def build_demo_data() -> Owner:
	"""Create one owner, two pets, and at least three timed tasks for today."""
	owner = Owner(name="Jordan", available_minutes=180)

	dog = Pet(name="Mochi", species="dog", age=4)
	cat = Pet(name="Luna", species="cat", age=2)

	today = date.today()
	# Intentionally add tasks out of chronological order for sorting demo.
	dog.add_task(
		Task(
			description="Give medication",
			scheduled_time=datetime.combine(today, time(hour=12, minute=0)),
			frequency="daily",
			duration_minutes=10,
			priority=3,
		)
	)
	dog.add_task(
		Task(
			description="Morning walk",
			scheduled_time=datetime.combine(today, time(hour=8, minute=0)),
			frequency="once",
			duration_minutes=30,
			priority=3,
		)
	)
	dog.add_task(
		Task(
			description="Training session",
			scheduled_time=datetime.combine(today, time(hour=8, minute=20)),
			frequency="weekly",
			duration_minutes=20,
			priority=2,
		)
	)
	cat.add_task(
		Task(
			description="Evening play",
			scheduled_time=datetime.combine(today, time(hour=18, minute=30)),
			frequency="daily",
			duration_minutes=25,
			priority=2,
		)
	)
	cat.add_task(
		Task(
			description="Litter cleanup",
			scheduled_time=datetime.combine(today, time(hour=8, minute=15)),
			frequency="daily",
			duration_minutes=20,
			priority=2,
		)
	)

	# Add a task at the EXACT same time as Morning walk to demonstrate conflict detection.
	cat.add_task(
		Task(
			description="Cat feeding",
			scheduled_time=datetime.combine(today, time(hour=8, minute=0)),
			frequency="once",
			duration_minutes=15,
			priority=3,
		)
	)

	# Mark one task completed to demonstrate status filtering.
	cat.complete_task("Litter cleanup")

	owner.add_pet(dog)
	owner.add_pet(cat)
	return owner


def print_todays_schedule(owner: Owner) -> None:
	scheduler = Scheduler(owner)
	todays_tasks = scheduler.get_todays_tasks()

	print("Today's Schedule")
	print("=" * 16)

	if not todays_tasks:
		print("No tasks scheduled for today.")
		return

	for idx, task in enumerate(todays_tasks, start=1):
		time_label = task.scheduled_time.strftime("%H:%M") if task.scheduled_time else "Unscheduled"
		print(
			f"{idx}. {time_label} | {task.description} "
			f"({task.duration_minutes} min, priority {task.priority}, {task.frequency})"
		)


def print_target_feature_demo(owner: Owner) -> None:
	"""Show sorting, filtering, recurring behavior, and conflict detection."""
	scheduler = Scheduler(owner)
	today = date.today()

	print("\nFeature Demo")
	print("=" * 12)

	print("\n1) Sorted pending tasks for today")
	for task in scheduler.sort_by_time(for_date=today):
		time_label = task.scheduled_time.strftime("%H:%M") if task.scheduled_time else "Unscheduled"
		print(f"- {time_label} | {task.description} | priority {task.priority}")

	print("\n2) Filter: Mochi + pending")
	for task in scheduler.filter_by_status_or_pet(status="pending", pet_name="Mochi", for_date=today):
		print(f"- {task.description} ({task.frequency})")

	print("\n3) Filter: completed tasks")
	for task in scheduler.filter_by_status_or_pet(status="completed", for_date=today):
		print(f"- {task.description}")

	print("\n4) Recurring tasks included today")
	for task in scheduler.filter_tasks(status="pending", for_date=today):
		if task.frequency in {"daily", "weekly"}:
			print(f"- {task.description} [{task.frequency}]")

	print("\n5) Conflicts for today's schedule (lightweight warning)")
	conflicts = scheduler.detect_conflicts(for_date=today, tasks=scheduler.get_todays_tasks())
	if not conflicts:
		print("- No conflicts found ✓")
	else:
		print(f"⚠ WARNING: {len(conflicts)} conflict(s) detected:")
		for first, second in conflicts:
			first_time = first.scheduled_time.strftime("%H:%M") if first.scheduled_time else "Unscheduled"
			second_time = second.scheduled_time.strftime("%H:%M") if second.scheduled_time else "Unscheduled"
			print(f"  • {first.description} ({first_time}) overlaps with {second.description} ({second_time})")


if __name__ == "__main__":
	owner = build_demo_data()
	print_todays_schedule(owner)
	print_target_feature_demo(owner)
