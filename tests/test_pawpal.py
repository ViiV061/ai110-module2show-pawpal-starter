from datetime import date, datetime, time, timedelta

from pawpal_system import Owner, Pet, Scheduler, Task


def test_task_completion_changes_status() -> None:
	"""Calling mark_completed should update task completion state."""
	task = Task(description="Feed breakfast")

	assert task.is_completed is False
	task.mark_completed()
	assert task.is_completed is True


def test_add_task_increases_pet_task_count() -> None:
	"""Adding a task to a pet should increase the number of tasks."""
	pet = Pet(name="Mochi", species="dog", age=4)
	initial_count = len(pet.get_tasks())

	pet.add_task(Task(description="Evening walk"))

	assert len(pet.get_tasks()) == initial_count + 1


def test_sort_tasks_orders_by_time_then_priority() -> None:
	owner = Owner(name="Jordan", available_minutes=120)
	pet = Pet(name="Mochi", species="dog", age=4)
	today = date.today()

	pet.add_task(
		Task(
			description="Later low priority",
			scheduled_time=datetime.combine(today, time(hour=9, minute=0)),
			priority=1,
		)
	)
	pet.add_task(
		Task(
			description="Earlier task",
			scheduled_time=datetime.combine(today, time(hour=8, minute=30)),
			priority=1,
		)
	)
	pet.add_task(
		Task(
			description="Same time higher priority",
			scheduled_time=datetime.combine(today, time(hour=9, minute=0)),
			priority=3,
		)
	)
	owner.add_pet(pet)

	sorted_tasks = Scheduler(owner).sort_tasks(for_date=today)

	assert [task.description for task in sorted_tasks] == [
		"Earlier task",
		"Same time higher priority",
		"Later low priority",
	]


def test_sort_by_time_orders_hhmm_strings_correctly() -> None:
	owner = Owner(name="Jordan", available_minutes=120)
	pet = Pet(name="Mochi", species="dog", age=4)
	today = date.today()

	pet.add_task(Task(description="Nine", scheduled_time=datetime.combine(today, time(hour=9, minute=0))))
	pet.add_task(Task(description="Eight thirty", scheduled_time=datetime.combine(today, time(hour=8, minute=30))))
	pet.add_task(Task(description="Eight", scheduled_time=datetime.combine(today, time(hour=8, minute=0))))
	owner.add_pet(pet)

	sorted_tasks = Scheduler(owner).sort_by_time(for_date=today)

	assert [task.description for task in sorted_tasks] == ["Eight", "Eight thirty", "Nine"]


def test_filter_tasks_by_pet_and_status() -> None:
	owner = Owner(name="Jordan", available_minutes=120)
	dog = Pet(name="Mochi", species="dog", age=4)
	cat = Pet(name="Luna", species="cat", age=2)
	today = date.today()

	dog_task = Task(
		description="Dog walk",
		scheduled_time=datetime.combine(today, time(hour=8, minute=0)),
	)
	completed_task = Task(
		description="Completed grooming",
		scheduled_time=datetime.combine(today, time(hour=10, minute=0)),
		is_completed=True,
	)
	cat_task = Task(
		description="Cat feeding",
		scheduled_time=datetime.combine(today, time(hour=11, minute=0)),
	)

	dog.add_task(dog_task)
	dog.add_task(completed_task)
	cat.add_task(cat_task)
	owner.add_pet(dog)
	owner.add_pet(cat)

	scheduler = Scheduler(owner)
	filtered = scheduler.filter_tasks(pet_name="Mochi", status="pending", for_date=today)

	assert [task.description for task in filtered] == ["Dog walk"]


def test_filter_by_status_or_pet_handles_completed_and_pet_name() -> None:
	owner = Owner(name="Jordan", available_minutes=120)
	dog = Pet(name="Mochi", species="dog", age=4)
	cat = Pet(name="Luna", species="cat", age=2)
	today = date.today()

	dog.add_task(Task(description="Dog pending", scheduled_time=datetime.combine(today, time(hour=9, minute=0))))
	dog.add_task(
		Task(
			description="Dog done",
			scheduled_time=datetime.combine(today, time(hour=10, minute=0)),
			is_completed=True,
		)
	)
	cat.add_task(Task(description="Cat pending", scheduled_time=datetime.combine(today, time(hour=11, minute=0))))

	owner.add_pet(dog)
	owner.add_pet(cat)
	scheduler = Scheduler(owner)

	completed = scheduler.filter_by_status_or_pet(status="completed", for_date=today)
	mochi_pending = scheduler.filter_by_status_or_pet(status="pending", pet_name="Mochi", for_date=today)

	assert [task.description for task in completed] == ["Dog done"]
	assert [task.description for task in mochi_pending] == ["Dog pending"]


def test_generate_schedule_includes_recurring_tasks_on_matching_date() -> None:
	owner = Owner(name="Jordan", available_minutes=120)
	pet = Pet(name="Mochi", species="dog", age=4)
	today = date.today()
	past_day = today - timedelta(days=3)

	pet.add_task(
		Task(
			description="Daily meds",
			scheduled_time=datetime.combine(past_day, time(hour=7, minute=30)),
			frequency="daily",
		)
	)
	pet.add_task(
		Task(
			description="Weekly training",
			scheduled_time=datetime.combine(today - timedelta(days=7), time(hour=17, minute=0)),
			frequency="weekly",
		)
	)
	owner.add_pet(pet)

	tasks = Scheduler(owner).generate_schedule(for_date=today)
	descriptions = [task.description for task in tasks]

	assert "Daily meds" in descriptions
	assert "Weekly training" in descriptions


def test_detect_conflicts_for_specific_date() -> None:
	owner = Owner(name="Jordan", available_minutes=180)
	pet = Pet(name="Mochi", species="dog", age=4)
	today = date.today()

	pet.add_task(
		Task(
			description="Morning walk",
			scheduled_time=datetime.combine(today, time(hour=8, minute=0)),
			duration_minutes=30,
		)
	)
	pet.add_task(
		Task(
			description="Medication",
			scheduled_time=datetime.combine(today, time(hour=8, minute=20)),
			duration_minutes=10,
		)
	)
	pet.add_task(
		Task(
			description="Play time",
			scheduled_time=datetime.combine(today, time(hour=9, minute=0)),
			duration_minutes=20,
		)
	)
	owner.add_pet(pet)

	scheduler = Scheduler(owner)
	conflicts = scheduler.detect_conflicts(for_date=today)

	assert len(conflicts) == 1
	assert conflicts[0][0].description == "Morning walk"
	assert conflicts[0][1].description == "Medication"


def test_mark_task_complete_daily_spawns_next_day_task() -> None:
	owner = Owner(name="Jordan", available_minutes=120)
	pet = Pet(name="Mochi", species="dog", age=4)
	today = date.today()
	start_time = datetime.combine(today, time(hour=8, minute=0))

	pet.add_task(
		Task(
			description="Daily meds",
			scheduled_time=start_time,
			frequency="daily",
			duration_minutes=15,
			priority=2,
		)
	)
	owner.add_pet(pet)

	scheduler = Scheduler(owner)
	updated = scheduler.mark_task_complete("Mochi", "Daily meds", completed_at=start_time)

	assert updated is True
	tasks = pet.get_tasks(include_completed=True)
	assert len(tasks) == 2
	assert tasks[0].is_completed is True
	assert tasks[1].is_completed is False
	assert tasks[1].scheduled_time == start_time + timedelta(days=1)


def test_mark_task_complete_weekly_spawns_next_week_task() -> None:
	owner = Owner(name="Jordan", available_minutes=120)
	pet = Pet(name="Mochi", species="dog", age=4)
	today = date.today()
	start_time = datetime.combine(today, time(hour=17, minute=30))

	pet.add_task(
		Task(
			description="Weekly training",
			scheduled_time=start_time,
			frequency="weekly",
			duration_minutes=30,
			priority=3,
		)
	)
	owner.add_pet(pet)

	scheduler = Scheduler(owner)
	updated = scheduler.mark_task_complete("Mochi", "Weekly training", completed_at=start_time)

	assert updated is True
	tasks = pet.get_tasks(include_completed=True)
	assert len(tasks) == 2
	assert tasks[1].scheduled_time == start_time + timedelta(days=7)


def test_mark_task_complete_once_does_not_spawn_new_task() -> None:
	owner = Owner(name="Jordan", available_minutes=120)
	pet = Pet(name="Mochi", species="dog", age=4)
	today = date.today()

	pet.add_task(
		Task(
			description="Vet visit",
			scheduled_time=datetime.combine(today, time(hour=11, minute=0)),
			frequency="once",
		)
	)
	owner.add_pet(pet)

	scheduler = Scheduler(owner)
	updated = scheduler.mark_task_complete("Mochi", "Vet visit")

	assert updated is True
	assert len(pet.get_tasks(include_completed=True)) == 1
	assert pet.get_tasks(include_completed=True)[0].is_completed is True


def test_mark_task_complete_overdue_daily_uses_completion_date() -> None:
	owner = Owner(name="Jordan", available_minutes=120)
	pet = Pet(name="Mochi", species="dog", age=4)
	today = date.today()
	overdue_time = datetime.combine(today - timedelta(days=3), time(hour=7, minute=0))
	completed_at = datetime.combine(today, time(hour=9, minute=0))

	pet.add_task(
		Task(
			description="Daily check-in",
			scheduled_time=overdue_time,
			frequency="daily",
		)
	)
	owner.add_pet(pet)

	scheduler = Scheduler(owner)
	updated = scheduler.mark_task_complete("Mochi", "Daily check-in", completed_at=completed_at)

	assert updated is True
	new_task = pet.get_tasks(include_completed=True)[1]
	assert new_task.scheduled_time == datetime.combine(today + timedelta(days=1), time(hour=7, minute=0))


def test_detect_conflicts_same_time_same_pet() -> None:
	"""Detect conflicts when same pet has two tasks at same time."""
	owner = Owner(name="Jordan", available_minutes=180)
	pet = Pet(name="Mochi", species="dog", age=4)
	today = date.today()

	pet.add_task(
		Task(
			description="Morning walk",
			scheduled_time=datetime.combine(today, time(hour=8, minute=0)),
			duration_minutes=30,
		)
	)
	pet.add_task(
		Task(
			description="Morning play",
			scheduled_time=datetime.combine(today, time(hour=8, minute=0)),
			duration_minutes=25,
		)
	)
	owner.add_pet(pet)

	scheduler = Scheduler(owner)
	conflicts = scheduler.detect_conflicts(for_date=today)

	assert len(conflicts) == 1
	assert conflicts[0][0].description in {"Morning walk", "Morning play"}
	assert conflicts[0][1].description in {"Morning walk", "Morning play"}


def test_detect_conflicts_same_time_different_pets() -> None:
	"""Detect conflicts when different pets have tasks at same time."""
	owner = Owner(name="Jordan", available_minutes=180)
	dog = Pet(name="Mochi", species="dog", age=4)
	cat = Pet(name="Luna", species="cat", age=2)
	today = date.today()

	dog.add_task(
		Task(
			description="Dog breakfast",
			scheduled_time=datetime.combine(today, time(hour=8, minute=0)),
			duration_minutes=20,
		)
	)
	cat.add_task(
		Task(
			description="Cat feeding",
			scheduled_time=datetime.combine(today, time(hour=8, minute=0)),
			duration_minutes=15,
		)
	)
	owner.add_pet(dog)
	owner.add_pet(cat)

	scheduler = Scheduler(owner)
	conflicts = scheduler.detect_conflicts(for_date=today)

	assert len(conflicts) == 1
	assert {"Dog breakfast", "Cat feeding"} == {conflicts[0][0].description, conflicts[0][1].description}
