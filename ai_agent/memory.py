from datetime import datetime


class Memory:

    def __init__(self):
        self.employee_context = ""
        self.chat_history = []
        self.created_at = datetime.now()

    def load_employee(self, employee):
        """
        Builds the full context string given to the AI.

        FIX vs original: previously this only ever saw whatever certifications
        happened to be in employee.certifications — which was incomplete because
        the sync only pulled from one Credly endpoint. Now that UserService pulls
        BOTH native + external badges, this naturally sees everything.

        FIX 2: skill listing now shows occurrence count (how many certs cover
        each skill) instead of a flat deduplicated list — this is what lets the
        AI reason about depth of expertise, not just breadth.
        """
        context = []

        context.append("=" * 60)
        context.append("EMPLOYEE INFORMATION")
        context.append("=" * 60)
        context.append(f"Name: {employee.full_name}")
        context.append(f"Credly ID: {employee.user_id}")
        context.append(f"Total Certifications: {len(employee.certifications)}")
        context.append("")

        context.append("=" * 60)
        context.append("CERTIFICATIONS (full detail)")
        context.append("=" * 60)

        for i, cert in enumerate(employee.certifications, 1):
            context.append(f"\n[{i}] {cert.name}")
            context.append(f"    Issuer        : {cert.issuer}")
            context.append(f"    Source        : {cert.source}")
            context.append(f"    Issue Date    : {cert.issue_date or 'Unknown'}")
            context.append(
                f"    Expiry Date   : {cert.expiry_date if cert.expiry_date else 'No expiry (does not expire)'}"
            )
            if cert.skills:
                skill_names = ", ".join(s.name for s in cert.skills)
                context.append(f"    Skills        : {skill_names}")
            else:
                context.append(f"    Skills        : (none listed)")

        context.append("")
        context.append("=" * 60)
        context.append("SKILL FREQUENCY (across all certifications, duplicates counted)")
        context.append("=" * 60)
        context.append(
            "Note: a higher count means the skill is reinforced by multiple "
            "certifications — a stronger signal of depth."
        )

        freq = employee.skill_frequency
        for name, count in sorted(freq.items(), key=lambda x: -x[1]):
            marker = f" (x{count})" if count > 1 else ""
            context.append(f"  • {name}{marker}")

        context.append("")
        context.append(f"Total unique skills: {len(freq)}")
        context.append(f"Total skill instances (with duplicates): {len(employee.all_skills)}")

        self.employee_context = "\n".join(context)

    def add_user_message(self, message):
        self.chat_history.append({"role": "user", "content": message})

    def add_ai_message(self, message):
        self.chat_history.append({"role": "assistant", "content": message})

    def build_prompt(self, question):
        history = [f"{m['role'].upper()}: {m['content']}" for m in self.chat_history]
        conversation = "\n".join(history)

        return f"""
EMPLOYEE CONTEXT

{self.employee_context}

----------------------------------------

CONVERSATION HISTORY

{conversation}

----------------------------------------

CURRENT USER QUESTION

{question}
"""

    def print_context(self):
        print(self.employee_context)
