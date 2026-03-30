from datetime import date, datetime, time

from pawpal_system import Owner, Pet, Scheduler, Task


def build_demo_data() -> Owner:
	"""Create one owner, two pets, and at least three timed tasks for today."""
	owner = Owner(name="Jordan", available_minutes=180)

	dog = Pet(name="Mochi", species="dog", age=4)
	cat = Pet(name="Luna", species="cat", age=2)

	today = date.today()
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
			description="Give medication",
			scheduled_time=datetime.combine(today, time(hour=12, minute=0)),
			frequency="daily",
			duration_minutes=10,
			priority=3,
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


if __name__ == "__main__":
	owner = build_demo_data()
	print_todays_schedule(owner)
