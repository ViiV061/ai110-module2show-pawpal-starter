from pawpal_system import Pet, Task


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
