# Critical Edge Cases for PawPal Pet Scheduler

## 1. RECURRING TASK EDGE CASES (Highest Priority)

### 1.1 Overdue Recurring Task Completion

- **What to test**: When a daily/weekly task is marked complete AFTER its scheduled date
- **Why it matters**: `_next_occurrence_time()` uses `completed_at.date()` as reference if later than scheduled date
- **Edge case**: Complete a task 5 days late → next occurrence should be from completion date, not scheduled date
- **Test scenarios**:
  - Complete daily task 3 days overdue
  - Complete weekly task 10 days overdue
  - Complete task on exact scheduled date vs. late vs. early

### 1.2 Duplicate Recurring Task Prevention

- **What to test**: Spawning next occurrence when one already exists
- **Why it matters**: `_get_duplicate_task()` prevents spawning duplicates
- **Edge case**: Manually add a task for tomorrow, then complete today's → should reuse existing, not create new
- **Test scenarios**:
  - Spawn next task when it already exists (same description, frequency, time)
  - Task with same description but different TIME (should spawn, not duplicate)
  - Task with same time but different description (should spawn)

### 1.3 Recurring Task Frequency Edge Cases

- **What to test**: Boundaries between daily/weekly/once
- **Why it matters**: 'once' should spawn nothing; daily should add 1 day; weekly should add 7 days
- **Edge case**:
  - Mark complete a 'once' task → should have NO next occurrence
  - Mark complete an invalid frequency task (typo like 'daily ' with space)
- **Test scenarios**:
  - Test with frequency = "once"
  - Test with frequency = "" (empty string)
  - Test with frequency = "daily", "weekly" (valid)
  - Test with frequency = "monthly", "hourly" (unsupported)

### 1.4 Weekly Task on Week Boundaries

- **What to test**: Recurring weekly task that spans week/month boundaries
- **Why it matters**: Must preserve day-of-week correctly
- **Edge case**: Complete a Monday weekly task on Sunday, next should be next Monday
- **Test scenarios**:
  - Weekly task scheduled for Monday, complete on Sunday
  - Weekly task at 11:59 PM → next occurrence same weekday next week
  - Weekly task crossing month boundary (e.g., Wed Mar 27 → Wed Apr 3)

---

## 2. CONFLICT DETECTION EDGE CASES (High Priority)

### 2.1 Task Duration Edge Cases

- **What to test**: How conflicts are detected based on `start_time` and `duration_minutes`
- **Why it matters**: `is_conflicting()` uses: `self_end = self.scheduled_time + timedelta(minutes=duration_minutes)`
- **Edge cases**:
  - Task with 0 duration (should it conflict with overlapping task?)
  - Task with very long duration (e.g., 1440 minutes = 24 hours)
  - One task ends exactly when another starts (9:00-9:30, 9:30-10:00 → conflict or not?)

### 2.2 Boundary Time Conflicts

- **What to test**: Exact overlap vs. partial overlap vs. adjacent
- **Why it matters**: Logic is `start1 < end2 AND start2 < end1` (excludes exact end matches)
- **Edge cases**:
  - Task 1: 8:00-8:30, Task 2: 8:30-9:00 (touching but not overlapping → no conflict ✓)
  - Task 1: 8:00-8:30, Task 2: 8:29-9:00 (partial overlap → conflict ✓)
  - Task 1: 8:00-8:30, Task 2: 8:00-8:30 (exact same time → conflict ✓)

### 2.3 Conflicts Between Different Pets

- **What to test**: Does owner's available time apply across all pets?
- **Why it matters**: Current implementation detects pet-agnostic conflicts (different pets at same time)
- **Edge cases**:
  - Dog task 8:00-8:30 + Cat task 8:00-8:30 → detected as conflict?
  - Owner has 90 mins free, two pets each need 60 mins at same time → should conflict?

### 2.4 Completed Task Conflicts

- **What to test**: Should completed tasks be part of conflict detection?
- **Why it matters**: Scenarios differ: maybe user deleted a scheduled task
- **Edge cases**:
  - Task 1 (completed): 8:00-8:30, Task 2 (pending): 8:00-8:30 → conflict or not?
  - `detect_conflicts(for_date=today)` includes completed tasks if they'd overlap with pending

### 2.5 Recurring Task Conflicts on Same Date

- **What to test**: Does a recurring daily/weekly task conflict with itself?
- **Why it matters**: `detect_conflicts()` uses `_task_occurrence_time()` to compute effective time
- **Edge cases**:
  - Daily task at 8:00 AM → on any given date, should only appear once (not conflict with itself)
  - Two separate instances of same recurring task (e.g., generated manually)

### 2.6 Tasks Without Scheduled Time

- **What to test**: Edge case where `scheduled_time = None`
- **Why it matters**: `is_conflicting()` returns False if either task has no time
- **Edge cases**:
  - Task with no scheduled time vs. task with time → no conflict (correct)
  - Two tasks both with no time → no conflict (correct)

---

## 3. SORTING & FILTERING EDGE CASES (Medium Priority)

### 3.1 Sorting with Tied Times and Priorities

- **What to test**: `sort_tasks()` orders by scheduled_time first, then priority
- **Edge cases**:
  - Multiple tasks at identical time + identical priority → stable sort?
  - All tasks same time, different priorities → correctly sorted by priority
  - All tasks different times, same priority → correctly sorted by time

### 3.2 Sorting with None or Missing Values

- **Edge cases**:
  - Task with `scheduled_time = None` in list → where does it sort?
  - Task with `priority = 0` or negative priority

### 3.3 Filter by Non-Existent Pet or Status

- **Edge cases**:
  - Filter pet_name = "Nonexistent" → should return empty list
  - Filter status = "invalid_status" → behavior not specified
  - Filter for_date in future (90 days) with weekly recurring task

### 3.4 Recurring Task Application Logic

- **What to test**: `_task_applies_to_date()` determines if a recurring task applies on a target date
- **Edge cases**:
  - Daily task scheduled 30 days ago → should apply to today
  - Weekly task scheduled on Monday, check Wednesday → should NOT apply
  - Weekly task scheduled on Monday, check next Monday → should apply
  - Task on future date → should NOT apply to past date

---

## 4. MULTI-PET & CATEGORIZATION EDGE CASES (Medium Priority)

### 4.1 Duplicate Task Names Across Pets

- **Edge cases**:
  - Dog: "Feed", Cat: "Feed" with overlapping times → both detected in conflicts?
  - Mark complete "Feed" → which pet gets marked?

### 4.2 Priority Ordering with Identical Priority

- **Edge cases**:
  - 5 tasks all priority 3 → tie-breaking by time should be consistent

### 4.3 Empty Owner/Pet/Task States

- **Edge cases**:
  - Owner with 0 pets
  - Pet with 0 tasks
  - Generate schedule for a date with no tasks
  - Detect conflicts with no tasks

---

## 5. INPUT VALIDATION EDGE CASES (Medium Priority)

### 5.1 Task Duration Values

- **Edge cases**:
  - `duration_minutes = 0` (zero-length task)
  - `duration_minutes = -30` (negative)
  - `duration_minutes = 10080` (7 days!)
  - `duration_minutes = None`

### 5.2 Task Description Edge Cases

- **Edge cases**:
  - Empty string: `description = ""`
  - Very long string: 1000+ character description
  - Special characters: emojis, unicode, newlines
  - Whitespace only: `description = "   "`

### 5.3 Owner Available Minutes

- **Edge cases**:
  - `available_minutes = 0` (no free time)
  - `available_minutes = -100` (negative)
  - `available_minutes = 1440` (full day)
  - Owner time vs. total task duration validation

### 5.4 Pet Age Edge Cases

- **Edge cases**:
  - `age = 0` (newborn)
  - `age = -1` (invalid)
  - `age = 50` (very old)

---

## 6. DATETIME/TIMEZONE EDGE CASES (Lower Priority)

### 6.1 Midnight Boundary Tasks

- **Edge cases**:
  - Task at 00:00 (midnight)
  - Task at 23:59 (nearly midnight)
  - Task duration spanning midnight (e.g., 23:00-01:00)

### 6.2 Date Boundary Recurring Tasks

- **Edge cases**:
  - Complete daily task at 23:59 on Dec 31 → next should be Jan 1 00:xx
  - Weekly task from March to April (cross month boundary)

### 6.3 Daylight Saving Time (DST) Edge Cases

- **Edge cases**:
  - March → April (DST forward): task scheduled for 2:30 AM doesn't exist
  - October → November (DST backward): 1:30 AM happens twice
  - Weekly task spanning DST change

---

## 7. SUGGESTED TEST IMPLEMENTATION ORDER

**Phase 1 (Critical - implement first):**

1. Overdue recurring task completion
2. Duplicate recurring task prevention
3. Conflict detection boundary conditions
4. Sorting with tied values

**Phase 2 (Important - implement next):** 5. Recurring task at week boundaries 6. Multi-pet conflict detection 7. Task without scheduled_time 8. Filter by non-existent pet

**Phase 3 (Good to have - implement after):** 9. Invalid frequency values 10. Negative/zero duration tasks 11. Empty owner/pet states 12. Special character descriptions

---

## 8. RECOMMENDED PARAMETERIZED TEST PATTERNS

```python
# Pattern 1: Conflict detection boundary testing
@pytest.mark.parametrize("task1_end,task2_start,should_conflict", [
    (8, 30, 8, 30, False),     # Adjacent (no conflict)
    (8, 30, 8, 29, True),      # Partial overlap
    (8, 30, 8, 00, True),      # Task 2 contained in Task 1
])
def test_conflict_boundaries(task1_end, task2_start, should_conflict):
    ...

# Pattern 2: Recurring task delay testing
@pytest.mark.parametrize("days_overdue,frequency", [
    (1, "daily"), (3, "daily"), (10, "weekly"), (7, "weekly")
])
def test_overdue_recurring_completion(days_overdue, frequency):
    ...

# Pattern 3: Sorting stability testing
@pytest.mark.parametrize("times,priorities,expected_order", [
    ([1, 1, 1], [1, 2, 3], [[1], [2], [3]]),  # All same time, diff priority
    ([1, 2, 3], [1, 1, 1], [[1], [2], [3]]),  # All same priority, diff time
])
def test_sort_stability(times, priorities, expected_order):
    ...
```
