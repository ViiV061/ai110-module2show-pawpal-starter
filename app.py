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

if "pets" not in st.session_state:
    st.session_state.pets = {}

st.markdown("### Pets")
if st.button("Add pet"):
    st.session_state.pets[pet_name] = {
        "species": species,
        "age": int(pet_age),
        "tasks": st.session_state.pets.get(pet_name, {}).get("tasks", []),
    }

if st.session_state.pets:
    st.write("Current pets:")
    st.table(
        [
            {
                "pet": name,
                "species": data["species"],
                "age": data["age"],
                "task_count": len(data["tasks"]),
            }
            for name, data in st.session_state.pets.items()
        ]
    )
else:
    st.info("No pets yet. Add one above.")

st.markdown("### Tasks")
st.caption("Add task or schedule a walk for an existing pet.")

if "tasks" not in st.session_state:
    st.session_state.tasks = []

pet_options = list(st.session_state.pets.keys()) or [pet_name]

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
    if target_pet_name not in st.session_state.pets:
        st.error("Add the pet first before assigning tasks.")
    else:
        st.session_state.pets[target_pet_name]["tasks"].append(
            {
                "description": task_title,
                "duration_minutes": int(duration),
                "priority": priority_map[priority],
                "frequency": task_frequency,
                "scheduled_time": datetime.combine(selected_date, scheduled_time),
                "is_completed": False,
            }
        )

if st.button("Schedule a walk"):
    if target_pet_name not in st.session_state.pets:
        st.error("Add the pet first before scheduling a walk.")
    else:
        st.session_state.pets[target_pet_name]["tasks"].append(
            {
                "description": f"Walk {target_pet_name}",
                "duration_minutes": int(duration),
                "priority": priority_map[priority],
                "frequency": task_frequency,
                "scheduled_time": datetime.combine(selected_date, scheduled_time),
                "is_completed": False,
            }
        )

flat_tasks = [
    {"pet": pet_name_key, **task}
    for pet_name_key, info in st.session_state.pets.items()
    for task in info["tasks"]
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
    owner = Owner(name=owner_name, available_minutes=int(available_minutes))

    for pet_name_key, pet_data in st.session_state.pets.items():
        pet = Pet(name=pet_name_key, species=pet_data["species"], age=pet_data["age"])
        for task_data in pet_data["tasks"]:
            pet.add_task(
                Task(
                    description=task_data["description"],
                    scheduled_time=task_data["scheduled_time"],
                    frequency=task_data["frequency"],
                    is_completed=task_data["is_completed"],
                    duration_minutes=task_data["duration_minutes"],
                    priority=task_data["priority"],
                )
            )
        owner.add_pet(pet)

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
