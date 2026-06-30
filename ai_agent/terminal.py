from provider.credly.user_service import UserService
from ai_agent.copilot import Copilot


def print_banner():
    print()
    print("=" * 60)
    print("      CERTIFICATE INTELLIGENCE COPILOT")
    print("=" * 60)
    print()


def print_employee(employee):
    print(f"Employee         : {employee.full_name}")
    print(f"Certifications   : {len(employee.certifications)}")
    print(f"  - Native       : {sum(1 for c in employee.certifications if c.source == 'native')}")
    print(f"  - External     : {sum(1 for c in employee.certifications if c.source == 'external')}")
    print(f"Unique Skills    : {len(employee.unique_skills)}")
    no_expiry = sum(1 for c in employee.certifications if not c.expiry_date)
    if no_expiry:
        print(f"  ({no_expiry} certification(s) have no expiry date)")
    print()


def main(user_id: str):
    print_banner()
    print("Loading employee profile...")

    service = UserService()
    employee = service.load_employee(user_id)

    if not employee.certifications:
        print("⚠️  No certifications found. Check the Credly user_id and that the profile is public.")
        return

    print("✓ Employee Loaded")
    print()
    print_employee(employee)

    copilot = Copilot(employee)
    print("✓ AI Ready")
    print()
    print("Commands: 'context' to view raw data sent to AI | 'exit' to quit")
    print("-" * 60)

    while True:
        question = input("\nYou > ").strip()

        if not question:
            continue
        if question.lower() in ["exit", "quit"]:
            print("\nGoodbye!")
            break
        if question.lower() == "context":
            copilot.show_context()
            continue

        try:
            answer = copilot.chat(question)
            print()
            print("Copilot")
            print("-" * 20)
            print(answer)
        except Exception as e:
            print()
            print("Error")
            print("-" * 20)
            print(e)


if __name__ == "__main__":
    main("38056054-049b-4ad2-8929-82dc0ca985d0")
