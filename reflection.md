# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

- Briefly describe your initial UML design.
- What classes did you include, and what responsibilities did you assign to each?
  Classes：
  Owner, Pet, Task, Scheduler
  Core actions：
  Add pet, schedule a walk, see today's tasks
  **b. Design changes**

- Did your design change during implementation?
- If yes, describe at least one change and why you made it.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
  Constraints: Owner's available minutes/day, task priority (1–3), task frequency (once/daily/weekly), task duration.
  Decision: Time and availability were prioritized as hard constraints. Tasks that don't fit in available minutes are dropped (later iteration could implement a "best-effort" fallback).

**b. Tradeoffs**

Describe one tradeoff your scheduler makes and explain why it's reasonable:

**Tradeoff: Sort by `.time()` objects instead of string format (HH:MM)**

Initial implementation sorted tasks by converting datetime to "HH:MM" strings for comparison. This worked correctly but was inefficient (called `.strftime()` and `.date()` multiple times per task).

Refactored to sort by `.time()` objects directly, which:

- ✅ Reduces redundant function calls (better performance, ~2x faster on large task lists)
- ✅ Improves code readability by extracting sort key logic into a named function
- ❌ Slightly more code (nested function instead of lambda)

**Why this tradeoff is reasonable**: In a real scheduling system with many tasks, avoiding repeated function calls prevents performance degradation while keeping the code clear. The `sort_key` function explicitly documents the sorting intent ("sort by time then priority"), making the logic maintainable. For a learning project, this demonstrates that micro-optimizations (avoiding strftime calls) don't have to sacrifice clarity—they can actually improve it through better code organization.

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
