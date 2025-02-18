# coding: utf-8
"""
Permissions

Various resources in SampleDB, such as objects and actions, have a unified
permission system that controls how each user can interact with them.

There are three general types of permissions for each resource:
 - READ, being able to access the resource and its information,
 - WRITE, being able to make changes to the resources, and
 - GRANT, being able to grant permissions to other users.

A user may get permissions in several ways:
- they may be implicitly granted permissions along with all other users
- they may be explicitly granted permissions as individual users
- they may be transitively granted permissions as member of a group
- they may be transitively granted permissions as member of a project
- they may be an administrator utilizing administrator permissions

Depending on the type of resource, there may be additional ways of getting
permissions, e.g. by being an instrument responsible user.

Even if a user has been granted WRITE or GRANT permissions in some of the ways
listed above, they might be limited to READ permissions only if they have been
marked as read only users.

The ResourcePermissions class in this module is meant to be used by modules
for the individual resource types, as a base to avoid code duplication.
"""
import typing

from . import users, groups, projects
from ..models import Permissions
from .. import db


class ResourcePermissions(object):
    def __init__(
            self,
            resource_id_name: str,
            all_user_permissions_table: typing.Any,
            anonymous_user_permissions_table: typing.Any,
            user_permissions_table: typing.Any,
            group_permissions_table: typing.Any,
            project_permissions_table: typing.Any,
            check_resource_exists: typing.Callable[[int], typing.Any]
    ) -> None:
        self._resource_id_name = resource_id_name
        self._all_user_permissions_table = all_user_permissions_table
        self._anonymous_user_permissions_table = anonymous_user_permissions_table
        self._user_permissions_table = user_permissions_table
        self._group_permissions_table = group_permissions_table
        self._project_permissions_table = project_permissions_table
        self._check_resource_exists = check_resource_exists

    def _get_user_independent_permissions(
            self,
            resource_id: int,
            table: typing.Any
    ) -> Permissions:
        """
        Return the permissions for a specific resource from a user independent table.

        :param resource_id: the ID of an existing resource
        :param table: the permissions table
        :return: the user independent permissions
        """
        if table is None:
            return Permissions.NONE
        permissions = table.query.filter_by(**{self._resource_id_name: resource_id}).first()
        if permissions is None:
            self._check_resource_exists(resource_id)
            return Permissions.NONE
        return permissions.permissions

    def _set_user_independent_permissions(
            self,
            resource_id: int,
            permissions: Permissions,
            table: typing.Any
    ) -> None:
        """
        Set the permissions for a specific resource in a user independent table.

        :param resource_id: the ID of an existing resource
        :param permissions: the user independent permissions
        :param table: the permissions table
        """
        self._check_resource_exists(resource_id)

        if table is None:
            return

        if permissions == Permissions.NONE:
            table.query.filter_by(**{self._resource_id_name: resource_id}).delete()
        else:
            all_user_permissions = table.query.filter_by(**{self._resource_id_name: resource_id}).first()
            if all_user_permissions is None:
                all_user_permissions = table(permissions=permissions, **{self._resource_id_name: resource_id})
            else:
                all_user_permissions.permissions = permissions
            db.session.add(all_user_permissions)
        db.session.commit()

    def get_permissions_for_all_users(
            self,
            resource_id: int
    ) -> Permissions:
        """
        Return the permissions all users have for a specific resource.

        :param resource_id: the ID of an existing resource
        :return: the permissions for all users
        """
        return self._get_user_independent_permissions(resource_id, self._all_user_permissions_table)

    def set_permissions_for_all_users(
            self,
            resource_id: int,
            permissions: Permissions
    ) -> None:
        """
        Set the permissions all users have for a specific resource.

        :param resource_id: the ID of an existing resource
        :param permissions: the permissions for all users
        """
        self._set_user_independent_permissions(resource_id, permissions, self._all_user_permissions_table)

    def get_permissions_for_anonymous_users(
            self,
            resource_id: int
    ) -> Permissions:
        """
        Return the permissions anonymous users have for a specific resource.

        :param resource_id: the ID of an existing resource
        :return: the permissions for anonymous users
        """
        return self._get_user_independent_permissions(resource_id, self._anonymous_user_permissions_table)

    def set_permissions_for_anonymous_users(
            self,
            resource_id: int,
            permissions: Permissions
    ) -> None:
        """
        Set the permissions all users have for a specific resource.

        :param resource_id: the ID of an existing resource
        :param permissions: the permissions for anonymous users
        """
        self._set_user_independent_permissions(resource_id, permissions, self._anonymous_user_permissions_table)

    def get_permissions_for_users(
            self,
            resource_id: int,
            *,
            include_all_users: bool = False,
            include_groups: bool = False,
            include_projects: bool = False,
            include_admin_permissions: bool = False,
            limit_readonly_users: bool = False,
            additional_permissions: typing.Optional[typing.Dict[int, Permissions]] = None
    ) -> typing.Dict[int, Permissions]:
        """
        Get permissions for users for a specific resource.

        This does not consider modifications to user permissions other than
        those explicitly included using the function parameters.

        :param resource_id: the ID of an existing resource
        :param include_all_users: whether permissions for all users should be included
        :param include_groups: whether groups that the users are members of should be included
        :param include_projects: whether projects that the users are members of should be included
        :param include_admin_permissions: whether admin permissions should be included
        :param limit_readonly_users: whether readonly users should be limited to READ permissions
        :param additional_permissions: additional permissions to assume
        :return: a dict mapping users IDs to permissions
        """
        self._check_resource_exists(resource_id)

        permissions_for_users = {}
        if additional_permissions is not None:
            permissions_for_users = additional_permissions.copy()

        for user_permissions in self._user_permissions_table.query.filter_by(**{self._resource_id_name: resource_id}).all():
            permissions_for_users[user_permissions.user_id] = max(permissions_for_users.get(user_permissions.user_id, Permissions.NONE), user_permissions.permissions)

        if include_all_users:
            permissions_for_all_users = self.get_permissions_for_all_users(resource_id=resource_id)
            if permissions_for_all_users != Permissions.NONE:
                for user in users.get_users():
                    permissions_for_users[user.id] = max(permissions_for_users.get(user.id, Permissions.NONE), permissions_for_all_users)

        if include_groups:
            permissions_for_groups = self.get_permissions_for_groups(resource_id=resource_id, include_projects=include_projects)
            for group_id, group_permissions in permissions_for_groups.items():
                for user_id in groups.get_group_member_ids(group_id):
                    permissions_for_users[user_id] = max(permissions_for_users.get(user_id, Permissions.NONE), group_permissions)

        if include_projects:
            permissions_for_projects = self.get_permissions_for_projects(resource_id=resource_id)
            for project_id, project_permissions in permissions_for_projects.items():
                for user_id, member_permissions in projects.get_project_member_user_ids_and_permissions(project_id, include_groups=include_groups).items():
                    permissions_for_users[user_id] = max(permissions_for_users.get(user_id, Permissions.NONE), min(member_permissions, project_permissions))

        if include_admin_permissions:
            for user in users.get_administrators():
                if not user.has_admin_permissions:
                    # skip admins who do not use admin permissions
                    continue
                permissions_for_users[user.id] = Permissions.GRANT

        if limit_readonly_users:
            for user in users.get_users():
                if user.is_readonly and user.id in permissions_for_users:
                    permissions_for_users[user.id] = min(Permissions.READ, permissions_for_users[user.id])

        return {
            user_id: permissions
            for user_id, permissions in permissions_for_users.items()
            if permissions != Permissions.NONE
        }

    def set_permissions_for_user(
            self,
            resource_id: int,
            user_id: int,
            permissions: Permissions
    ) -> None:
        """
        Set the permissions for a user for a specific resource.

        Clear the permissions if called with Permissions.NONE

        :param resource_id: the ID of an existing resource
        :param user_id: the ID of an existing user
        :param permissions: the new permissions
        """
        self._check_resource_exists(resource_id)
        # ensure that the user can be found
        users.get_user(user_id)

        if permissions == Permissions.NONE:
            self._user_permissions_table.query.filter_by(user_id=user_id, **{self._resource_id_name: resource_id}).delete()
        else:
            user_permissions = self._user_permissions_table.query.filter_by(user_id=user_id, **{self._resource_id_name: resource_id}).first()
            if user_permissions is None:
                user_permissions = self._user_permissions_table(user_id=user_id, permissions=permissions, **{self._resource_id_name: resource_id})
            else:
                user_permissions.permissions = permissions
            db.session.add(user_permissions)
        db.session.commit()

    def get_permissions_for_groups(
            self,
            resource_id: int,
            *,
            include_projects: bool = False
    ) -> typing.Dict[int, Permissions]:
        """
        Get permissions for groups for a specific resource.

        This does not consider modifications to user permissions other than
        those explicitly included using the function parameters.

        :param resource_id: the ID of an existing resource
        :param include_projects: whether projects that the groups are members of should be included
        :return: a dict mapping group IDs to permissions
        """
        self._check_resource_exists(resource_id)

        permissions_for_groups = {}
        for group_permissions in self._group_permissions_table.query.filter_by(**{self._resource_id_name: resource_id}).all():
            permissions_for_groups[group_permissions.group_id] = group_permissions.permissions

        if include_projects:
            permissions_for_projects = self.get_permissions_for_projects(resource_id=resource_id)
            for project_id, project_permissions in permissions_for_projects.items():
                for group_id, member_permissions in projects.get_project_member_group_ids_and_permissions(project_id).items():
                    permissions_for_groups[group_id] = max(permissions_for_groups.get(group_id, Permissions.NONE), min(member_permissions, project_permissions))
        return {
            group_id: permissions
            for group_id, permissions in permissions_for_groups.items()
            if permissions != Permissions.NONE
        }

    def set_permissions_for_group(
            self,
            resource_id: int,
            group_id: int,
            permissions: Permissions
    ) -> None:
        """
        Set the permissions for a group for a specific resource.

        Clear the permissions if called with Permissions.NONE.

        :param resource_id: the ID of an existing resource
        :param group_id: the ID of an existing group
        :param permissions: the new permissions
        """
        self._check_resource_exists(resource_id)
        # ensure that the group can be found
        groups.get_group(group_id)

        if permissions == Permissions.NONE:
            self._group_permissions_table.query.filter_by(group_id=group_id, **{self._resource_id_name: resource_id}).delete()
        else:
            group_permissions = self._group_permissions_table.query.filter_by(group_id=group_id, **{self._resource_id_name: resource_id}).first()
            if group_permissions is None:
                group_permissions = self._group_permissions_table(group_id=group_id, permissions=permissions, **{self._resource_id_name: resource_id})
            else:
                group_permissions.permissions = permissions
            db.session.add(group_permissions)
        db.session.commit()

    def get_permissions_for_projects(
            self,
            resource_id: int
    ) -> typing.Dict[int, Permissions]:
        """
        Get permissions for projects for a specific resource.

        :param resource_id: the ID of an existing resource
        :return: a dict mapping project IDs to permissions
        """
        self._check_resource_exists(resource_id)

        permissions_for_projects = {}
        for project_permissions in self._project_permissions_table.query.filter_by(**{self._resource_id_name: resource_id}).all():
            permissions_for_projects[project_permissions.project_id] = project_permissions.permissions
        return {
            project_id: permissions
            for project_id, permissions in permissions_for_projects.items()
            if permissions != Permissions.NONE
        }

    def set_permissions_for_project(
            self,
            resource_id: int,
            project_id: int,
            permissions: Permissions
    ) -> None:
        """
        Set the permissions for a project for a specific resource.

        Clear the permissions if called with Permissions.NONE.

        :param resource_id: the ID of an existing resource
        :param project_id: the ID of an existing project
        :param permissions: the new permissions
        """
        self._check_resource_exists(resource_id)
        # ensure that the project can be found
        projects.get_project(project_id)

        if permissions == Permissions.NONE:
            self._project_permissions_table.query.filter_by(project_id=project_id, **{self._resource_id_name: resource_id}).delete()
        else:
            project_permissions = self._project_permissions_table.query.filter_by(project_id=project_id, **{self._resource_id_name: resource_id}).first()
            if project_permissions is None:
                project_permissions = self._project_permissions_table(project_id=project_id, permissions=permissions, **{self._resource_id_name: resource_id})
            else:
                project_permissions.permissions = permissions
            db.session.add(project_permissions)
        db.session.commit()

    def get_permissions_for_user(
            self,
            resource_id: int,
            user_id: typing.Optional[int],
            *,
            include_all_users: bool = False,
            include_anonymous_users: bool = False,
            include_groups: bool = False,
            include_projects: bool = False,
            include_admin_permissions: bool = False,
            limit_readonly_users: bool = False,
            additional_permissions: Permissions = Permissions.NONE
    ) -> Permissions:
        """
        Get combined permissions for a specific user for a specific resource.

        This does not consider instrument responsible users or other resource
        type dependent modifications to user permissions. Depending on the
        given arguments, it will however consider transitive permissions,
        admin permissions and readonly users.

        :param resource_id: the ID of an existing resource
        :param user_id: the ID of an existing user
        :param include_all_users: whether permissions for all users should be included
        :param include_anonymous_users: whether permissions for anonymous users should be included
        :param include_groups: whether groups that the users are members of should be included
        :param include_projects: whether projects that the users are members of should be included
        :param include_admin_permissions: whether admin permissions should be included
        :param limit_readonly_users: whether readonly users should be limited to READ permissions
        :param additional_permissions: additional permissions to assume for this user
        :return: the combined permissions for the given user
        """
        self._check_resource_exists(resource_id)

        permissions = additional_permissions
        max_permissions = Permissions.GRANT

        if max_permissions not in permissions and include_anonymous_users:
            permissions = max(permissions, self.get_permissions_for_anonymous_users(resource_id))

        if user_id is None:
            return permissions

        # ensure that the user can be found
        user = users.get_user(user_id)

        # readonly users may never have more than READ permissions
        if user.is_readonly and limit_readonly_users:
            max_permissions = Permissions.READ

        if max_permissions not in permissions and include_admin_permissions:
            # administrators have GRANT permissions if they use admin permissions
            if user.has_admin_permissions:
                permissions = max(permissions, Permissions.GRANT)

        if max_permissions not in permissions and include_all_users:
            permissions = max(permissions, self.get_permissions_for_all_users(resource_id))

        if max_permissions not in permissions:
            user_permissions = self._user_permissions_table.query.filter_by(user_id=user_id, **{self._resource_id_name: resource_id}).first()
            if user_permissions is not None:
                permissions = max(permissions, user_permissions.permissions)

        if max_permissions not in permissions and include_groups:
            group_permissions = self.get_permissions_for_groups(resource_id=resource_id)
            for group in groups.get_user_groups(user_id):
                permissions = max(permissions, group_permissions.get(group.id, Permissions.NONE))

        if max_permissions not in permissions and include_projects:
            project_permissions = self.get_permissions_for_projects(resource_id=resource_id)
            for project in projects.get_user_projects(user_id, include_groups=include_groups):
                max_project_permissions = projects.get_user_project_permissions(project_id=project.id, user_id=user_id, include_groups=include_groups)
                permissions = max(permissions, min(max_project_permissions, project_permissions.get(project.id, Permissions.NONE)))

        return permissions

    def copy_permissions(self, source_resource_id: int, target_resource_id: int) -> None:
        self._check_resource_exists(source_resource_id)
        self._check_resource_exists(target_resource_id)

        # clear current permissions for the target resource
        self._all_user_permissions_table.query.filter_by(**{self._resource_id_name: target_resource_id}).delete()
        self._user_permissions_table.query.filter_by(**{self._resource_id_name: target_resource_id}).delete()
        self._group_permissions_table.query.filter_by(**{self._resource_id_name: target_resource_id}).delete()
        self._project_permissions_table.query.filter_by(**{self._resource_id_name: target_resource_id}).delete()

        permissions_for_all_users = self.get_permissions_for_all_users(source_resource_id)
        self.set_permissions_for_all_users(target_resource_id, permissions_for_all_users)
        permissions_for_users = self.get_permissions_for_users(source_resource_id)
        for user_id, permissions in permissions_for_users.items():
            self.set_permissions_for_user(target_resource_id, user_id, permissions)
        permissions_for_groups = self.get_permissions_for_groups(source_resource_id)
        for group_id, permissions in permissions_for_groups.items():
            self.set_permissions_for_group(target_resource_id, group_id, permissions)
        permissions_for_projects = self.get_permissions_for_projects(source_resource_id)
        for project_id, permissions in permissions_for_projects.items():
            self.set_permissions_for_project(target_resource_id, project_id, permissions)
