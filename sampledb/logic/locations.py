# coding: utf-8
"""
Logic module for locations and object location assignments.

Locations are fully user-defined using a name and a description. Users with
WRITE permissions for an object can assign it to a location with an optional
description for details on where the object is stored.
"""

import collections
import datetime
import typing

from .components import get_component, Component
from .. import db
from . import user_log, object_log, location_log, objects, users, errors, languages, components
from .notifications import create_notification_for_being_assigned_as_responsible_user
from ..models import locations


class LocationType(collections.namedtuple(
    'LocationType',
    [
        'id',
        'name',
        'location_name_singular',
        'location_name_plural',
        'admin_only',
        'enable_parent_location',
        'enable_sub_locations',
        'enable_object_assignments',
        'enable_responsible_users',
        'show_location_log',
        'fed_id',
        'component_id',
        'component'
    ]
)):
    """
    This class provides an immutable wrapper around models.locations.LocationType.
    """

    LOCATION = locations.LocationType.LOCATION

    def __new__(
            cls,
            id: int,
            name: typing.Optional[typing.Dict[str, str]],
            location_name_singular: typing.Optional[typing.Dict[str, str]],
            location_name_plural: typing.Optional[typing.Dict[str, str]],
            admin_only: bool,
            enable_parent_location: bool,
            enable_sub_locations: bool,
            enable_object_assignments: bool,
            enable_responsible_users: bool,
            show_location_log: bool,
            fed_id: typing.Optional[int] = None,
            component_id: typing.Optional[int] = None,
            component: typing.Optional[Component] = None
    ):
        self = super(LocationType, cls).__new__(
            cls,
            id,
            name,
            location_name_singular,
            location_name_plural,
            admin_only,
            enable_parent_location,
            enable_sub_locations,
            enable_object_assignments,
            enable_responsible_users,
            show_location_log,
            fed_id,
            component_id,
            component
        )
        return self

    @classmethod
    def from_database(cls, location_type: locations.LocationType) -> 'LocationType':
        return LocationType(
            id=location_type.id,
            name=location_type.name,
            location_name_singular=location_type.location_name_singular,
            location_name_plural=location_type.location_name_plural,
            admin_only=location_type.admin_only,
            enable_parent_location=location_type.enable_parent_location,
            enable_sub_locations=location_type.enable_sub_locations,
            enable_object_assignments=location_type.enable_object_assignments,
            enable_responsible_users=location_type.enable_responsible_users,
            show_location_log=location_type.show_location_log,
            fed_id=location_type.fed_id,
            component_id=location_type.component_id,
            component=location_type.component
        )


class Location(collections.namedtuple(
    'Location',
    [
        'id',
        'name',
        'description',
        'type_id',
        'type',
        'responsible_users',
        'parent_location_id',
        'fed_id',
        'component',
    ]
)):
    """
    This class provides an immutable wrapper around models.locations.Location.
    """

    def __new__(
            cls,
            id: int,
            name: typing.Optional[typing.Dict[str, str]],
            description: typing.Optional[typing.Dict[str, str]],
            type_id: int,
            type: LocationType,
            responsible_users: typing.List[users.User],
            parent_location_id: typing.Optional[int] = None,
            fed_id: typing.Optional[int] = None,
            component: typing.Optional[Component] = None
    ):
        self = super(Location, cls).__new__(cls, id, name, description, type_id, type, responsible_users, parent_location_id, fed_id, component)
        return self

    @classmethod
    def from_database(cls, location: locations.Location) -> 'Location':
        return Location(
            id=location.id,
            name=location.name,
            description=location.description,
            parent_location_id=location.parent_location_id,
            fed_id=location.fed_id,
            component=location.component,
            type_id=location.type_id,
            type=LocationType.from_database(location.type),
            responsible_users=[
                users.User.from_database(responsible_user)
                for responsible_user in location.responsible_users
            ]
        )


class ObjectLocationAssignment(collections.namedtuple('ObjectLocationAssignment', ['id', 'object_id', 'location_id', 'user_id', 'description', 'utc_datetime', 'responsible_user_id', 'confirmed', 'fed_id', 'component_id', 'declined'])):
    """
    This class provides an immutable wrapper around models.locations.ObjectLocationAssignment.
    """

    def __new__(
            cls,
            id: int,
            object_id: int,
            location_id: int,
            user_id: int,
            description: typing.Optional[typing.Dict[str, str]],
            utc_datetime: datetime.datetime,
            responsible_user_id: int,
            confirmed: bool,
            fed_id: typing.Optional[int] = None,
            component_id: typing.Optional[int] = None,
            declined: bool = False
    ):
        self = super(ObjectLocationAssignment, cls).__new__(cls, id, object_id, location_id, user_id, description, utc_datetime, responsible_user_id, confirmed, fed_id, component_id, declined)
        return self

    @classmethod
    def from_database(cls, object_location_assignment: locations.ObjectLocationAssignment) -> 'ObjectLocationAssignment':
        return ObjectLocationAssignment(
            id=object_location_assignment.id,
            object_id=object_location_assignment.object_id,
            location_id=object_location_assignment.location_id,
            responsible_user_id=object_location_assignment.responsible_user_id,
            user_id=object_location_assignment.user_id,
            description=object_location_assignment.description,
            utc_datetime=object_location_assignment.utc_datetime,
            confirmed=object_location_assignment.confirmed,
            fed_id=object_location_assignment.fed_id,
            component_id=object_location_assignment.component_id,
            declined=object_location_assignment.declined
        )


def create_location(
        name: typing.Optional[typing.Dict[str, str]],
        description: typing.Optional[typing.Dict[str, str]],
        parent_location_id: typing.Optional[int],
        user_id: typing.Optional[int],
        type_id: int,
        *,
        fed_id: typing.Optional[int] = None,
        component_id: typing.Optional[int] = None
) -> Location:
    """
    Create a new location.

    :param name: the names for the new location in a dict. Keys are the language codes and values are the names.
    :param description: the descriptions for the new location.
        Keys are the language code and values are the descriptions.
    :param parent_location_id: the optional parent location ID for the new location
    :param user_id: the ID of an existing user
    :param fed_id: the federation ID of the location
    :param component_id: origin component ID
    :param type_id: the ID of an existing location type
    :return: the created location
    :raise errors.LocationDoesNotExistError: when no location with the given
        parent location ID exists
    :raise errors.UserDoesNotExistError: when no user with the given user ID
        exists
    :raise errors.LocationTypeDoesNotExistError: when no location type with the
        given location type ID exists
    """

    if (component_id is None) != (fed_id is None) or (component_id is None and (name is None or description is None or user_id is None)):
        raise TypeError('Invalid parameter combination.')

    if name is not None:
        if isinstance(name, str):
            name = {
                'en': name
            }
        assert isinstance(name, dict)
        if component_id is None:
            name = languages.filter_translations(name)

        # if a name is provided, there should be an english translation
        if 'en' not in name:
            raise errors.MissingEnglishTranslationError()

    if description is not None:
        if isinstance(description, str):
            description = {
                'en': description
            }
        assert isinstance(description, dict)
        if component_id is None:
            description = languages.filter_translations(description)

    # ensure the user exists
    if user_id is not None:
        users.get_user(user_id)
    if parent_location_id is not None:
        # ensure parent location exists
        get_location(parent_location_id)
    if component_id is not None:
        # ensure that the component can be found
        components.get_component(component_id)
    if type_id is not None:
        # ensure location type exists
        get_location_type(type_id)
    location = locations.Location(
        name=name,
        description=description,
        parent_location_id=parent_location_id,
        fed_id=fed_id,
        component_id=component_id,
        type_id=type_id
    )
    db.session.add(location)
    db.session.commit()
    if component_id is None:
        user_log.create_location(user_id, location.id)
    location_log.create_location(user_id, location.id)
    return Location.from_database(location)


def update_location(
        location_id: int,
        name: typing.Optional[typing.Dict[str, str]],
        description: dict,
        parent_location_id: typing.Optional[int],
        user_id: typing.Optional[int],
        type_id: int
) -> None:
    """
    Update a location's information.

    :param location_id: the ID of the location to update
    :param name: the new names for the location in a dict. Keys are the language codes and the values the new names
    :param description: the descriptions for the location.
        Keys are the language code and the values the new descriptions.
    :param parent_location_id: the optional parent location id for the location
    :param user_id: the ID of an existing user
    :param type_id: the ID of an existing location type
    :raise errors.LocationDoesNotExistError: when no location with the given
        location ID or parent location ID exists
    :raise errors.CyclicLocationError: when location ID is an ancestor of
        parent location ID
    :raise errors.UserDoesNotExistError: when no user with the given user ID
        exists
    :raise errors.MissingEnglishTranslationError: if no english name is given
    :raise errors.LanguageDoesNotExistError: if an unknown language code is
        used
    :raise errors.LocationTypeDoesNotExistError: when no location type with the
        given location type ID exists
    """
    location = locations.Location.query.filter_by(id=location_id).first()
    if location is None:
        raise errors.LocationDoesNotExistError()

    if name is not None:
        assert isinstance(name, dict)
        if location.component_id is None:
            name = languages.filter_translations(name)

        # if a name is provided, there should be an english translation
        if 'en' not in name:
            raise errors.MissingEnglishTranslationError()

    if description is not None:
        assert isinstance(description, dict)
        if location.component_id is None:
            description = languages.filter_translations(description)

    # ensure the user exists
    if user_id is not None:
        users.get_user(user_id)
    if parent_location_id is not None:
        if location_id == parent_location_id or location_id in _get_location_ancestors(parent_location_id):
            raise errors.CyclicLocationError()
    if type_id is not None:
        # ensure location type exists
        get_location_type(type_id)
    location.name = name
    location.description = description
    location.parent_location_id = parent_location_id
    location.type_id = type_id
    db.session.add(location)
    db.session.commit()
    if user_id is not None:
        user_log.update_location(user_id, location.id)
    location_log.update_location(user_id, location.id)


def get_location(location_id: int, component_id: typing.Optional[int] = None) -> Location:
    """
    Get a location.

    :param location_id: the ID of an existing location
    :param component_id: the ID of an existing component, or None
    :raise errors.LocationDoesNotExistError: when no location with the given
        ID exists
    :return: the location with the given location ID
    """
    if component_id is None:
        location = locations.Location.query.filter_by(id=location_id).first()
    else:
        location = locations.Location.query.filter_by(fed_id=location_id, component_id=component_id).first()
    if location is None:
        if component_id is not None:
            get_component(component_id)
        raise errors.LocationDoesNotExistError()
    return Location.from_database(location)


def get_locations() -> typing.List[Location]:
    """
    Get the list of all locations.

    :return: the list of all locations
    """
    return [
        Location.from_database(location)
        for location in locations.Location.query.all()
    ]


def get_locations_tree() -> typing.Tuple[typing.Dict[int, Location], typing.Any]:
    """
    Get the list of locations as a tree.

    :return: the list of all locations and the locations tree
    """
    locations = get_locations()
    locations_map = {
        location.id: location
        for location in locations
    }
    locations_tree = {}
    locations_tree_helper = {None: locations_tree}
    unvisited_locations = locations
    while unvisited_locations:
        locations = unvisited_locations
        unvisited_locations = []
        for location in locations:
            if location.parent_location_id in locations_tree_helper:
                locations_subtree = locations_tree_helper[location.parent_location_id]
                locations_subtree[location.id] = {}
                locations_tree_helper[location.id] = locations_subtree[location.id]
            else:
                unvisited_locations.append(location)
    return locations_map, locations_tree


def _get_location_ancestors(location_id: int) -> typing.List[int]:
    """
    Get the list of all ancestor location IDs.

    :param location_id: the ID of an existing location
    :return: the list of all ancestor location IDs
    :raise errors.LocationDoesNotExistError: when no location with the given
        location ID exists
    """
    ancestor_location_ids = []
    while location_id is not None:
        ancestor_location_ids.append(location_id)
        location_id = get_location(location_id).parent_location_id
    return ancestor_location_ids[1:]


def assign_location_to_object(
        object_id: int,
        location_id: typing.Optional[int],
        responsible_user_id: typing.Optional[int],
        user_id: int,
        description: typing.Optional[typing.Dict[str, str]]
) -> None:
    """
    Assign a location to an object.

    :param object_id: the ID of an existing object
    :param location_id: the ID of an existing location
    :param responsible_user_id: the ID of an existing user
    :param user_id: the ID of an existing user
    :param description: a description of where the object was stored in a dict.
        The keys are the lang codes and the values are the descriptions.
    :raise errors.ObjectDoesNotExistError: when no object with the given
        object ID exists
    :raise errors.LocationDoesNotExistError: when no location with the given
        location ID exists
    :raise errors.UserDoesNotExistError: when no user with the given user ID
        or responsible user ID exists
    """

    if description is not None:
        if isinstance(description, str):
            description = {
                'en': description
            }
        assert isinstance(description, dict)
        description = languages.filter_translations(description)

    # ensure the object exists
    objects.get_object(object_id)
    if location_id is not None:
        # ensure the location exists
        get_location(location_id)
    # ensure the user exists
    users.get_user(user_id)
    object_location_assignment = locations.ObjectLocationAssignment(
        object_id=object_id,
        location_id=location_id,
        responsible_user_id=responsible_user_id,
        user_id=user_id,
        description=description,
        utc_datetime=datetime.datetime.utcnow(),
        confirmed=(user_id == responsible_user_id),
        declined=False
    )
    db.session.add(object_location_assignment)
    db.session.commit()
    if responsible_user_id is not None:
        users.get_user(responsible_user_id)
        if user_id != responsible_user_id:
            create_notification_for_being_assigned_as_responsible_user(object_location_assignment.id)
    object_log.assign_location(user_id, object_id, object_location_assignment.id)
    user_log.assign_location(user_id, object_location_assignment.id)
    previous_object_location_assignment = locations.ObjectLocationAssignment.query.filter_by(
        object_id=object_id
    ).order_by(
        db.desc(locations.ObjectLocationAssignment.utc_datetime)
    ).offset(1).first()
    if previous_object_location_assignment is not None:
        previous_location_id = previous_object_location_assignment.location_id
    else:
        previous_location_id = None
    if location_id is not None and location_id == previous_location_id:
        location_log.change_object(user_id, location_id, object_location_assignment.id)
    else:
        if location_id is not None:
            location_log.add_object(user_id, location_id, object_location_assignment.id)
        if previous_location_id is not None:
            location_log.remove_object(user_id, previous_location_id, object_location_assignment.id)


def create_fed_assignment(
        fed_id: int,
        component_id: int,
        object_id: int,
        location_id: typing.Optional[int],
        responsible_user_id: typing.Optional[int],
        user_id: typing.Optional[int],
        description: typing.Optional[typing.Dict[str, str]],
        utc_datetime: typing.Optional[datetime.datetime],
        confirmed: typing.Optional[bool],
        declined: bool = False
) -> ObjectLocationAssignment:
    if description is not None:
        if isinstance(description, str):
            description = {
                'en': description
            }
        assert isinstance(description, dict)
        description = languages.filter_translations(description)

    objects.get_object(object_id)
    # ensure the component exists
    get_component(component_id)
    if location_id is not None:
        # ensure the location exists
        get_location(location_id)
    if user_id is not None:
        users.get_user(user_id)
    if responsible_user_id is not None:
        users.get_user(responsible_user_id)
    object_location_assignment = locations.ObjectLocationAssignment(
        object_id=object_id,
        location_id=location_id,
        responsible_user_id=responsible_user_id,
        user_id=user_id,
        description=description,
        utc_datetime=utc_datetime,
        confirmed=confirmed,
        declined=declined,
        fed_id=fed_id,
        component_id=component_id
    )
    db.session.add(object_location_assignment)
    db.session.commit()
    return object_location_assignment


def get_object_location_assignments(object_id: int) -> typing.List[ObjectLocationAssignment]:
    """
    Get a list of all object location assignments for an object.

    :param object_id: the ID of an existing object
    :return: the list of object location assignments
    :raise errors.ObjectDoesNotExistError: when no object with the given
        object ID exists
    """
    # ensure the object exists
    objects.get_object(object_id)
    object_location_assignments = locations.ObjectLocationAssignment.query.filter_by(object_id=object_id).order_by(locations.ObjectLocationAssignment.utc_datetime).all()
    return [
        ObjectLocationAssignment.from_database(object_location_assignment)
        for object_location_assignment in object_location_assignments
    ]


def get_fed_object_location_assignment(fed_id: int, component_id: int):
    object_location_assignment = locations.ObjectLocationAssignment.query.filter_by(fed_id=fed_id, component_id=component_id).first()
    return object_location_assignment


def get_current_object_location_assignment(object_id: int) -> typing.Optional[ObjectLocationAssignment]:
    """
    Get the current location assignment for an object.

    :param object_id: the ID of an existing object
    :return: the object location assignment
    :raise errors.ObjectDoesNotExistError: when no object with the given
        object ID exists
    """
    # ensure the object exists
    objects.get_object(object_id)
    object_location_assignment = locations.ObjectLocationAssignment.query.filter_by(object_id=object_id).order_by(locations.ObjectLocationAssignment.utc_datetime.desc()).first()
    if object_location_assignment is not None:
        object_location_assignment = ObjectLocationAssignment.from_database(object_location_assignment)
    return object_location_assignment


def get_object_location_assignment(object_location_assignment_id: int) -> ObjectLocationAssignment:
    """
    Get an object location assignment with a given ID.

    :param object_location_assignment_id: the ID of an existing object location
        assignment
    :return: the object location assignment
    :raise errors.ObjectLocationAssignmentDoesNotExistError: when no object
        location assignment with the given object location assignment ID exists
    """
    object_location_assignment = locations.ObjectLocationAssignment.query.filter_by(id=object_location_assignment_id).first()
    if object_location_assignment is None:
        raise errors.ObjectLocationAssignmentDoesNotExistError()
    return object_location_assignment


def any_objects_at_location(location_id: int) -> bool:
    """
    Get whether there are any objects currently assigned to a location.

    :param location_id: the ID of an existing location
    :return: whether there are any objects assigned to the location
    :raise errors.LocationDoesNotExistError: when no location with the given
        location ID exists
    """
    # ensure the location exists
    get_location(location_id)
    object_location_assignments = locations.ObjectLocationAssignment.query.filter_by(location_id=location_id).all()
    for object_location_assignment in object_location_assignments:
        object_id = object_location_assignment.object_id
        if get_current_object_location_assignment(object_id).location_id == location_id:
            return True
    return False


def get_object_ids_at_location(location_id: int) -> typing.Set[int]:
    """
    Get a list of all objects currently assigned to a location.

    :param location_id: the ID of an existing location
    :return: the list of object IDs assigned to the location
    :raise errors.LocationDoesNotExistError: when no location with the given
        location ID exists
    """
    # ensure the location exists
    get_location(location_id)
    object_location_assignments = locations.ObjectLocationAssignment.query.filter_by(location_id=location_id).all()
    object_ids = set()
    for object_location_assignment in object_location_assignments:
        object_id = object_location_assignment.object_id
        if get_current_object_location_assignment(object_id).location_id == location_id:
            object_ids.add(object_id)
    return object_ids


def confirm_object_responsibility(object_location_assignment_id: int) -> None:
    """
    Confirm an object location assignment.

    :param object_location_assignment_id: the ID of an existing object location
        assignment
    :raise errors.ObjectLocationAssignmentDoesNotExistError: when no object
        location assignment with the given object location assignment ID exists
    """
    object_location_assignment = get_object_location_assignment(object_location_assignment_id)
    if object_location_assignment.declined:
        raise errors.ObjectLocationAssignmentAlreadyDeclinedError()
    object_location_assignment.confirmed = True
    db.session.add(object_location_assignment)
    db.session.commit()


def decline_object_responsibility(object_location_assignment_id: int) -> None:
    """
    Decline responsibility for an object.

    :param object_location_assignment_id: the ID of an existing object location
        assignment
    :raise errors.ObjectLocationAssignmentDoesNotExistError: when no object
        location assignment with the given object location assignment ID exists
    """
    object_location_assignment = get_object_location_assignment(object_location_assignment_id)
    if object_location_assignment.confirmed:
        raise errors.ObjectLocationAssignmentAlreadyConfirmedError()
    object_location_assignment.declined = True
    db.session.add(object_location_assignment)
    db.session.commit()


def create_location_type(
        name: typing.Optional[typing.Dict[str, str]],
        location_name_singular: typing.Optional[typing.Dict[str, str]],
        location_name_plural: typing.Optional[typing.Dict[str, str]],
        admin_only: bool,
        enable_parent_location: bool,
        enable_sub_locations: bool,
        enable_object_assignments: bool,
        enable_responsible_users: bool,
        show_location_log: bool,
        fed_id: typing.Optional[int] = None,
        component_id: typing.Optional[int] = None
) -> LocationType:
    """
    Create a new location type.

    :param name: the names for the new location type in a dict. Keys are the
        language codes and values are the names.
    :param location_name_singular: the names for single locations of this type in a dict
    :param location_name_plural: the names for multiple locations of this type in a dict
    :param admin_only: whether only administrators can create locations of this type
    :param enable_parent_location: whether locations of this type may have a parent location
    :param enable_sub_locations: whether locations of this type may have sub locations
    :param enable_object_assignments: whether objects may be assigned to locations of this type
    :param enable_responsible_users: whether locations of this type may have responsible users
    :param show_location_log: whether the location log should be shown for locations of this type
    :param fed_id: the federation ID of the location type
    :param component_id: origin component ID
    :return: the created location type
    """
    location_type = locations.LocationType(
        name=name,
        location_name_singular=location_name_singular,
        location_name_plural=location_name_plural,
        admin_only=admin_only,
        enable_parent_location=enable_parent_location,
        enable_sub_locations=enable_sub_locations,
        enable_object_assignments=enable_object_assignments,
        enable_responsible_users=enable_responsible_users,
        show_location_log=show_location_log,
        fed_id=fed_id,
        component_id=component_id
    )
    db.session.add(location_type)
    db.session.commit()
    return location_type


def update_location_type(
        location_type_id: int,
        name: typing.Optional[typing.Dict[str, str]],
        location_name_singular: typing.Optional[typing.Dict[str, str]],
        location_name_plural: typing.Optional[typing.Dict[str, str]],
        admin_only: bool,
        enable_parent_location: bool,
        enable_sub_locations: bool,
        enable_object_assignments: bool,
        enable_responsible_users: bool,
        show_location_log: bool,
) -> None:
    """
    Create a new location type.

    :param location_type_id: the ID of an existing location type
    :param name: the names for the new location type in a dict. Keys are the
        language codes and values are the names.
    :param location_name_singular: the names for single locations of this type in a dict
    :param location_name_plural: the names for multiple locations of this type in a dict
    :param admin_only: whether only administrators can create locations of this type
    :param enable_parent_location: whether locations of this type may have a parent location
    :param enable_sub_locations: whether locations of this type may have sub locations
    :param enable_object_assignments: whether objects may be assigned to locations of this type
    :param enable_responsible_users: whether locations of this type may have responsible users
    :param show_location_log: whether the location log should be shown for locations of this type
    :raise errors.LocationTypeDoesNotExistError: if no location type with the
        given ID exists
    """
    location_type = locations.LocationType.query.get(location_type_id)
    if location_type is None:
        raise errors.LocationTypeDoesNotExistError()
    location_type.name = name
    location_type.location_name_singular = location_name_singular
    location_type.location_name_plural = location_name_plural
    location_type.admin_only = admin_only
    location_type.enable_parent_location = enable_parent_location
    location_type.enable_sub_locations = enable_sub_locations
    location_type.enable_object_assignments = enable_object_assignments
    location_type.enable_responsible_users = enable_responsible_users
    location_type.show_location_log = show_location_log
    db.session.add(location_type)
    db.session.commit()


def get_location_type(
        location_type_id: int,
        component_id: typing.Optional[int] = None
) -> locations.LocationType:
    """
    Get a location type.

    :param location_type_id: the ID of an existing location type
    :param component_id: the ID of an existing component, or None
    :raise errors.LocationTypeDoesNotExistError: when no location type with
        the given ID exists
    :return: the location type with the given location type ID
    """
    if component_id is None:
        location_type = locations.LocationType.query.filter_by(id=location_type_id).first()
    else:
        location_type = locations.LocationType.query.filter_by(fed_id=location_type_id, component_id=component_id).first()
    if location_type is None:
        if component_id is not None:
            get_component(component_id)
        raise errors.LocationTypeDoesNotExistError()
    return LocationType.from_database(location_type)


def get_location_types() -> typing.List[locations.LocationType]:
    """
    Get all location types.

    :return: the list of all location types
    """
    location_types = locations.LocationType.query.order_by(db.asc(locations.LocationType.id)).all()
    return [
        LocationType.from_database(location_type)
        for location_type in location_types
    ]


def set_location_responsible_users(
        location_id: int,
        responsible_user_ids: typing.List[int]
) -> None:
    """
    Set the responsible users for a location.

    :param location_id: the ID of an existing location
    :param responsible_user_ids: a list of user IDs
    :raise errors.LocationDoesNotExistError: when no location with the given
        location ID exists
    :raise errors.UserDoesNotExistError: when no user with the given
        user ID exists
    """
    location = locations.Location.query.filter_by(id=location_id).first()
    if location is None:
        raise errors.LocationDoesNotExistError()
    location.responsible_users.clear()
    for user_id in responsible_user_ids:
        user = users.get_mutable_user(user_id)
        location.responsible_users.append(user)
    db.session.add(location)
    db.session.commit()
