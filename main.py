"""
Main entry point.

Flow:
  1. Ensure DB schema exists
  2. Sync employee from Credly → SQLite (both native + external badges)
  3. Print expiry status report
  4. Launch the AI terminal chat using the FULL, freshly-loaded employee object
"""

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


def main():
    # 1. DB ready
    Schema().create_tables()

    # 2. Sync from Credly
    employee = SyncEngine().run(USER_ID)

    if not employee.certifications:
        return

    # 3. Expiry report
    print_expiry_report(employee)

    # 4. AI chat
    print()
    print("=" * 60)
    print("Starting AI Copilot...")
    print("=" * 60)

    copilot = Copilot(employee)
    print("✓ AI Ready. Type 'exit' to quit.\n")

    while True:
        question = input("You > ").strip()
        if not question:
            continue
        if question.lower() in ["exit", "quit"]:
            print("Goodbye!")
            break
        try:
            answer = copilot.chat(question)
            print(f"\nCopilot\n{'-'*20}\n{answer}\n")
        except Exception as e:
            print(f"\nError: {e}\n")


if __name__ == "__main__":
    main()
