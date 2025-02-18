# coding: utf-8
"""
Add type_id column to locations table and set default location type.
"""

import os

from ..locations import LocationType

MIGRATION_INDEX = 116
MIGRATION_NAME, _ = os.path.splitext(os.path.basename(__file__))


def run(db):
    # Skip migration by condition
    column_names = db.session.execute("""
        SELECT column_name
        FROM information_schema.columns
        WHERE table_name = 'locations'
    """).fetchall()
    if ('type_id',) in column_names:
        return False

    # Perform migration
    db.session.execute("""
        ALTER TABLE locations
            ADD type_id INTEGER NULL,
            ADD FOREIGN KEY(type_id) REFERENCES location_types(id)
    """)

    db.session.execute("""
        UPDATE locations
        SET type_id = :type_id
        WHERE type_id IS NULL
    """, params={
        'type_id': LocationType.LOCATION
    })

    db.session.execute("""
        ALTER TABLE locations
        ALTER type_id SET NOT NULL
    """)
    return True
