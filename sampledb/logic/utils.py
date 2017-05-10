# coding: utf-8
"""

"""

import smtplib
import flask
import flask_mail

from .. import mail, db
from .security_tokens import generate_token
from ..models import Authentication, AuthenticationType, User


def send_confirm_email(email, id, salt):
    if id == None:
        route = "frontend.%s_route" % salt
        token = generate_token(email, salt=salt,
                               secret_key=flask.current_app.config['SECRET_KEY'])
        confirm_url = flask.url_for(route, token=token, _external=True)
    else:
        token = generate_token([email, id], salt=salt,
                               secret_key=flask.current_app.config['SECRET_KEY'])
        confirm_url = flask.url_for("frontend.user_preferences", user_id=id, token=token, _external=True)

    subject = "Please confirm your email"
    html = flask.render_template('activate.html', confirm_url=confirm_url)
    try:
        mail.send(flask_mail.Message(
            subject,
            sender=flask.current_app.config['MAIL_SENDER'],
            recipients=[email],
            html=html
        ))
    except smtplib.SMTPRecipientsRefused:
        pass


def send_recovery_email(email):
    users = User.query.filter_by(email=email).all()
    email_authentication = Authentication.query.filter(db.and_(Authentication.login['login'].astext == email, Authentication.type == AuthenticationType.EMAIL)).first()
    if email_authentication is not None and email_authentication.user not in users:
        users.append(email_authentication.user)

    if not users:
        return

    password_reset_urls = {}
    for user in users:
        for authentication_method in user.authentication_methods:
            if authentication_method.type != AuthenticationType.LDAP:
                password_reset_urls[authentication_method] = build_confirm_url(authentication_method)

    subject = "Recovery email"
    html = flask.render_template('recovery_information.html', email=email, users=users, password_reset_urls=password_reset_urls)
    try:
        mail.send(flask_mail.Message(
            subject,
            sender=flask.current_app.config['MAIL_SENDER'],
            recipients=[email],
            html=html
        ))
    except smtplib.SMTPRecipientsRefused:
        pass


def build_confirm_url(authentication_method, salt='password'):
    assert authentication_method.type != AuthenticationType.LDAP

    user_id = authentication_method.user_id
    token = generate_token(authentication_method.id, salt=salt,
                           secret_key=flask.current_app.config['SECRET_KEY'])
    return flask.url_for("frontend.user_preferences", user_id=user_id, token=token, _external=True)
