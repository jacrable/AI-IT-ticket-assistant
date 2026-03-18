import sqlite3
from datetime import datetime
from dotenv import load_dotenv
import os
from openai import OpenAI

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

DB_NAME = "tickets.db"


def setup_database():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tickets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            issue TEXT NOT NULL,
            category TEXT NOT NULL,
            priority TEXT NOT NULL,
            ai_response TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()


def ask_ai(issue_text):
    prompt = f"""
You are an IT support assistant.

A user reported this issue:
"{issue_text}"

Return your answer in this exact format:

Category: <one of: Hardware, Software, Network, Security, Account Access, Other>
Priority: <Low, Medium, High>
Troubleshooting Steps:
1. ...
2. ...
3. ...

Keep the answer practical, clear, and short.
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )

    return response.choices[0].message.content.strip()


def extract_field(text, field_name):
    for line in text.splitlines():
        if line.lower().startswith(field_name.lower() + ":"):
            return line.split(":", 1)[1].strip()
    return "Unknown"


def save_ticket(issue, category, priority, ai_response):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO tickets (created_at, issue, category, priority, ai_response)
        VALUES (?, ?, ?, ?, ?)
    """, (
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        issue,
        category,
        priority,
        ai_response
    ))

    conn.commit()
    conn.close()


def view_tickets():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, created_at, category, priority, issue
        FROM tickets
        ORDER BY id DESC
    """)

    rows = cursor.fetchall()
    conn.close()

    if not rows:
        print("\nNo tickets found.\n")
        return

    print("\nSaved Tickets:")
    print("-" * 80)
    for row in rows:
        ticket_id, created_at, category, priority, issue = row
        print(f"ID: {ticket_id}")
        print(f"Date: {created_at}")
        print(f"Category: {category}")
        print(f"Priority: {priority}")
        print(f"Issue: {issue}")
        print("-" * 80)


def create_ticket():
    issue = input("\nDescribe the IT issue: ").strip()
    if not issue:
        print("Issue cannot be empty.")
        return

    print("\nAnalyzing with AI...\n")
    ai_response = ask_ai(issue)

    category = extract_field(ai_response, "Category")
    priority = extract_field(ai_response, "Priority")

    print("AI Result:")
    print("-" * 80)
    print(ai_response)
    print("-" * 80)

    save_ticket(issue, category, priority, ai_response)
    print("\nTicket saved successfully.\n")


def main():
    setup_database()

    while True:
        print("AI IT Support Ticket Assistant")
        print("1. Create new ticket")
        print("2. View saved tickets")
        print("3. Exit")

        choice = input("Choose an option: ").strip()

        if choice == "1":
            create_ticket()
        elif choice == "2":
            view_tickets()
        elif choice == "3":
            print("Goodbye.")
            break
        else:
            print("Invalid choice. Please try again.\n")


if __name__ == "__main__":
    main()