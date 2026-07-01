import ssl

from database.repository import EmployeeRepository, ReminderRepository
from services.reminder_engine import ReminderEngine
ssl._create_default_https_context = ssl._create_unverified_context

from database.schema import Schema
from services.sync_engine import SyncEngine
from services.expiry_engine import ExpiryEngine
from ai_agent.copilot import Copilot

USER_ID = "38056054-049b-4ad2-8929-82dc0ca985d0"


def print_expiry_report(employee):
    engine = ExpiryEngine()
    statuses = engine.get_status(employee)

    print()
    print("-" * 60)
    print("CERTIFICATION EXPIRY STATUS")
    print("-" * 60)

    for item in statuses:
        print(f"Certification : {item.certification}")
        print(f"Expiry Date   : {item.expiry_date or 'N/A'}")
        print(f"Days Remaining: {item.days_remaining if item.days_remaining is not None else 'N/A'}")
        print(f"Status        : {item.status}")
        print("-" * 60)

def print_list_skills(employee):
    skills = set()
    for cert in employee.certifications:
        for skill in cert.skills:
            skills.add(skill.name)
    
    print()
    print("-" * 60)
    print("ALL SKILLS ACROSS CERTIFICATIONS")
    print("-" * 60)
    
    for skill in sorted(skills):
        print(f"- {skill}")
    
def print_reminders(employee_id):
    repo = ReminderRepository()
    reminders = repo.get_pending(employee_id)

    print()
    print("-" * 60)
    print(f"PENDING REMINDERS  ({len(reminders)})")
    print("-" * 60)

    if not reminders:
        print("  No pending reminders.")
    else:
        for r in reminders:
            print(f"  [{r['reminder_type']}] {r['message']}")
    print()





def main():
    # 1. DB ready
    Schema().create_tables()

    # 2. Sync from Credly
    employee = SyncEngine().run(USER_ID)

    if not employee.certifications:
        return

    # 3. Expiry report
    print_expiry_report(employee)
    
    # 4.Reminder engine
    employee_repo = EmployeeRepository()
    db_employee = employee_repo.get_by_credly_id(USER_ID)
    employee_id = db_employee["id"]
    engine =ReminderEngine()
    count = engine.run(employee,employee_id)
    print(f"\n{count} reminders created for expiring certifications.\n")
    print_reminders(employee_id)
    # 5. List all skills
    print_list_skills(employee)
    # 6. AI chat
    print()
    print("=" * 60)
    print("Starting AI Copilot...")
    print("=" * 60)

    copilot = Copilot(employee)
    print("Ai is ready for interaction. Type 'exit' to quit.\n")

    while True:
        question = input("You > ").strip()
        if not question:
            continue
        if question.lower() in ["exit", "quit"]:
            print("See you Again!")
            break
        try:
            answer = copilot.chat(question)
            print(f"\nCopilot\n{'-'*20}\n{answer}\n")
        except Exception as e:
            print(f"\nError: {e}\n")


if __name__ == "__main__":
    main()
