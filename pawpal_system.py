from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Tuple


class Owner:
	def __init__(self, name: str, available_minutes: int) -> None:
		self.name = name
		self.available_minutes = available_minutes
		self._pets: List[Pet] = []

	def add_pet(self, pet: Pet) -> None:
		"""Add a pet to the owner's pet list."""
		self._pets.append(pet)

	def get_pets(self) -> List[Pet]:
		"""Return the list of pets owned by this owner."""
		return self._pets


@dataclass
class Task:
	title: str
	category: str
	duration: int
	priority: int
	is_recurring: bool
	scheduled_time: Optional[datetime] = None

	def is_conflicting(self, other: Task) -> bool:
		pass


@dataclass
class Pet:
	name: str
	species: str
	age: int
	_tasks: List[Task] = field(default_factory=list)

	def add_task(self, task: Task) -> None:
		"""Add a task to the pet's task list."""
		self._tasks.append(task)

	def get_tasks(self) -> List[Task]:
		"""Return the list of tasks assigned to this pet."""
		return self._tasks


class Scheduler:
	def __init__(self, owner: Owner) -> None:
		"""Initialize scheduler with an Owner to manage all their pets' tasks."""
		self._owner = owner
		self._tasks: List[Task] = []

	def sort_tasks(self) -> List[Task]:
		pass

	def detect_conflicts(self) -> List[Tuple[Task, Task]]:
		pass

	def generate_schedule(self) -> List[Task]:
		pass
