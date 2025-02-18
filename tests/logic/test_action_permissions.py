# coding: utf-8
"""

"""

import pytest

import sampledb
import sampledb.logic
from sampledb.logic import action_permissions, groups, action_translations, languages, instrument_translations
from sampledb.models import User, UserType, Action, Instrument, Permissions, UserActionPermissions


__author__ = 'Florian Rhiem <f.rhiem@fz-juelich.de>'


@pytest.fixture
def users():
    names = ['User 1', 'User 2']
    users = [User(name=name, email="example@example.com", type=UserType.PERSON) for name in names]
    for user in users:
        sampledb.db.session.add(user)
        sampledb.db.session.commit()
        # force attribute refresh
        assert user.id is not None
    return users


@pytest.fixture
def independent_action():
    action = Action(
        action_type_id=sampledb.models.ActionType.SAMPLE_CREATION,
        schema={
            'title': 'Example Action',
            'type': 'action',
            'properties': {}
        },
        instrument_id=None
    )
    sampledb.db.session.add(action)
    sampledb.db.session.commit()
    action_translations.set_action_translation(
        language_id=languages.Language.ENGLISH,
        action_id=action.id,
        name='Example Action',
        description='',
    )
    # force attribute refresh
    assert action.id is not None
    return action


@pytest.fixture
def user_action(users):
    action = Action(
        action_type_id=sampledb.models.ActionType.SAMPLE_CREATION,
        schema={
            'title': 'Example Action',
            'type': 'action',
            'properties': {}
        },
        instrument_id=None,
        user_id=users[1].id
    )
    sampledb.db.session.add(action)
    sampledb.db.session.commit()
    action_translations.set_action_translation(
        language_id=languages.Language.ENGLISH,
        action_id=action.id,
        name='Example Action',
        description='',
    )
    # force attribute refresh
    assert action.id is not None
    return action


@pytest.fixture
def instrument():
    instrument = Instrument()
    sampledb.db.session.add(instrument)
    sampledb.db.session.commit()
    instrument_translations.set_instrument_translation(
        language_id=languages.Language.ENGLISH,
        instrument_id=instrument.id,
        name='Example Instrument',
        description=''
    )
    # force attribute refresh
    assert instrument.id is not None
    return instrument


@pytest.fixture
def instrument_action(instrument):
    action = Action(
        action_type_id=sampledb.models.ActionType.SAMPLE_CREATION,
        schema={
            'title': 'Example Action',
            'type': 'action',
            'properties': {}
        },
        instrument_id=instrument.id
    )
    sampledb.db.session.add(action)
    sampledb.db.session.commit()
    action_translations.set_action_translation(
        language_id=languages.Language.ENGLISH,
        action_id=action.id,
        name='Example Action',
        description='',
    )
    # force attribute refresh
    assert action.id is not None
    return action


@pytest.fixture
def user(users):
    return users[0]


def test_public_actions(independent_action, user_action):
    # non-user actions will always
    action_id = independent_action.id
    assert Permissions.READ not in action_permissions.get_action_permissions_for_all_users(action_id)
    action_permissions.set_action_permissions_for_all_users(action_id, sampledb.models.Permissions.READ)
    assert Permissions.READ in action_permissions.get_action_permissions_for_all_users(action_id)
    action_permissions.set_action_permissions_for_all_users(action_id, sampledb.models.Permissions.NONE)
    assert Permissions.READ not in action_permissions.get_action_permissions_for_all_users(action_id)

    action_id = user_action.id
    assert Permissions.READ not in action_permissions.get_action_permissions_for_all_users(action_id)
    action_permissions.set_action_permissions_for_all_users(action_id, sampledb.models.Permissions.READ)
    assert Permissions.READ in action_permissions.get_action_permissions_for_all_users(action_id)
    action_permissions.set_action_permissions_for_all_users(action_id, sampledb.models.Permissions.NONE)
    assert Permissions.READ not in action_permissions.get_action_permissions_for_all_users(action_id)


def test_get_user_action_permissions(user, independent_action):
    user_id = user.id
    action_id = independent_action.id
    sampledb.db.session.add(UserActionPermissions(user_id=user_id, action_id=action_id, permissions=Permissions.WRITE))
    sampledb.db.session.commit()
    assert action_permissions.get_user_action_permissions(user_id=user_id, action_id=action_id) == Permissions.WRITE


def test_get_user_action_permissions_with_project(users, user_action):
    user_id = users[0].id
    action_id = user_action.id
    project_id = sampledb.logic.projects.create_project("Example Project", "", users[1].id).id
    assert action_permissions.get_user_action_permissions(user_id=user_id, action_id=action_id) == Permissions.NONE
    action_permissions.set_project_action_permissions(project_id=project_id, action_id=action_id, permissions=Permissions.GRANT)
    assert action_permissions.get_user_action_permissions(user_id=user_id, action_id=action_id) == Permissions.NONE
    sampledb.logic.projects.add_user_to_project(project_id, user_id, Permissions.READ)
    assert action_permissions.get_user_action_permissions(user_id=user_id, action_id=action_id) == Permissions.READ
    sampledb.db.session.add(UserActionPermissions(user_id=user_id, action_id=action_id, permissions=Permissions.WRITE))
    sampledb.db.session.commit()
    assert action_permissions.get_user_action_permissions(user_id=user_id, action_id=action_id) == Permissions.WRITE
    sampledb.logic.projects.update_user_project_permissions(project_id, user_id, Permissions.GRANT)
    assert action_permissions.get_user_action_permissions(user_id=user_id, action_id=action_id) == Permissions.GRANT


def test_get_user_action_permissions_with_group_project(users, user_action):
    user_id = users[0].id
    action_id = user_action.id
    project_id = sampledb.logic.projects.create_project("Example Project", "", users[1].id).id
    assert action_permissions.get_user_action_permissions(user_id=user_id, action_id=action_id) == Permissions.NONE
    action_permissions.set_project_action_permissions(project_id=project_id, action_id=action_id, permissions=Permissions.GRANT)
    assert action_permissions.get_user_action_permissions(user_id=user_id, action_id=action_id) == Permissions.NONE
    group_id = sampledb.logic.groups.create_group("Example Group", "", users[1].id).id
    sampledb.logic.projects.add_group_to_project(project_id, group_id, Permissions.READ)
    assert action_permissions.get_user_action_permissions(user_id=user_id, action_id=action_id) == Permissions.NONE
    sampledb.logic.groups.add_user_to_group(group_id=group_id, user_id=user_id)
    assert action_permissions.get_user_action_permissions(user_id=user_id, action_id=action_id) == Permissions.READ
    sampledb.db.session.add(UserActionPermissions(user_id=user_id, action_id=action_id, permissions=Permissions.WRITE))
    sampledb.db.session.commit()
    assert action_permissions.get_user_action_permissions(user_id=user_id, action_id=action_id) == Permissions.WRITE
    sampledb.logic.projects.update_group_project_permissions(project_id, group_id, Permissions.GRANT)
    assert action_permissions.get_user_action_permissions(user_id=user_id, action_id=action_id) == Permissions.GRANT


def test_get_instrument_responsible_user_action_permissions(user, instrument, instrument_action):
    user_id = user.id
    action_id = instrument_action.id
    instrument.responsible_users.append(user)
    sampledb.db.session.add(instrument)
    sampledb.db.session.add(UserActionPermissions(user_id=user_id, action_id=action_id, permissions=Permissions.WRITE))
    sampledb.db.session.commit()
    assert action_permissions.get_user_action_permissions(user_id=user_id, action_id=action_id) == Permissions.GRANT


def test_get_user_user_action_permissions(users, user_action):
    action_id = user_action.id

    user_id = users[0].id
    assert action_permissions.get_user_action_permissions(user_id=user_id, action_id=action_id) == Permissions.NONE

    user_id = users[1].id
    assert action_permissions.get_user_action_permissions(user_id=user_id, action_id=action_id) == Permissions.GRANT


def test_get_user_public_action_permissions(user, user_action, independent_action):
    user_id = user.id
    action_id = user_action.id
    action_permissions.set_action_permissions_for_all_users(action_id, sampledb.models.Permissions.READ)
    assert action_permissions.get_user_action_permissions(user_id=user_id, action_id=action_id) == Permissions.READ

    action_id = independent_action.id
    assert action_permissions.get_user_action_permissions(user_id=user_id, action_id=action_id) == Permissions.NONE
    action_permissions.set_action_permissions_for_all_users(action_id, sampledb.models.Permissions.READ)
    assert action_permissions.get_user_action_permissions(user_id=user_id, action_id=action_id) == Permissions.READ


def test_get_action_permissions_for_users(users, user_action):
    user_id = users[0].id
    action_id = user_action.id

    assert action_permissions.get_action_permissions_for_users(action_id=action_id) == {}
    sampledb.db.session.add(UserActionPermissions(user_id=user_id, action_id=action_id, permissions=Permissions.WRITE))
    sampledb.db.session.commit()
    assert action_permissions.get_action_permissions_for_users(action_id=action_id) == {
        user_id: Permissions.WRITE
    }


def test_get_action_permissions_with_projects(users, user_action):
    user_id = users[0].id
    action_id = user_action.id

    assert {
        user.id: action_permissions.get_user_action_permissions(action_id=action_id, user_id=user.id)
        for user in users
    } == {
        users[0].id: Permissions.NONE,
        users[1].id: Permissions.GRANT
    }

    project_id = sampledb.logic.projects.create_project("Example Project", "", users[1].id).id

    action_permissions.set_project_action_permissions(action_id=action_id, project_id=project_id, permissions=Permissions.WRITE)

    assert {
        user.id: action_permissions.get_user_action_permissions(action_id=action_id, user_id=user.id)
        for user in users
    } == {
        users[0].id: Permissions.NONE,
        users[1].id: Permissions.GRANT
    }

    sampledb.logic.projects.add_user_to_project(project_id, user_id, Permissions.READ)

    assert {
        user.id: action_permissions.get_user_action_permissions(action_id=action_id, user_id=user.id, include_projects=False)
        for user in users
    } == {
        users[0].id: Permissions.NONE,
        users[1].id: Permissions.GRANT
    }

    assert {
        user.id: action_permissions.get_user_action_permissions(action_id=action_id, user_id=user.id)
        for user in users
    } == {
        user_id: Permissions.READ,
        users[1].id: Permissions.GRANT
    }

    group_id = sampledb.logic.groups.create_group("Example Group", "", users[1].id).id

    sampledb.logic.projects.add_group_to_project(project_id=project_id, group_id=group_id, permissions=Permissions.WRITE)

    assert {
        user.id: action_permissions.get_user_action_permissions(action_id=action_id, user_id=user.id)
        for user in users
    } == {
        user_id: Permissions.READ,
        users[1].id: Permissions.GRANT
    }

    sampledb.logic.groups.add_user_to_group(group_id=group_id, user_id=user_id)

    assert {
        user.id: action_permissions.get_user_action_permissions(action_id=action_id, user_id=user.id, include_groups=False)
        for user in users
    } == {
        user_id: Permissions.READ,
        users[1].id: Permissions.GRANT
    }

    assert {
        user.id: action_permissions.get_user_action_permissions(action_id=action_id, user_id=user.id)
        for user in users
    } == {
        user_id: Permissions.WRITE,
        users[1].id: Permissions.GRANT
    }

    sampledb.logic.groups.remove_user_from_group(group_id=group_id, user_id=user_id)

    assert {
        user.id: action_permissions.get_user_action_permissions(action_id=action_id, user_id=user.id)
        for user in users
    } == {
        user_id: Permissions.READ,
        users[1].id: Permissions.GRANT
    }


def test_set_user_action_permissions(users, user_action):
    user_id = users[0].id
    action_id = user_action.id

    assert action_permissions.get_action_permissions_for_users(action_id=action_id) == {}
    action_permissions.set_user_action_permissions(action_id=action_id, user_id=user_id, permissions=Permissions.WRITE)
    assert action_permissions.get_action_permissions_for_users(action_id=action_id) == {
        user_id: Permissions.WRITE
    }

    action_permissions.set_user_action_permissions(action_id=action_id, user_id=user_id, permissions=Permissions.READ)
    assert action_permissions.get_action_permissions_for_users(action_id=action_id) == {
        user_id: Permissions.READ
    }

    action_permissions.set_user_action_permissions(action_id=action_id, user_id=user_id, permissions=Permissions.NONE)
    assert action_permissions.get_action_permissions_for_users(action_id=action_id) == {}


def test_group_permissions(users, user_action):
    user, creator = users
    action_id = user_action.id
    group_id = groups.create_group("Example Group", "", creator.id).id

    assert Permissions.READ not in action_permissions.get_action_permissions_for_all_users(action_id)
    assert action_permissions.get_user_action_permissions(action_id=action_id, user_id=user.id) == Permissions.NONE

    action_permissions.set_group_action_permissions(action_id=action_id, group_id=group_id, permissions=Permissions.WRITE)

    assert Permissions.READ not in action_permissions.get_action_permissions_for_all_users(action_id)
    assert action_permissions.get_user_action_permissions(action_id=action_id, user_id=user.id) == Permissions.NONE

    groups.add_user_to_group(group_id=group_id, user_id=user.id)

    assert Permissions.READ not in action_permissions.get_action_permissions_for_all_users(action_id)
    assert action_permissions.get_user_action_permissions(action_id=action_id, user_id=user.id) == Permissions.WRITE

    action_permissions.set_user_action_permissions(action_id=action_id, user_id=user.id, permissions=Permissions.READ)

    assert Permissions.READ not in action_permissions.get_action_permissions_for_all_users(action_id)
    assert action_permissions.get_user_action_permissions(action_id=action_id, user_id=user.id) == Permissions.WRITE

    action_permissions.set_group_action_permissions(action_id=action_id, group_id=group_id, permissions=Permissions.READ)
    action_permissions.set_user_action_permissions(action_id=action_id, user_id=user.id, permissions=Permissions.WRITE)

    assert Permissions.READ not in action_permissions.get_action_permissions_for_all_users(action_id)
    assert action_permissions.get_user_action_permissions(action_id=action_id, user_id=user.id) == Permissions.WRITE

    action_permissions.set_user_action_permissions(action_id=action_id, user_id=user.id, permissions=Permissions.READ)
    action_permissions.set_group_action_permissions(action_id=action_id, group_id=group_id, permissions=Permissions.GRANT)
    groups.remove_user_from_group(group_id=group_id, user_id=user.id)

    assert Permissions.READ not in action_permissions.get_action_permissions_for_all_users(action_id)
    assert action_permissions.get_user_action_permissions(action_id=action_id, user_id=user.id) == Permissions.READ


def test_action_permissions_for_groups(users, user_action):
    user, creator = users
    action_id = user_action.id
    group_id = groups.create_group("Example Group", "", creator.id).id

    assert action_permissions.get_action_permissions_for_groups(action_id) == {}

    action_permissions.set_group_action_permissions(action_id=action_id, group_id=group_id, permissions=Permissions.WRITE)

    assert action_permissions.get_action_permissions_for_groups(action_id) == {
        group_id: Permissions.WRITE
    }

    action_permissions.set_group_action_permissions(action_id=action_id, group_id=group_id, permissions=Permissions.NONE)

    assert action_permissions.get_action_permissions_for_groups(action_id) == {}


def test_action_permissions_for_projects(users, user_action):
    user, creator = users
    action_id = user_action.id
    project_id = sampledb.logic.projects.create_project("Example Project", "", creator.id).id

    assert action_permissions.get_action_permissions_for_projects(action_id) == {}

    action_permissions.set_project_action_permissions(action_id=action_id, project_id=project_id, permissions=Permissions.WRITE)

    assert action_permissions.get_action_permissions_for_projects(action_id) == {
        project_id: Permissions.WRITE
    }

    action_permissions.set_project_action_permissions(action_id=action_id, project_id=project_id, permissions=Permissions.GRANT)

    assert action_permissions.get_action_permissions_for_projects(action_id) == {
        project_id: Permissions.GRANT
    }

    action_permissions.set_project_action_permissions(action_id=action_id, project_id=project_id, permissions=Permissions.NONE)

    assert action_permissions.get_action_permissions_for_projects(action_id) == {}

