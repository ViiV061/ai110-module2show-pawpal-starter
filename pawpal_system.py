from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Tuple


class Owner:
	def __init__(self, name: str, available_minutes: int) -> None:
		self.name = name
		self.available_minutes = available_minutes
		self._pets: List[Pet] = []

	def add_pet(self, pet: Pet) -> None:
		pass

	def get_pets(self) -> List[Pet]:
		pass


@dataclass
class Task:
	title: str
	category: str
	duration: int
	priority: int
	is_recurring: bool
	scheduled_time: str

	def is_conflicting(self, other: Task) -> bool:
		pass


@dataclass
class Pet:
	name: str
	species: str
	age: int
	_tasks: List[Task] = field(default_factory=list)

	def add_task(self, task: Task) -> None:
		pass

	def get_tasks(self) -> List[Task]:
		pass


class Scheduler:
	def __init__(self, pet: Optional[Pet] = None) -> None:
		self._pet = pet
		self._tasks: List[Task] = []

	def sort_tasks(self) -> List[Task]:
		pass

	def detect_conflicts(self) -> List[Tuple[Task, Task]]:
		pass

	def generate_schedule(self) -> List[Task]:
		pass
