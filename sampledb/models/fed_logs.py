# coding: utf-8
"""

"""

import enum
import datetime

from .files import File
from .. import db


@enum.unique
class FedUserLogEntryType(enum.Enum):
    OTHER = 0
    IMPORT_USER = 1
    UPDATE_USER = 2
    SHARE_USER = 3
    UPDATE_SHARED_USER = 4
    UPDATE_USER_POLICY = 5
    CREATE_REF_USER = 6


class FedUserLogEntry(db.Model):
    __tablename__ = 'fed_user_log_entries'

    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.Enum(FedUserLogEntryType), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    component_id = db.Column(db.Integer, db.ForeignKey('components.id'), nullable=False)
    data = db.Column(db.JSON, nullable=False)
    utc_datetime = db.Column(db.DateTime, nullable=False)

    def __init__(self, type: FedUserLogEntryType, user_id: int, component_id: int, data: dict, utc_datetime=None):
        self.type = type
        self.user_id = user_id
        self.component_id = component_id
        self.data = data
        if utc_datetime is None:
            utc_datetime = datetime.datetime.utcnow()
        self.utc_datetime = utc_datetime

    def __repr__(self):
        return '<{0}(id={1.id}, type={1.type}, user_id={1.user_id}, utc_datetime={1.utc_datetime}, data={1.data})>'.format(type(self).__name__, self)


@enum.unique
class FedObjectLogEntryType(enum.Enum):
    OTHER = 0
    IMPORT_OBJECT = 1
    UPDATE_OBJECT = 2
    ADD_POLICY = 3
    UPDATE_SHARED_OBJECT = 4
    UPDATE_OBJECT_POLICY = 5
    CREATE_REF_OBJECT = 6


class FedObjectLogEntry(db.Model):
    __tablename__ = 'fed_object_log_entries'

    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.Enum(FedObjectLogEntryType), nullable=False)
    object_id = db.Column(db.Integer, db.ForeignKey('objects_current.object_id'), nullable=False)
    component_id = db.Column(db.Integer, db.ForeignKey('components.id'), nullable=False)
    data = db.Column(db.JSON, nullable=False)
    utc_datetime = db.Column(db.DateTime, nullable=False)

    def __init__(self, type: FedObjectLogEntryType, object_id: int, component_id: int, data: dict, utc_datetime=None):
        self.type = type
        self.object_id = object_id
        self.component_id = component_id
        self.data = data
        if utc_datetime is None:
            utc_datetime = datetime.datetime.utcnow()
        self.utc_datetime = utc_datetime

    def __repr__(self):
        return '<{0}(id={1.id}, type={1.type}, object_id={1.object_id}, utc_datetime={1.utc_datetime}, data={1.data})>'.format(type(self).__name__, self)


@enum.unique
class FedLocationLogEntryType(enum.Enum):
    OTHER = 0
    IMPORT_LOCATION = 1
    UPDATE_LOCATION = 2
    SHARE_LOCATION = 3
    UPDATE_SHARED_LOCATION = 4
    UPDATE_LOCATION_POLICY = 5
    CREATE_REF_LOCATION = 6


class FedLocationLogEntry(db.Model):
    __tablename__ = 'fed_location_log_entries'

    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.Enum(FedLocationLogEntryType), nullable=False)
    location_id = db.Column(db.Integer, db.ForeignKey('locations.id'), nullable=False)
    component_id = db.Column(db.Integer, db.ForeignKey('components.id'), nullable=False)
    data = db.Column(db.JSON, nullable=False)
    utc_datetime = db.Column(db.DateTime, nullable=False)

    def __init__(self, type: FedLocationLogEntryType, location_id: int, component_id: int, data: dict, utc_datetime=None):
        self.type = type
        self.location_id = location_id
        self.component_id = component_id
        self.data = data
        if utc_datetime is None:
            utc_datetime = datetime.datetime.utcnow()
        self.utc_datetime = utc_datetime

    def __repr__(self):
        return '<{0}(id={1.id}, type={1.type}, location_id={1.location_id}, utc_datetime={1.utc_datetime}, data={1.data})>'.format(
            type(self).__name__, self)


@enum.unique
class FedLocationTypeLogEntryType(enum.Enum):
    OTHER = 0
    IMPORT_LOCATION_TYPE = 1
    UPDATE_LOCATION_TYPE = 2
    SHARE_LOCATION_TYPE = 3
    UPDATE_SHARED_LOCATION_TYPE = 4
    UPDATE_LOCATION_TYPE_POLICY = 5
    CREATE_REF_LOCATION_TYPE = 6


class FedLocationTypeLogEntry(db.Model):
    __tablename__ = 'fed_location_type_log_entries'

    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.Enum(FedLocationTypeLogEntryType), nullable=False)
    location_type_id = db.Column(db.Integer, db.ForeignKey('location_types.id'), nullable=False)
    component_id = db.Column(db.Integer, db.ForeignKey('components.id'), nullable=False)
    data = db.Column(db.JSON, nullable=False)
    utc_datetime = db.Column(db.DateTime, nullable=False)

    def __init__(self, type: FedLocationTypeLogEntryType, location_type_id: int, component_id: int, data: dict, utc_datetime=None):
        self.type = type
        self.location_type_id = location_type_id
        self.component_id = component_id
        self.data = data
        if utc_datetime is None:
            utc_datetime = datetime.datetime.utcnow()
        self.utc_datetime = utc_datetime

    def __repr__(self):
        return '<{0}(id={1.id}, type={1.type}, location_type_id={1.location_type_id}, utc_datetime={1.utc_datetime}, data={1.data})>'.format(type(self).__name__, self)


@enum.unique
class FedActionLogEntryType(enum.Enum):
    OTHER = 0
    IMPORT_ACTION = 1
    UPDATE_ACTION = 2
    SHARE_ACTION = 3
    UPDATE_SHARED_ACTION = 4
    UPDATE_ACTION_POLICY = 5
    CREATE_REF_ACTION = 6


class FedActionLogEntry(db.Model):
    __tablename__ = 'fed_action_log_entries'

    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.Enum(FedActionLogEntryType), nullable=False)
    action_id = db.Column(db.Integer, db.ForeignKey('actions.id'), nullable=False)
    component_id = db.Column(db.Integer, db.ForeignKey('components.id'), nullable=False)
    data = db.Column(db.JSON, nullable=False)
    utc_datetime = db.Column(db.DateTime, nullable=False)

    def __init__(self, type: FedActionLogEntryType, action_id: int, component_id: int, data: dict, utc_datetime=None):
        self.type = type
        self.action_id = action_id
        self.component_id = component_id
        self.data = data
        if utc_datetime is None:
            utc_datetime = datetime.datetime.utcnow()
        self.utc_datetime = utc_datetime

    def __repr__(self):
        return '<{0}(id={1.id}, type={1.type}, action_id={1.action_id}, utc_datetime={1.utc_datetime}, data={1.data})>'.format(
            type(self).__name__, self)


@enum.unique
class FedActionTypeLogEntryType(enum.Enum):
    OTHER = 0
    IMPORT_ACTION_TYPE = 1
    UPDATE_ACTION_TYPE = 2
    SHARE_ACTION_TYPE = 3
    UPDATE_SHARED_ACTION_TYPE = 4
    UPDATE_ACTION_TYPE_POLICY = 5
    CREATE_REF_ACTION_TYPE = 6


class FedActionTypeLogEntry(db.Model):
    __tablename__ = 'fed_action_type_log_entries'

    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.Enum(FedActionTypeLogEntryType), nullable=False)
    action_type_id = db.Column(db.Integer, db.ForeignKey('action_types.id'), nullable=False)
    component_id = db.Column(db.Integer, db.ForeignKey('components.id'), nullable=False)
    data = db.Column(db.JSON, nullable=False)
    utc_datetime = db.Column(db.DateTime, nullable=False)

    def __init__(self, type: FedActionTypeLogEntryType, action_type_id: int, component_id: int, data: dict, utc_datetime=None):
        self.type = type
        self.action_type_id = action_type_id
        self.component_id = component_id
        self.data = data
        if utc_datetime is None:
            utc_datetime = datetime.datetime.utcnow()
        self.utc_datetime = utc_datetime

    def __repr__(self):
        return '<{0}(id={1.id}, type={1.type}, action_type_id={1.action_type_id}, utc_datetime={1.utc_datetime}, data={1.data})>'.format(
            type(self).__name__, self)


@enum.unique
class FedInstrumentLogEntryType(enum.Enum):
    OTHER = 0
    IMPORT_INSTRUMENT = 1
    UPDATE_INSTRUMENT = 2
    SHARE_INSTRUMENT = 3
    UPDATE_SHARED_INSTRUMENT = 4
    UPDATE_INSTRUMENT_POLICY = 5
    CREATE_REF_INSTRUMENT = 6


class FedInstrumentLogEntry(db.Model):
    __tablename__ = 'fed_instrument_log_entries'

    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.Enum(FedInstrumentLogEntryType), nullable=False)
    instrument_id = db.Column(db.Integer, db.ForeignKey('instruments.id'), nullable=False)
    component_id = db.Column(db.Integer, db.ForeignKey('components.id'), nullable=False)
    data = db.Column(db.JSON, nullable=False)
    utc_datetime = db.Column(db.DateTime, nullable=False)

    def __init__(self, type: FedInstrumentLogEntryType, instrument_id: int, component_id: int, data: dict, utc_datetime=None):
        self.type = type
        self.instrument_id = instrument_id
        self.component_id = component_id
        self.data = data
        if utc_datetime is None:
            utc_datetime = datetime.datetime.utcnow()
        self.utc_datetime = utc_datetime

    def __repr__(self):
        return '<{0}(id={1.id}, type={1.type}, instrument_id={1.instrument_id}, utc_datetime={1.utc_datetime}, data={1.data})>'.format(
            type(self).__name__, self)


@enum.unique
class FedCommentLogEntryType(enum.Enum):
    OTHER = 0
    IMPORT_COMMENT = 1
    UPDATE_COMMENT = 2
    SHARE_COMMENT = 3
    UPDATE_SHARED_COMMENT = 4
    UPDATE_COMMENT_POLICY = 5
    CREATE_REF_COMMENT = 6


class FedCommentLogEntry(db.Model):
    __tablename__ = 'fed_comment_log_entries'

    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.Enum(FedCommentLogEntryType), nullable=False)
    comment_id = db.Column(db.Integer, db.ForeignKey('comments.id'), nullable=False)
    component_id = db.Column(db.Integer, db.ForeignKey('components.id'), nullable=False)
    data = db.Column(db.JSON, nullable=False)
    utc_datetime = db.Column(db.DateTime, nullable=False)

    def __init__(self, type: FedCommentLogEntryType, comment_id: int, component_id: int, data: dict, utc_datetime=None):
        self.type = type
        self.comment_id = comment_id
        self.component_id = component_id
        self.data = data
        if utc_datetime is None:
            utc_datetime = datetime.datetime.utcnow()
        self.utc_datetime = utc_datetime

    def __repr__(self):
        return '<{0}(id={1.id}, type={1.type}, comment_id={1.comment_id}, utc_datetime={1.utc_datetime}, data={1.data})>'.format(
            type(self).__name__, self)


@enum.unique
class FedFileLogEntryType(enum.Enum):
    OTHER = 0
    IMPORT_FILE = 1
    UPDATE_FILE = 2
    SHARE_FILE = 3
    UPDATE_SHARED_FILE = 4
    UPDATE_FILE_POLICY = 5
    CREATE_REF_FILE = 6


class FedFileLogEntry(db.Model):
    __tablename__ = 'fed_file_log_entries'

    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.Enum(FedFileLogEntryType), nullable=False)
    object_id = db.Column(db.Integer, nullable=False)
    file_id = db.Column(db.Integer, nullable=False)
    component_id = db.Column(db.Integer, db.ForeignKey('components.id'), nullable=False)
    data = db.Column(db.JSON, nullable=False)
    utc_datetime = db.Column(db.DateTime, nullable=False)

    __table_args__ = (db.ForeignKeyConstraint([object_id, file_id], [File.object_id, File.id]), {})

    def __init__(self, type: FedFileLogEntryType, object_id: int, file_id: int, component_id: int, data: dict, utc_datetime=None):
        self.type = type
        self.object_id = object_id
        self.file_id = file_id
        self.component_id = component_id
        self.data = data
        if utc_datetime is None:
            utc_datetime = datetime.datetime.utcnow()
        self.utc_datetime = utc_datetime

    def __repr__(self):
        return '<{0}(id={1.id}, type={1.type}, file_id={1.file_id}, utc_datetime={1.utc_datetime}, data={1.data})>'.format(
            type(self).__name__, self)


@enum.unique
class FedObjectLocationAssignmentLogEntryType(enum.Enum):
    OTHER = 0
    IMPORT_OBJECT_LOCATION_ASSIGNMENT = 1
    UPDATE_OBJECT_LOCATION_ASSIGNMENT = 2
    SHARE_OBJECT_LOCATION_ASSIGNMENT = 3
    UPDATE_SHARED_OBJECT_LOCATION_ASSIGNMENT = 4
    UPDATE_OBJECT_LOCATION_ASSIGNMENT_POLICY = 5
    CREATE_REF_OBJECT_LOCATION_ASSIGNMENT = 6


class FedObjectLocationAssignmentLogEntry(db.Model):
    __tablename__ = 'fed_object_location_assignment_log_entries'

    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.Enum(FedObjectLocationAssignmentLogEntryType), nullable=False)
    object_location_assignment_id = db.Column(db.Integer, db.ForeignKey('object_location_assignments.id'), nullable=False)
    component_id = db.Column(db.Integer, db.ForeignKey('components.id'), nullable=False)
    data = db.Column(db.JSON, nullable=False)
    utc_datetime = db.Column(db.DateTime, nullable=False)

    def __init__(self, type: FedObjectLocationAssignmentLogEntryType, object_location_assignment_id: int, component_id: int, data: dict, utc_datetime=None):
        self.type = type
        self.object_location_assignment_id = object_location_assignment_id
        self.component_id = component_id
        self.data = data
        if utc_datetime is None:
            utc_datetime = datetime.datetime.utcnow()
        self.utc_datetime = utc_datetime

    def __repr__(self):
        return '<{0}(id={1.id}, type={1.type}, object_location_assignment_id={1.object_location_assignment_id}, utc_datetime={1.utc_datetime}, data={1.data})>'.format(type(self).__name__, self)
