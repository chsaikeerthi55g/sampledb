# coding: utf-8
"""
Replace the view user_object_permissions_by_all to use
all_user_object_permissions instead of public_objects.

The new version also avoids unnecessary jsonb objects and only returns one row
for each object_id and user_id combination, containing the maximum permissions.
"""

import os

MIGRATION_INDEX = 97
MIGRATION_NAME, _ = os.path.splitext(os.path.basename(__file__))


def run(db):
    # Perform migration
    db.engine.execute("""
    CREATE OR REPLACE VIEW user_object_permissions_by_all
    AS SELECT
    u.user_id AS user_id,
    u.object_id AS object_id,
    MAX(u.permissions_int) AS permissions_int
    FROM (
        SELECT
        NULL AS user_id,
        object_id AS object_id,
        CASE all_user_object_permissions.permissions
            WHEN 'NONE' THEN 0
            WHEN 'READ' THEN 1
            WHEN 'WRITE' THEN 2
            WHEN 'GRANT' THEN 3
            ELSE 0
        END AS permissions_int
        FROM all_user_object_permissions
    UNION
        SELECT
        association.user_id AS user_id,
        objects.object_id AS object_id,
        3 AS permissions_int
        FROM association AS association
        JOIN actions AS actions ON association.instrument_id = actions.instrument_id
        JOIN objects_current AS objects ON objects.action_id = actions.id
    UNION
        SELECT
        user_object_permissions.user_id AS user_id,
        user_object_permissions.object_id AS object_id,
        CASE user_object_permissions.permissions
            WHEN 'NONE' THEN 0
            WHEN 'READ' THEN 1
            WHEN 'WRITE' THEN 2
            WHEN 'GRANT' THEN 3
            ELSE 0
        END AS permissions_int
        FROM user_object_permissions
    UNION
        SELECT
        user_group_memberships.user_id AS user_id,
        group_object_permissions.object_id AS object_id,
        CASE group_object_permissions.permissions
            WHEN 'NONE' THEN 0
            WHEN 'READ' THEN 1
            WHEN 'WRITE' THEN 2
            WHEN 'GRANT' THEN 3
            ELSE 0
        END AS permissions_int
        FROM user_group_memberships AS user_group_memberships
        JOIN group_object_permissions AS group_object_permissions ON user_group_memberships.group_id = group_object_permissions.group_id
    UNION
        SELECT
        user_project_permissions.user_id AS user_id,
        project_object_permissions.object_id AS object_id,
        LEAST(
            CASE project_object_permissions.permissions
                WHEN 'NONE' THEN 0
                WHEN 'READ' THEN 1
                WHEN 'WRITE' THEN 2
                WHEN 'GRANT' THEN 3
                ELSE 0
            END,
            CASE user_project_permissions.permissions
                WHEN 'NONE' THEN 0
                WHEN 'READ' THEN 1
                WHEN 'WRITE' THEN 2
                WHEN 'GRANT' THEN 3
                ELSE 0
            END
        ) AS permissions_int
        FROM user_project_permissions AS user_project_permissions
        JOIN project_object_permissions AS project_object_permissions ON user_project_permissions.project_id = project_object_permissions.project_id
    UNION
        SELECT
        user_group_memberships.user_id AS user_id,
        project_object_permissions.object_id AS object_id,
        LEAST(
            CASE project_object_permissions.permissions
                WHEN 'NONE' THEN 0
                WHEN 'READ' THEN 1
                WHEN 'WRITE' THEN 2
                WHEN 'GRANT' THEN 3
                ELSE 0
            END,
            CASE group_project_permissions.permissions
                WHEN 'NONE' THEN 0
                WHEN 'READ' THEN 1
                WHEN 'WRITE' THEN 2
                WHEN 'GRANT' THEN 3
                ELSE 0
            END
        ) AS permissions_int
        FROM user_group_memberships AS user_group_memberships
        JOIN group_project_permissions ON group_project_permissions.group_id = user_group_memberships.group_id
        JOIN project_object_permissions AS project_object_permissions ON group_project_permissions.project_id = project_object_permissions.project_id
    ) AS u
    GROUP BY (u.object_id, u.user_id)
    """)
    return True
