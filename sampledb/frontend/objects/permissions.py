# coding: utf-8
"""

"""
import json

import flask
import flask_login
import requests
from flask_babel import _

from ...logic.federation import update_poke_component
from .. import frontend
from ... import logic
from ...logic import user_log
from ...logic.actions import get_action
from ...logic.components import get_component_by_uuid
from ...logic.errors import ObjectDoesNotExistError, ComponentDoesNotExistError
from ...logic.object_permissions import Permissions, get_user_object_permissions, get_object_permissions_for_all_users, get_object_permissions_for_anonymous_users, get_object_permissions_for_users, get_objects_with_permissions, get_object_permissions_for_groups, get_object_permissions_for_projects, request_object_permissions
from ...logic.shares import get_shares_for_object, add_object_share, update_object_share
from ...logic.users import get_users, get_users_for_component
from ...logic.groups import get_group, get_user_groups
from ...logic.objects import get_object, get_fed_object
from ...logic.projects import get_project, get_user_projects
from ...logic.components import get_component, get_components
from .forms import CopyPermissionsForm, ObjectNewShareAccessForm, ObjectEditShareAccessForm
from ..permission_forms import PermissionsForm, UserPermissionsForm, GroupPermissionsForm, ProjectPermissionsForm, handle_permission_forms, set_up_permissions_forms
from ...utils import object_permissions_required
from ..utils import get_user_if_exists, check_current_user_is_not_readonly


def on_unauthorized(object_id):
    permissions_by_user = get_object_permissions_for_users(object_id)
    has_grant_user = any(
        Permissions.GRANT in permissions
        for permissions in permissions_by_user.values()
    )
    return flask.render_template('objects/unauthorized.html', object_id=object_id, has_grant_user=has_grant_user), 403


def get_object_if_current_user_has_read_permissions(object_id, component_uuid=None):
    user_id = flask_login.current_user.id
    if component_uuid is None or component_uuid == flask.current_app.config['FEDERATION_UUID']:
        try:
            permissions = get_user_object_permissions(object_id, user_id)
            if Permissions.READ not in permissions:
                return None
            else:
                return get_object(object_id)
        except ObjectDoesNotExistError:
            return None
    else:
        try:
            component = get_component_by_uuid(component_uuid)
        except ComponentDoesNotExistError:
            return None
        try:
            object = get_fed_object(object_id, component.id)
            permissions = get_user_object_permissions(object.id, user_id)
            if Permissions.READ not in permissions:
                return None
        except ObjectDoesNotExistError:
            return None
        return object


def get_fed_object_if_current_user_has_read_permissions(fed_object_id, component_uuid):
    user_id = flask_login.current_user.id
    component = get_component_by_uuid(component_uuid)
    try:
        fed_object = get_fed_object(fed_object_id, component_id=component.id)
        permissions = get_user_object_permissions(fed_object.id, user_id)
    except ObjectDoesNotExistError:
        return None
    if Permissions.READ not in permissions:
        return None
    return fed_object


@frontend.route('/objects/<int:object_id>/permissions/request', methods=['POST'])
@flask_login.login_required
def object_permissions_request(object_id):
    current_permissions = get_user_object_permissions(object_id=object_id, user_id=flask_login.current_user.id)
    if Permissions.READ in current_permissions:
        flask.flash(_('You already have permissions to access this object.'), 'error')
        return flask.redirect(flask.url_for('.object', object_id=object_id))
    request_object_permissions(flask_login.current_user.id, object_id)
    flask.flash(_('Your request for permissions has been sent.'), 'success')
    return flask.redirect(flask.url_for('.objects'))


@frontend.route('/objects/<int:object_id>/permissions')
@object_permissions_required(Permissions.READ, on_unauthorized=on_unauthorized)
def object_permissions(object_id):
    check_current_user_is_not_readonly()
    object = get_object(object_id)
    components = get_components()
    if object.action_id is not None:
        action = get_action(object.action_id)
        instrument = action.instrument
    else:
        action = None
        instrument = None
    user_permissions = get_object_permissions_for_users(object_id=object_id, include_instrument_responsible_users=False, include_groups=False, include_projects=False, include_readonly=False, include_admin_permissions=False)
    group_permissions = get_object_permissions_for_groups(object_id=object_id, include_projects=False)
    project_permissions = get_object_permissions_for_projects(object_id=object_id)
    all_user_permissions = get_object_permissions_for_all_users(object_id=object_id)
    anonymous_user_permissions = get_object_permissions_for_anonymous_users(object_id=object_id)
    component_policies = {share.component_id: share for share in get_shares_for_object(object_id)}
    policies = {share.component_id: share.policy for share in get_shares_for_object(object_id)}
    suggested_user_id = flask.request.args.get('add_user_id', '')
    try:
        suggested_user_id = int(suggested_user_id)
    except ValueError:
        suggested_user_id = None
    if Permissions.GRANT in get_user_object_permissions(object_id=object_id, user_id=flask_login.current_user.id):
        (
            add_user_permissions_form,
            add_group_permissions_form,
            add_project_permissions_form,
            permissions_form
        ) = set_up_permissions_forms(
            resource_permissions=logic.object_permissions.object_permissions,
            resource_id=object_id,
            existing_all_user_permissions=all_user_permissions,
            existing_anonymous_user_permissions=anonymous_user_permissions,
            existing_user_permissions=user_permissions,
            existing_group_permissions=group_permissions,
            existing_project_permissions=project_permissions
        )

        users = get_users(exclude_hidden=True, exclude_fed=True)
        users = [user for user in users if user.id not in user_permissions]
        users.sort(key=lambda user: user.id)

        groups = get_user_groups(flask_login.current_user.id)
        groups = [group for group in groups if group.id not in group_permissions]
        groups.sort(key=lambda group: group.id)

        projects = get_user_projects(flask_login.current_user.id, include_groups=True)
        projects = [project for project in projects if project.id not in project_permissions]
        projects.sort(key=lambda project: project.id)

        possible_new_components = [component for component in components if component.id not in component_policies.keys()]
        component_users = {
            component.id: {
                user.fed_id: user.get_name(include_ref=True)
                for user in get_users_for_component(component.id, exclude_hidden=False)
            }
            for component in components
        }
        add_component_policy_form = ObjectNewShareAccessForm()
        add_component_policy_form.data.data = True
        add_component_policy_form.action.data = True
        add_component_policy_form.users.data = True
        add_component_policy_form.files.data = True
        add_component_policy_form.comments.data = True
        add_component_policy_form.object_location_assignments.data = True
        edit_component_policy_form = ObjectEditShareAccessForm()
        edit_component_policy_form.data.data = True
        edit_component_policy_form.action.data = True
        edit_component_policy_form.users.data = True
        edit_component_policy_form.files.data = True
        edit_component_policy_form.comments.data = True
        edit_component_policy_form.object_location_assignments.data = True
        copy_permissions_form = CopyPermissionsForm()
        if not flask.current_app.config["LOAD_OBJECTS_IN_BACKGROUND"]:
            existing_objects = get_objects_with_permissions(
                user_id=flask_login.current_user.id,
                permissions=Permissions.GRANT
            )
            copy_permissions_form.object_id.choices = [
                (str(existing_object.id), existing_object.name)
                for existing_object in existing_objects
                if existing_object.id != object_id
            ]
            if len(copy_permissions_form.object_id.choices) == 0:
                copy_permissions_form = None
        else:
            copy_permissions_form.object_id.choices = []
    else:
        permissions_form = None
        add_user_permissions_form = None
        add_group_permissions_form = None
        add_project_permissions_form = None
        add_component_policy_form = None
        copy_permissions_form = None
        edit_component_policy_form = None

        users = []
        groups = []
        projects = []
        possible_new_components = None
        component_users = []

    acceptable_project_ids = {
        project.id
        for project in projects
    }

    all_projects = logic.projects.get_projects()
    all_projects_by_id = {
        project.id: project
        for project in all_projects
    }

    if not flask.current_app.config['DISABLE_SUBPROJECTS']:
        project_id_hierarchy_list = logic.projects.get_project_id_hierarchy_list(list(all_projects_by_id))
        project_id_hierarchy_list = [
            (level, project_id, project_id in acceptable_project_ids)
            for level, project_id in project_id_hierarchy_list
        ]
    else:
        project_id_hierarchy_list = [
            (0, project.id, project.id in acceptable_project_ids)
            for project in sorted(all_projects, key=lambda project: project.id)
        ]
    show_projects_form = any(
        enabled
        for level, project_id, enabled in project_id_hierarchy_list
    )
    return flask.render_template(
        'objects/object_permissions.html',
        instrument=instrument,
        action=action,
        object=object,
        user_permissions=user_permissions,
        group_permissions=group_permissions,
        project_permissions=project_permissions,
        all_user_permissions=all_user_permissions,
        anonymous_user_permissions=anonymous_user_permissions,
        federation_shares=component_policies,
        get_user=get_user_if_exists,
        get_component=get_component,
        Permissions=Permissions,
        permissions_form=permissions_form,
        users=users,
        groups=groups,
        projects_by_id=all_projects_by_id,
        project_id_hierarchy_list=project_id_hierarchy_list,
        show_projects_form=show_projects_form,
        edit_component_policy_form=edit_component_policy_form,
        component_users=component_users,
        copy_permissions_form=copy_permissions_form,
        add_component_policy_form=add_component_policy_form,
        possible_new_components=possible_new_components,
        add_user_permissions_form=add_user_permissions_form,
        add_group_permissions_form=add_group_permissions_form,
        get_group=get_group,
        add_project_permissions_form=add_project_permissions_form,
        get_project=get_project,
        suggested_user_id=suggested_user_id,
        json_dumps=json.dumps,
        policies=policies
    )


@frontend.route('/objects/<int:object_id>/permissions', methods=['POST'])
@object_permissions_required(Permissions.GRANT)
def update_object_permissions(object_id):
    permissions_form = PermissionsForm()
    add_user_permissions_form = UserPermissionsForm()
    add_group_permissions_form = GroupPermissionsForm()
    add_project_permissions_form = ProjectPermissionsForm()
    add_component_policy_form = ObjectNewShareAccessForm()
    edit_component_policy_form = ObjectEditShareAccessForm()
    copy_permissions_form = CopyPermissionsForm()
    if 'copy_permissions' in flask.request.form:
        if not flask.current_app.config["LOAD_OBJECTS_IN_BACKGROUND"]:
            existing_objects = get_objects_with_permissions(
                user_id=flask_login.current_user.id,
                permissions=Permissions.GRANT
            )
            copy_permissions_form.object_id.choices = [
                (str(existing_object.id), existing_object.name)
                for existing_object in existing_objects
                if existing_object.id != object_id
            ]
        else:
            copy_permissions_form.object_id.choices = []
        if copy_permissions_form.validate_on_submit():
            logic.object_permissions.copy_permissions(object_id, int(copy_permissions_form.object_id.data))
            logic.object_permissions.set_user_object_permissions(object_id, flask_login.current_user.id, Permissions.GRANT)
            flask.flash(_("Successfully copied object permissions."), 'success')
    elif 'add_component_policy' in flask.request.form and add_component_policy_form.validate_on_submit():
        component_id = add_component_policy_form.component_id.data
        component = get_component(component_id)
        policy = {
            'access': {
                'data': add_component_policy_form.data.data,
                'action': add_component_policy_form.action.data,
                'users': add_component_policy_form.users.data,
                'files': add_component_policy_form.files.data,
                'comments': add_component_policy_form.comments.data,
                'object_location_assignments': add_component_policy_form.object_location_assignments.data,
            },
            'permissions': {'users': {}, 'groups': {}, 'projects': {}, 'all_users': 'none'}
        }
        allowed_permissions = [Permissions.READ.name.lower(), Permissions.WRITE.name.lower(), Permissions.GRANT.name.lower()]
        for attr_name, value in flask.request.form.items():
            if attr_name[:len('permissions_add_policy_user_')] == 'permissions_add_policy_user_':
                user_id = attr_name[len('permissions_add_policy_user_'):]
                try:
                    user_id = int(user_id)
                except ValueError:
                    flask.flash(_("A problem occurred while changing the object permissions. Please try again."), 'error')
                if value not in allowed_permissions:
                    flask.flash(_("A problem occurred while changing the object permissions. Please try again."), 'error')
                policy['permissions']['users'][user_id] = value
        add_object_share(object_id, component_id, policy)
        try:
            update_poke_component(component)
        except logic.errors.MissingComponentAddressError:
            flask.flash(_('Unable to contact %(component_name)s. Missing database address.', component_name=component.get_name()), 'warning')
        except logic.errors.NoAuthenticationMethodError:
            flask.flash(_('No valid authentication method configured for %(component_name)s (%(component_address)s).', component_name=component.get_name(), component_address=component.address), 'warning')
        except requests.ConnectionError:
            flask.flash(_('Unable to contact %(component_name)s (%(component_address)s).', component_name=component.get_name(), component_address=component.address), 'warning')
        flask.flash(_("Successfully updated object permissions."), 'success')
    elif 'edit_component_policy' in flask.request.form and edit_component_policy_form.validate_on_submit():
        component_id = edit_component_policy_form.component_id.data
        component = get_component(component_id)
        policy = {
            'access': {
                'data': edit_component_policy_form.data.data,
                'action': edit_component_policy_form.action.data,
                'users': edit_component_policy_form.users.data,
                'files': edit_component_policy_form.files.data,
                'comments': edit_component_policy_form.comments.data,
                'object_location_assignments': edit_component_policy_form.object_location_assignments.data,
            },
            'permissions': {'users': {}, 'groups': {}, 'projects': {}, 'all_users': 'none'}
        }
        allowed_permissions = [Permissions.READ.name.lower(), Permissions.WRITE.name.lower(), Permissions.GRANT.name.lower()]
        for attr_name, value in flask.request.form.items():
            if attr_name[:len('permissions_edit_policy_user_')] == 'permissions_edit_policy_user_':
                user_id = attr_name[len('permissions_edit_policy_user_'):]
                try:
                    user_id = int(user_id)
                except ValueError:
                    flask.flash(_("A problem occurred while changing the object permissions. Please try again."), 'error')
                    return flask.redirect(flask.url_for('.object_permissions', object_id=object_id))
                if value not in allowed_permissions:
                    flask.flash(_("A problem occurred while changing the object permissions. Please try again."), 'error')
                    return flask.redirect(flask.url_for('.object_permissions', object_id=object_id))
                policy['permissions']['users'][user_id] = value
        update_object_share(object_id, component_id, policy)
        try:
            update_poke_component(component)
        except logic.errors.MissingComponentAddressError:
            flask.flash(_('Unable to contact %(component_name)s. Missing database address.', component_name=component.get_name()), 'warning')
        except logic.errors.NoAuthenticationMethodError:
            flask.flash(_('No valid authentication method configured for %(component_name)s (%(component_address)s).', component_name=component.get_name(), component_address=component.address), 'warning')
        except requests.ConnectionError:
            flask.flash(_('Unable to contact %(component_name)s (%(component_address)s).', component_name=component.get_name(), component_address=component.address), 'warning')
        flask.flash(_("Successfully updated object permissions."), 'success')
    else:
        if handle_permission_forms(
            logic.object_permissions.object_permissions,
            object_id,
            add_user_permissions_form,
            add_group_permissions_form,
            add_project_permissions_form,
            permissions_form
        ):
            user_log.edit_object_permissions(user_id=flask_login.current_user.id, object_id=object_id)
            flask.flash(_("Successfully updated object permissions."), 'success')
        else:
            flask.flash(_("A problem occurred while changing the object permissions. Please try again."), 'error')
    return flask.redirect(flask.url_for('.object_permissions', object_id=object_id))
