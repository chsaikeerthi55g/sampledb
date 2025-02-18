# coding: utf-8
"""
Replace NOT NULL constraints per column by NOT NULL constraints conditioned by federation reference in object_location_assignments.
"""

import os

MIGRATION_INDEX = 85
MIGRATION_NAME, _ = os.path.splitext(os.path.basename(__file__))


def run(db):
    constraints = db.session.execute("""
         SELECT conname
         FROM pg_catalog.pg_constraint
         WHERE conname = 'object_location_assignments_not_null_check'
    """).fetchall()

    if len(constraints) > 0:
        return False

    # Perform migration
    db.session.execute("""
        ALTER TABLE object_location_assignments
            ADD CONSTRAINT object_location_assignments_not_null_check
                CHECK (
                    (
                        fed_id IS NOT NULL AND
                        component_id IS NOT NULL
                    ) OR (
                        description IS NOT NULL AND
                        user_id IS NOT NULL AND
                        utc_datetime IS NOT NULL
                    )
                ),
            ALTER COLUMN description DROP NOT NULL,
            ALTER COLUMN user_id DROP NOT NULL,
            ALTER COLUMN utc_datetime DROP NOT NULL
    """)
    return True
