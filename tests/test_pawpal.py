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


# ============================================================================
# EDGE CASE TESTS: CONFLICT DETECTION BOUNDARIES
# ============================================================================


def test_detect_conflicts_adjacent_tasks_no_overlap() -> None:
	"""Tasks that end exactly when another starts should NOT conflict."""
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
			description="Training session",
			scheduled_time=datetime.combine(today, time(hour=8, minute=30)),
			duration_minutes=20,
		)
	)
	owner.add_pet(pet)

	scheduler = Scheduler(owner)
	conflicts = scheduler.detect_conflicts(for_date=today)

	assert len(conflicts) == 0


def test_detect_conflicts_partial_overlap() -> None:
	"""Tasks with partial time overlap SHOULD conflict."""
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
			description="Training session",
			scheduled_time=datetime.combine(today, time(hour=8, minute=20)),
			duration_minutes=20,
		)
	)
	owner.add_pet(pet)

	scheduler = Scheduler(owner)
	conflicts = scheduler.detect_conflicts(for_date=today)

	assert len(conflicts) == 1


def test_detect_conflicts_no_conflict_without_scheduled_time() -> None:
	"""Tasks without scheduled_time should not be flagged as conflicts."""
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
			description="Unscheduled task",
			scheduled_time=None,
			duration_minutes=20,
		)
	)
	owner.add_pet(pet)

	scheduler = Scheduler(owner)
	conflicts = scheduler.detect_conflicts(for_date=today)

	assert len(conflicts) == 0


# ============================================================================
# EDGE CASE TESTS: RECURRING TASK DUPLICATE PREVENTION
# ============================================================================


def test_duplicate_recurring_task_prevention() -> None:
	"""When next occurrence already exists, don't spawn duplicate."""
	owner = Owner(name="Jordan", available_minutes=120)
	pet = Pet(name="Mochi", species="dog", age=4)
	today = date.today()
	tomorrow = today + timedelta(days=1)
	start_time = datetime.combine(today, time(hour=8, minute=0))
	next_time = datetime.combine(tomorrow, time(hour=8, minute=0))

	pet.add_task(
		Task(
			description="Daily meds",
			scheduled_time=start_time,
			frequency="daily",
			duration_minutes=15,
			priority=2,
		)
	)
	# Manually add the next occurrence
	pet.add_task(
		Task(
			description="Daily meds",
			scheduled_time=next_time,
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
	# Should still be 2 (not 3), reusing existing task
	assert len(tasks) == 2
	assert tasks[1].is_completed is False


def test_spawn_next_task_when_different_time_exists() -> None:
	"""When task with same description but different time exists, spawn new one."""
	owner = Owner(name="Jordan", available_minutes=120)
	pet = Pet(name="Mochi", species="dog", age=4)
	today = date.today()
	tomorrow = today + timedelta(days=1)
	start_time = datetime.combine(today, time(hour=8, minute=0))
	different_time = datetime.combine(tomorrow, time(hour=10, minute=0))  # Different time

	pet.add_task(
		Task(
			description="Daily meds",
			scheduled_time=start_time,
			frequency="daily",
			duration_minutes=15,
		)
	)
	# Add task with same description but different time
	pet.add_task(
		Task(
			description="Daily meds",
			scheduled_time=different_time,
			frequency="daily",
			duration_minutes=15,
		)
	)
	owner.add_pet(pet)

	scheduler = Scheduler(owner)
	updated = scheduler.mark_task_complete("Mochi", "Daily meds", completed_at=start_time)

	assert updated is True
	tasks = pet.get_tasks(include_completed=True)
	# Should spawn new task at 8:00 tomorrow (not match the 10:00 task)
	assert len(tasks) == 3


# ============================================================================
# EDGE CASE TESTS: RECURRING TASK FREQUENCY VALIDATION
# ============================================================================


def test_mark_complete_invalid_frequency_no_spawn() -> None:
	"""Tasks with invalid frequency should not spawn next occurrence."""
	owner = Owner(name="Jordan", available_minutes=120)
	pet = Pet(name="Mochi", species="dog", age=4)
	today = date.today()

	pet.add_task(
		Task(
			description="Task with invalid frequency",
			scheduled_time=datetime.combine(today, time(hour=8, minute=0)),
			frequency="monthly",  # Invalid frequency
			duration_minutes=15,
		)
	)
	owner.add_pet(pet)

	scheduler = Scheduler(owner)
	updated = scheduler.mark_task_complete("Mochi", "Task with invalid frequency")

	assert updated is True
	tasks = pet.get_tasks(include_completed=True)
	# Should stay 1 (no spawn for invalid frequency)
	assert len(tasks) == 1
	assert tasks[0].is_completed is True


def test_mark_complete_empty_frequency_no_spawn() -> None:
	"""Tasks with empty frequency string should not spawn next occurrence."""
	owner = Owner(name="Jordan", available_minutes=120)
	pet = Pet(name="Mochi", species="dog", age=4)
	today = date.today()

	pet.add_task(
		Task(
			description="Task with empty frequency",
			scheduled_time=datetime.combine(today, time(hour=8, minute=0)),
			frequency="",  # Empty frequency
			duration_minutes=15,
		)
	)
	owner.add_pet(pet)

	scheduler = Scheduler(owner)
	updated = scheduler.mark_task_complete("Mochi", "Task with empty frequency")

	assert updated is True
	tasks = pet.get_tasks(include_completed=True)
	assert len(tasks) == 1


# ============================================================================
# EDGE CASE TESTS: SORTING STABILITY WITH TIED VALUES
# ============================================================================


def test_sort_tasks_stable_with_identical_time_and_priority() -> None:
	"""Tasks with identical time and priority should maintain insertion order."""
	owner = Owner(name="Jordan", available_minutes=120)
	pet = Pet(name="Mochi", species="dog", age=4)
	today = date.today()
	same_time = datetime.combine(today, time(hour=9, minute=0))

	# Add tasks in specific order
	pet.add_task(Task(description="Task A", scheduled_time=same_time, priority=3))
	pet.add_task(Task(description="Task B", scheduled_time=same_time, priority=3))
	pet.add_task(Task(description="Task C", scheduled_time=same_time, priority=3))
	owner.add_pet(pet)

	sorted_tasks = Scheduler(owner).sort_tasks(for_date=today)
	descriptions = [task.description for task in sorted_tasks]

	# Should maintain insertion order for identical time/priority
	assert descriptions == ["Task A", "Task B", "Task C"]


def test_sort_tasks_with_zero_duration() -> None:
	"""Tasks with zero duration should still sort correctly."""
	owner = Owner(name="Jordan", available_minutes=120)
	pet = Pet(name="Mochi", species="dog", age=4)
	today = date.today()

	pet.add_task(
		Task(
			description="Zero duration task",
			scheduled_time=datetime.combine(today, time(hour=8, minute=30)),
			duration_minutes=0,
			priority=1,
		)
	)
	pet.add_task(
		Task(
			description="Normal task",
			scheduled_time=datetime.combine(today, time(hour=8, minute=30)),
			duration_minutes=30,
			priority=2,
		)
	)
	owner.add_pet(pet)

	sorted_tasks = Scheduler(owner).sort_tasks(for_date=today)
	# Should sort by priority (2 > 1)
	assert sorted_tasks[0].description == "Normal task"
	assert sorted_tasks[1].description == "Zero duration task"


# ============================================================================
# EDGE CASE TESTS: WEEKLY TASK WEEK BOUNDARIES
# ============================================================================


def test_weekly_task_preserves_day_of_week_across_month_boundary() -> None:
	"""Weekly task should preserve day-of-week when spawned across month boundary."""
	owner = Owner(name="Jordan", available_minutes=120)
	pet = Pet(name="Mochi", species="dog", age=4)

	# Use a known date: March 31, 2026 is a Monday
	start_date = date(2026, 3, 30)  # Monday of week
	start_time = datetime.combine(start_date, time(hour=10, minute=0))

	pet.add_task(
		Task(
			description="Weekly Monday training",
			scheduled_time=start_time,
			frequency="weekly",
			duration_minutes=30,
		)
	)
	owner.add_pet(pet)

	scheduler = Scheduler(owner)
	updated = scheduler.mark_task_complete("Mochi", "Weekly Monday training", completed_at=start_time)

	assert updated is True
	tasks = pet.get_tasks(include_completed=True)
	next_task = tasks[1]

	# Next occurrence should be 7 days later (still Monday, next month)
	assert next_task.scheduled_time.date() == start_date + timedelta(days=7)
	assert next_task.scheduled_time.weekday() == start_date.weekday()  # Both Monday


# ============================================================================
# EDGE CASE TESTS: MULTIPLE CONSECUTIVE COMPLETIONS
# ============================================================================


def test_multiple_consecutive_daily_task_completions() -> None:
	"""Completing same daily task multiple times should spawn multiple instances."""
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
		)
	)
	owner.add_pet(pet)

	scheduler = Scheduler(owner)

	# Complete first day
	updated1 = scheduler.mark_task_complete("Mochi", "Daily meds", completed_at=start_time)
	assert updated1 is True
	assert len(pet.get_tasks(include_completed=True)) == 2

	# Complete second day (tomorrow's task)
	tomorrow_time = start_time + timedelta(days=1)
	updated2 = scheduler.mark_task_complete(
		"Mochi", "Daily meds", completed_at=tomorrow_time
	)
	assert updated2 is True
	assert len(pet.get_tasks(include_completed=True)) == 3

	# Verify dates are sequential
	tasks = pet.get_tasks(include_completed=True)
	assert tasks[0].scheduled_time.date() == today
	assert tasks[1].scheduled_time.date() == today + timedelta(days=1)
	assert tasks[2].scheduled_time.date() == today + timedelta(days=2)


# ============================================================================
# EDGE CASE TESTS: CONFLICT DETECTION WITH MULTI-PET SCHEDULING
# ============================================================================


def test_detect_conflicts_three_tasks_one_pair_overlap() -> None:
	"""With 3 tasks, should detect only the overlapping pair."""
	owner = Owner(name="Jordan", available_minutes=180)
	pet = Pet(name="Mochi", species="dog", age=4)
	today = date.today()

	pet.add_task(
		Task(
			description="Task 1",
			scheduled_time=datetime.combine(today, time(hour=8, minute=0)),
			duration_minutes=30,
		)
	)
	pet.add_task(
		Task(
			description="Task 2 (conflicts with Task 1)",
			scheduled_time=datetime.combine(today, time(hour=8, minute=20)),
			duration_minutes=10,
		)
	)
	pet.add_task(
		Task(
			description="Task 3 (no conflict)",
			scheduled_time=datetime.combine(today, time(hour=9, minute=0)),
			duration_minutes=20,
		)
	)
	owner.add_pet(pet)

	scheduler = Scheduler(owner)
	conflicts = scheduler.detect_conflicts(for_date=today)

	assert len(conflicts) == 1
	conflict_pair = {conflicts[0][0].description, conflicts[0][1].description}
	assert conflict_pair == {"Task 1", "Task 2 (conflicts with Task 1)"}


def test_detect_conflicts_multiple_pairs_same_date() -> None:
	"""Should detect multiple conflict pairs on same date."""
	owner = Owner(name="Jordan", available_minutes=180)
	dog = Pet(name="Mochi", species="dog", age=4)
	cat = Pet(name="Luna", species="cat", age=2)
	today = date.today()

	# Morning conflict pair
	dog.add_task(
		Task(
			description="Dog breakfast",
			scheduled_time=datetime.combine(today, time(hour=8, minute=0)),
			duration_minutes=20,
		)
	)
	cat.add_task(
		Task(
			description="Cat breakfast",
			scheduled_time=datetime.combine(today, time(hour=8, minute=0)),
			duration_minutes=20,
		)
	)

	# Evening conflict pair
	dog.add_task(
		Task(
			description="Dog dinner",
			scheduled_time=datetime.combine(today, time(hour=18, minute=0)),
			duration_minutes=20,
		)
	)
	cat.add_task(
		Task(
			description="Cat dinner",
			scheduled_time=datetime.combine(today, time(hour=18, minute=0)),
			duration_minutes=20,
		)
	)

	owner.add_pet(dog)
	owner.add_pet(cat)

	scheduler = Scheduler(owner)
	conflicts = scheduler.detect_conflicts(for_date=today)

	assert len(conflicts) == 2


# ============================================================================
# EDGE CASE TESTS: FILTERING EDGE CASES
# ============================================================================


def test_filter_tasks_nonexistent_pet_returns_empty() -> None:
	"""Filtering by non-existent pet name should return empty list."""
	owner = Owner(name="Jordan", available_minutes=120)
	dog = Pet(name="Mochi", species="dog", age=4)
	today = date.today()

	dog.add_task(
		Task(
			description="Dog walk",
			scheduled_time=datetime.combine(today, time(hour=8, minute=0)),
		)
	)
	owner.add_pet(dog)

	scheduler = Scheduler(owner)
	filtered = scheduler.filter_tasks(pet_name="NonexistentPet", for_date=today)

	assert len(filtered) == 0


def test_filter_tasks_future_date_with_recurring() -> None:
	"""Recurring task should apply to future dates."""
	owner = Owner(name="Jordan", available_minutes=120)
	pet = Pet(name="Mochi", species="dog", age=4)
	today = date.today()
	future_date = today + timedelta(days=30)

	pet.add_task(
		Task(
			description="Daily meds",
			scheduled_time=datetime.combine(today, time(hour=7, minute=30)),
			frequency="daily",
		)
	)
	owner.add_pet(pet)

	scheduler = Scheduler(owner)
	filtered = scheduler.filter_tasks(pet_name="Mochi", status="pending", for_date=future_date)

	assert len(filtered) == 1
	assert filtered[0].description == "Daily meds"


# ============================================================================
# EDGE CASE TESTS: TASK PROPERTIES EDGE CASES
# ============================================================================


def test_task_with_max_priority_value() -> None:
	"""Tasks with different priority values should sort correctly."""
	owner = Owner(name="Jordan", available_minutes=120)
	pet = Pet(name="Mochi", species="dog", age=4)
	today = date.today()
	same_time = datetime.combine(today, time(hour=9, minute=0))

	pet.add_task(Task(description="Low priority", scheduled_time=same_time, priority=1))
	pet.add_task(Task(description="High priority", scheduled_time=same_time, priority=5))
	pet.add_task(Task(description="Medium priority", scheduled_time=same_time, priority=3))
	owner.add_pet(pet)

	sorted_tasks = Scheduler(owner).sort_tasks(for_date=today)
	descriptions = [task.description for task in sorted_tasks]

	# Should sort by priority descending
	assert descriptions == ["High priority", "Medium priority", "Low priority"]


def test_recurring_task_preserves_all_properties() -> None:
	"""Spawned recurring task should preserve description, frequency, duration, priority."""
	owner = Owner(name="Jordan", available_minutes=120)
	pet = Pet(name="Mochi", species="dog", age=4)
	today = date.today()
	start_time = datetime.combine(today, time(hour=8, minute=0))

	pet.add_task(
		Task(
			description="Morning routine",
			scheduled_time=start_time,
			frequency="daily",
			duration_minutes=45,
			priority=3,
		)
	)
	owner.add_pet(pet)

	scheduler = Scheduler(owner)
	scheduler.mark_task_complete("Mochi", "Morning routine", completed_at=start_time)

	next_task = pet.get_tasks(include_completed=True)[1]
	assert next_task.description == "Morning routine"
	assert next_task.frequency == "daily"
	assert next_task.duration_minutes == 45
	assert next_task.priority == 3
	assert next_task.is_completed is False
