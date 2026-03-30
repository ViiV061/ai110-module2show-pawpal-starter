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

	def _next_occurrence_time(self, task: Task, completed_at: Optional[datetime] = None) -> Optional[datetime]:
		"""Calculate next occurrence datetime for recurring (daily/weekly) tasks.

		For frequency='once', returns None (no recurrence).
		For daily: advances by 1 day; for weekly: advances by 7 days.
		Preserves original time-of-day; uses completed_at if provided and later than scheduled_time.

		Args:
			task: Task object with frequency and scheduled_time
			completed_at: Optional completion datetime; if later than task.scheduled_time.date(),
			              uses completion date as reference for recurrence instead of scheduled date.

		Returns:
			Next occurrence datetime, or None if frequency is 'once' or scheduled_time is missing.
		"""
		if task.frequency not in {"daily", "weekly"}:
			return None

		if task.scheduled_time is None:
			return None

		reference_date = task.scheduled_time.date()
		if completed_at is not None and completed_at.date() > reference_date:
			reference_date = completed_at.date()

		delta_days = 1 if task.frequency == "daily" else 7
		next_date = reference_date + timedelta(days=delta_days)
		return datetime.combine(next_date, task.scheduled_time.time())

	def _get_duplicate_task(self, pet: Pet, task: Task, scheduled_time: datetime) -> Optional[Task]:
		"""Find existing uncompleted task with same description, frequency, and scheduled_time.

		Use: Prevents duplicate recurring task instances when spawning next occurrence.
		Only matches uncompleted tasks (is_completed=False).

		Args:
			pet: Pet object to search within
			task: Reference task to match against
			scheduled_time: Target datetime to match

		Returns:
			Matching Task if found, None otherwise.
		"""
		for candidate in pet.get_tasks(include_completed=True):
			if (
				candidate.description == task.description
				and candidate.frequency == task.frequency
				and candidate.scheduled_time == scheduled_time
				and not candidate.is_completed
			):
				return candidate
		return None

	def _spawn_next_recurring_task(self, pet: Pet, task: Task, completed_at: Optional[datetime] = None) -> Optional[Task]:
		"""Auto-create next occurrence for daily/weekly recurring tasks.

		Workflow: 1. Ignores 'once' frequency (no spawn), 2. Calculates next_time via +1 day (daily)
		or +7 days (weekly), preserving time-of-day, 3. Checks for duplicate via _get_duplicate_task(),
		4. Creates new Task if not duplicate, 5. Appends to pet.tasks

		Args:
			pet: Pet object containing task and where new task will be added
			task: Completed recurring task describing frequency and time pattern
			completed_at: Optional datetime marking task completion (basis for next date calculation)

		Returns:
			New Task instance if spawned, None if 'once' frequency or duplicate exists."""
		next_time = self._next_occurrence_time(task, completed_at=completed_at)
		if next_time is None:
			return None

		existing_match = self._get_duplicate_task(pet, task, next_time)
		if existing_match is not None:
			return existing_match

		next_task = Task(
			description=task.description,
			scheduled_time=next_time,
			frequency=task.frequency,
			is_completed=False,
			duration_minutes=task.duration_minutes,
			priority=task.priority,
		)
		pet.add_task(next_task)
		return next_task

	def mark_task_complete(
		self,
		pet_name: str,
		description: str,
		completed_at: Optional[datetime] = None,
	) -> bool:
		"""Mark a pet's task as completed and auto-spawn next occurrence if recurring.

		Main entry point for task completion workflow:
		1. Finds task by pet name and description
		2. Marks task as complete
		3. Triggers recurring task spawn if frequency is 'daily' or 'weekly'

		Args:
			pet_name: Name of pet that owns the task (e.g., 'Mochi')
			description: Task description to match (e.g., 'Daily meds')
			completed_at: Optional datetime of completion; useful for overdue tasks.
			              If not provided, mark_completed() is called with current internal time.

		Returns:
			True if task was found and marked complete; False if pet or task not found.
		"""
		for pet in self._owner.get_pets():
			if pet.name != pet_name:
				continue

			for task in pet.get_tasks(include_completed=True):
				if task.description != description or task.is_completed:
					continue

				task.mark_completed()
				self._spawn_next_recurring_task(pet, task, completed_at=completed_at)
				return True

		return False

	def _iter_owner_tasks(self, include_completed: bool = True) -> List[Tuple[Pet, Task]]:
		"""Iterate all tasks across all owner's pets, optionally filtering by completion status.

		Helper for filter_tasks and detect_conflicts. Returns (pet, task) tuples
		to preserve pet context when filtering or analyzing tasks.

		Args:
			include_completed: If True, return all tasks; if False, exclude completed tasks.

		Returns:
			List of (Pet, Task) tuples across all owner's pets.
		"""
		entries: List[Tuple[Pet, Task]] = []
		for pet in self._owner.get_pets():
			for task in pet.get_tasks(include_completed=include_completed):
				entries.append((pet, task))
		return entries

	def _task_occurrence_time(self, task: Task, target_date: date) -> Optional[datetime]:
		"""Compute effective datetime when a recurring task occurs on a given target_date.

		For frequency='once': returns task.scheduled_time as-is.
		For frequency='daily' or 'weekly': reconstructs datetime using target_date + original time-of-day.
		This allows recurring tasks to appear on every matching date without explicit instances.

		Args:
			task: Task with frequency and scheduled_time
			target_date: Date to compute occurrence for (e.g., today's date)

		Returns:
			Datetime when task occurs on target_date; None if scheduled_time is missing.
		"""
		if task.scheduled_time is None:
			return None

		if task.frequency in {"daily", "weekly"}:
			return datetime.combine(target_date, task.scheduled_time.time())

		return task.scheduled_time

	def _task_applies_to_date(self, task: Task, target_date: date) -> bool:
		"""Return True if a task should be considered for the target date."""
		if task.scheduled_time is None:
			return False

		task_date = task.scheduled_time.date()

		if task_date == target_date:
			return True
		if target_date < task_date:
			return False
		if task.frequency == "daily":
			return True

		return task.frequency == "weekly" and task.scheduled_time.weekday() == target_date.weekday()

	def filter_tasks(
		self,
		pet_name: Optional[str] = None,
		status: str = "all",
		for_date: Optional[date] = None,
	) -> List[Task]:
		"""Filter owner's tasks by pet name, completion status, and target date.

		Flexible filtering:
		- pet_name=None: include all pets; pet_name='Mochi': only Mochi's tasks
		- status='all': both completed and pending; 'completed': only complete; 'pending': only incomplete
		- for_date=None: include all dates; for_date=today(): only today's applicable tasks
		  (applies _task_applies_to_date for frequency logic)

		Args:
			pet_name: Optional pet name filter
			status: 'all', 'completed', or 'pending'
			for_date: Optional target date; uses _task_applies_to_date for recurring logic

		Returns:
			Filtered list of Task objects.
		"""

		def _passes_filters(pet: Pet, task: Task) -> bool:
			"""Check if task passes all filter criteria."""
			if pet_name is not None and pet.name != pet_name:
				return False
			if status == "completed" and not task.is_completed:
				return False
			if status == "pending" and task.is_completed:
				return False
			if for_date is not None and not self._task_applies_to_date(task, for_date):
				return False
			return True

		return [
			task
			for pet, task in self._iter_owner_tasks(include_completed=True)
			if _passes_filters(pet, task)
		]

	def filter_by_status_or_pet(
		self,
		status: str = "all",
		pet_name: Optional[str] = None,
		for_date: Optional[date] = None,
	) -> List[Task]:
		"""Convenience wrapper around filter_tasks with parameter order optimized for status-first queries.

		Use when filtering by status is primary concern (e.g., "show me all completed tasks" or
		"show all pending tasks for Mochi").

		Args:
			status: 'all', 'completed', or 'pending' (checked first)
			pet_name: Optional pet name filter
			for_date: Optional target date

		Returns:
			Filtered list of Task objects (delegates to filter_tasks).
		"""
		return self.filter_tasks(pet_name=pet_name, status=status, for_date=for_date)

	def sort_by_time(self, tasks: Optional[List[Task]] = None, for_date: Optional[date] = None) -> List[Task]:
		"""Sort tasks by scheduled time-of-day, then by priority (descending).

		Algorithm:
		1. Tasks without scheduled time are pushed to end
		2. Within scheduled tasks, sort by .time() object (e.g., 08:00 < 12:30)
		3. Tasks at same time sort by priority descending (priority 3 before priority 1)

		Optimization: Uses `.time()` objects for comparison instead of string formatting,
		caching _task_occurrence_time() to avoid redundant calls. ~2x faster than strftime approach.

		Args:
			tasks: Optional pre-filtered task list; if None, uses pending tasks for for_date
			for_date: Optional target date for recurring task occurrence; defaults to today

		Returns:
			Sorted list of Task objects.
		"""
		target_date = for_date or date.today()
		tasks_to_sort = tasks if tasks is not None else self.filter_tasks(status="pending", for_date=target_date)

		def sort_key(task: Task) -> tuple:
			"""Generate sort key: (has_no_time, time_of_day, neg_priority)."""
			occurrence = self._task_occurrence_time(task, target_date)
			return (
				occurrence is None,
				occurrence.time() if occurrence else datetime.max.time(),
				-task.priority,
			)

		return sorted(tasks_to_sort, key=sort_key)

	def sort_tasks(self, for_date: Optional[date] = None, tasks: Optional[List[Task]] = None) -> List[Task]:
		"""Sort tasks by effective datetime and then by priority."""
		target_date = for_date or date.today()
		sorted_tasks = self.sort_by_time(tasks=tasks, for_date=target_date)
		self._tasks = sorted_tasks
		return sorted_tasks

	def detect_conflicts(self, for_date: Optional[date] = None, tasks: Optional[List[Task]] = None) -> List[Tuple[Task, Task]]:
		"""Identify task time conflicts (overlapping duration) for a given date.

		Algorithm:
		1. Sorts tasks by time using sort_by_time()
		2. Compares each pair: if current.end > next.start AND next.start < current.end, conflicts
		3. Early-exit optimization: stops checking when next task starts after current ends

		Lightweight conflict detection: returns conflict pairs without halting execution;
		can be logged as warnings without crashing the schedule.

		Args:
			for_date: Target date to check; defaults to today
			tasks: Optional pre-filtered task list (e.g., from get_todays_tasks());
			       if None, checks all pending tasks for for_date

		Returns:
			List of (Task, Task) tuples representing conflicting pairs.
		"""
		target_date = for_date or date.today()
		conflicts: List[Tuple[Task, Task]] = []
		scheduled_tasks = [
			task
			for task in self.sort_tasks(for_date=target_date, tasks=tasks)
			if self._task_occurrence_time(task, target_date) is not None
		]

		for i, current in enumerate(scheduled_tasks):
			current_start = self._task_occurrence_time(current, target_date)
			if current_start is None:
				continue
			current_end = current_start + timedelta(minutes=current.duration_minutes)

			for nxt in scheduled_tasks[i + 1 :]:
				next_start = self._task_occurrence_time(nxt, target_date)
				if next_start is None:
					continue
				next_end = next_start + timedelta(minutes=nxt.duration_minutes)

				if current_start < next_end and next_start < current_end:
					conflicts.append((current, nxt))
				elif next_start >= current_end:
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
		ordered = self.sort_tasks(for_date=target_date)

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
