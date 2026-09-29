"""Create the synthetic SQLite database used by the demo mode."""

from pathlib import Path

from queryguard.demo import create_demo_database

if __name__ == "__main__":
    target = create_demo_database(Path("data/demo.sqlite"))
    print(f"Created demo database: {target}")
