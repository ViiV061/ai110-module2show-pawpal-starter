from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from typing import List, Optional, Tuple


class Owner:
	def __init__(self, name: str, available_minutes: int) -> None:
		"""Initialize an owner with a name, daily available time, and no pets."""
		self.name = name
		self.available_minutes = available_minutes
		self._pets: List[Pet] = []

	def add_pet(self, pet: Pet) -> None:
		"""Add a pet to the owner's pet list."""
		self._pets.append(pet)

	def get_pets(self) -> List[Pet]:
		"""Return the list of pets owned by this owner."""
		return list(self._pets)

	def get_all_tasks(self, include_completed: bool = True) -> List[Task]:
		"""Collect tasks across all pets owned by this owner."""
		all_tasks: List[Task] = []
		for pet in self._pets:
			all_tasks.extend(pet.get_tasks(include_completed=include_completed))
		return all_tasks


@dataclass
class Task:
	description: str
	scheduled_time: Optional[datetime] = None
	frequency: str = "once"
	is_completed: bool = False
	duration_minutes: int = 30
	priority: int = 3

	def mark_completed(self) -> None:
		"""Set this task's completion status to completed."""
		self.is_completed = True

	def mark_incomplete(self) -> None:
		"""Set this task's completion status to not completed."""
		self.is_completed = False

	def is_conflicting(self, other: Task) -> bool:
		"""Return True if this task overlaps in time with another task."""
		if self.scheduled_time is None or other.scheduled_time is None:
			return False

		self_end = self.scheduled_time + timedelta(minutes=self.duration_minutes)
		other_end = other.scheduled_time + timedelta(minutes=other.duration_minutes)
		return self.scheduled_time < other_end and other.scheduled_time < self_end


@dataclass
class Pet:
	name: str
	species: str
	age: int
	_tasks: List[Task] = field(default_factory=list)

	def add_task(self, task: Task) -> None:
		"""Add a task to the pet's task list."""
		self._tasks.append(task)

	def get_tasks(self, include_completed: bool = True) -> List[Task]:
		"""Return the list of tasks assigned to this pet."""
		if include_completed:
			return list(self._tasks)
		return [task for task in self._tasks if not task.is_completed]

	def get_tasks_for_date(self, target_date: date, include_completed: bool = True) -> List[Task]:
		"""Return tasks due on the given date."""
		selected = self.get_tasks(include_completed=include_completed)
		return [
			task
			for task in selected
			if task.scheduled_time is not None and task.scheduled_time.date() == target_date
		]

	def complete_task(self, description: str) -> bool:
		"""Mark the first task matching description as completed."""
		for task in self._tasks:
			if task.description == description and not task.is_completed:
				task.mark_completed()
				return True
		return False


class Scheduler:
	def __init__(self, owner: Owner) -> None:
		"""Initialize scheduler with an Owner to manage all their pets' tasks."""
		self._owner = owner
		self._tasks: List[Task] = []

	def _task_applies_to_date(self, task: Task, target_date: date) -> bool:
		"""Return True if a task should be considered for the target date."""
		if task.scheduled_time is not None and task.scheduled_time.date() == target_date:
			return True

		if task.frequency == "daily":
			return True

		if task.frequency == "weekly" and task.scheduled_time is not None:
			return task.scheduled_time.weekday() == target_date.weekday()

		return False

	def sort_tasks(self) -> List[Task]:
		"""Sort incomplete tasks by schedule time and then by priority."""
		tasks = self._owner.get_all_tasks(include_completed=False)
		sorted_tasks = sorted(
			tasks,
			key=lambda task: (
				task.scheduled_time is None,
				task.scheduled_time or datetime.max,
				-task.priority,
			),
		)
		self._tasks = sorted_tasks
		return sorted_tasks

	def detect_conflicts(self) -> List[Tuple[Task, Task]]:
		"""Detect overlapping scheduled tasks and return conflicting pairs."""
		conflicts: List[Tuple[Task, Task]] = []
		scheduled_tasks = [task for task in self.sort_tasks() if task.scheduled_time is not None]

		for i, current in enumerate(scheduled_tasks):
			for nxt in scheduled_tasks[i + 1 :]:
				if current.is_conflicting(nxt):
					conflicts.append((current, nxt))
				elif current.scheduled_time is not None and nxt.scheduled_time is not None:
					current_end = current.scheduled_time + timedelta(minutes=current.duration_minutes)
					if nxt.scheduled_time >= current_end:
						break

		return conflicts

	def schedule_walk(
		self,
		pet: Pet,
		when: datetime,
		duration_minutes: int = 30,
		priority: int = 3,
		frequency: str = "once",
	) -> Task:
		"""Create and attach a walk task for the provided pet."""
		walk_task = Task(
			description=f"Walk {pet.name}",
			scheduled_time=when,
			frequency=frequency,
			is_completed=False,
			duration_minutes=duration_minutes,
			priority=priority,
		)
		pet.add_task(walk_task)
		return walk_task

	def get_todays_tasks(self) -> List[Task]:
		"""Return tasks selected for today's schedule."""
		return self.generate_schedule(for_date=date.today())

	def generate_schedule(self, for_date: Optional[date] = None) -> List[Task]:
		"""Build a daily schedule constrained by owner available minutes."""
		target_date = for_date or date.today()
		ordered = self.sort_tasks()

		selected: List[Task] = []
		used_minutes = 0
		for task in ordered:
			if task.is_completed:
				continue
			if not self._task_applies_to_date(task, target_date):
				continue

			if used_minutes + task.duration_minutes <= self._owner.available_minutes:
				selected.append(task)
				used_minutes += task.duration_minutes

		self._tasks = selected
		return selected
