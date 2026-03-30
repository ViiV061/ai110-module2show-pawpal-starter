import streamlit as st
from datetime import date, datetime, time

from pawpal_system import Owner, Pet, Scheduler, Task

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")

st.markdown(
    """
Welcome to the PawPal+ starter app.

This file is intentionally thin. It gives you a working Streamlit app so you can start quickly,
but **it does not implement the project logic**. Your job is to design the system and build it.

Use this app as your interactive demo once your backend classes/functions exist.
"""
)

with st.expander("Scenario", expanded=True):
    st.markdown(
        """
**PawPal+** is a pet care planning assistant. It helps a pet owner plan care tasks
for their pet(s) based on constraints like time, priority, and preferences.

You will design and implement the scheduling logic and connect it to this Streamlit UI.
"""
    )

with st.expander("What you need to build", expanded=True):
    st.markdown(
        """
At minimum, your system should:
- Represent pet care tasks (what needs to happen, how long it takes, priority)
- Represent the pet and the owner (basic info and preferences)
- Build a plan/schedule for a day that chooses and orders tasks based on constraints
- Explain the plan (why each task was chosen and when it happens)
"""
    )

st.divider()

st.subheader("Quick Demo Inputs (UI only)")
owner_name = st.text_input("Owner name", value="Jordan")
pet_name = st.text_input("Pet name", value="Mochi")
species = st.selectbox("Species", ["dog", "cat", "other"])
pet_age = st.number_input("Pet age", min_value=0, max_value=40, value=3)
available_minutes = st.number_input(
    "Owner available minutes today", min_value=15, max_value=1440, value=120
)

if "owner" not in st.session_state:
    st.session_state.owner = Owner(name=owner_name, available_minutes=int(available_minutes))

owner = st.session_state.owner
owner.name = owner_name
owner.available_minutes = int(available_minutes)

st.markdown("### Pets")
if st.button("Add pet"):
    pet_exists = any(existing_pet.name == pet_name for existing_pet in owner.get_pets())
    if pet_exists:
        st.warning(f"Pet '{pet_name}' already exists.")
    else:
        owner.add_pet(Pet(name=pet_name, species=species, age=int(pet_age)))

if owner.get_pets():
    st.write("Current pets:")
    st.table(
        [
            {
                "pet": existing_pet.name,
                "species": existing_pet.species,
                "age": existing_pet.age,
                "task_count": len(existing_pet.get_tasks()),
            }
            for existing_pet in owner.get_pets()
        ]
    )
else:
    st.info("No pets yet. Add one above.")

st.markdown("### Tasks")
st.caption("Add task or schedule a walk for an existing pet.")

pet_options = [existing_pet.name for existing_pet in owner.get_pets()] or [pet_name]

col1, col2, col3 = st.columns(3)
with col1:
    target_pet_name = st.selectbox("Pet", pet_options)
with col2:
    task_title = st.text_input("Task description", value="Morning walk")
with col3:
    task_frequency = st.selectbox("Frequency", ["once", "daily", "weekly"], index=0)

col4, col5, col6 = st.columns(3)
with col4:
    duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=20)
with col5:
    priority = st.selectbox("Priority", ["low", "medium", "high"], index=2)
with col6:
    scheduled_time = st.time_input("Time", value=time(hour=9, minute=0))

selected_date = st.date_input("Date", value=date.today())

priority_map = {"low": 1, "medium": 2, "high": 3}

if st.button("Add task"):
    target_pet = next((pet for pet in owner.get_pets() if pet.name == target_pet_name), None)
    if target_pet is None:
        st.error("Add the pet first before assigning tasks.")
    else:
        target_pet.add_task(
            Task(
                description=task_title,
                duration_minutes=int(duration),
                priority=priority_map[priority],
                frequency=task_frequency,
                scheduled_time=datetime.combine(selected_date, scheduled_time),
                is_completed=False,
            )
        )

if st.button("Schedule a walk"):
    target_pet = next((pet for pet in owner.get_pets() if pet.name == target_pet_name), None)
    if target_pet is None:
        st.error("Add the pet first before scheduling a walk.")
    else:
        Scheduler(owner).schedule_walk(
            pet=target_pet,
            when=datetime.combine(selected_date, scheduled_time),
            duration_minutes=int(duration),
            priority=priority_map[priority],
            frequency=task_frequency,
        )

flat_tasks = [
    {
        "pet": existing_pet.name,
        "description": task.description,
        "duration_minutes": task.duration_minutes,
        "priority": task.priority,
        "frequency": task.frequency,
        "scheduled_time": task.scheduled_time,
        "is_completed": task.is_completed,
    }
    for existing_pet in owner.get_pets()
    for task in existing_pet.get_tasks()
]

if flat_tasks:
    st.write("Current tasks:")
    st.table(flat_tasks)
else:
    st.info("No tasks yet. Add one above.")

st.divider()

st.subheader("Build Schedule")
st.caption("Generate and show today's prioritized task plan.")

if st.button("Generate schedule"):
    owner = st.session_state.owner

    scheduler = Scheduler(owner=owner)
    todays_tasks = scheduler.get_todays_tasks()

    if not todays_tasks:
        st.warning("No tasks selected for today with current constraints.")
    else:
        st.success("Today's schedule generated.")
        st.table(
            [
                {
                    "description": task.description,
                    "time": task.scheduled_time.strftime("%H:%M") if task.scheduled_time else "unscheduled",
                    "duration_minutes": task.duration_minutes,
                    "priority": task.priority,
                    "frequency": task.frequency,
                }
                for task in todays_tasks
            ]
        )

        conflicts = scheduler.detect_conflicts()
        if conflicts:
            st.error("Conflicts detected in scheduled tasks:")
            st.table(
                [
                    {
                        "task_a": first.description,
                        "task_b": second.description,
                    }
                    for first, second in conflicts
                ]
            )
