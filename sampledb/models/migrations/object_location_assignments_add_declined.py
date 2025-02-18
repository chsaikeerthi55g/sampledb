# coding: utf-8
"""
Add declined column to object location assignments table.
"""

import os

MIGRATION_INDEX = 111
MIGRATION_NAME, _ = os.path.splitext(os.path.basename(__file__))


def run(db):
    # Skip migration by condition
    column_names = db.session.execute("""
        SELECT column_name
        FROM information_schema.columns
        WHERE table_name = 'object_location_assignments'
    """).fetchall()
    if ('declined',) in column_names:
        return False

    # Perform migration
    db.session.execute("""
        ALTER TABLE object_location_assignments
        ADD declined BOOLEAN DEFAULT FALSE NOT NULL
    """)
    db.session.execute("""
        ALTER TABLE object_location_assignments
        ADD CONSTRAINT object_location_assignments_not_both_states_check
            CHECK (
                NOT (confirmed AND declined)
            )
    """)
    return True
