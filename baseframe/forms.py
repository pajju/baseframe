# -*- coding: utf-8 -*-

"""
Standard forms
"""

from flask import render_template, request, Markup, abort, flash, redirect, json, escape, url_for
from wtforms.widgets import html_params
import flask.ext.wtf as wtf
from coaster import sanitize_html


class RichText(wtf.TextArea):
    """
    Rich text widget.
    """
    def __call__(self, field, **kwargs):
        c = kwargs.pop('class', '') or kwargs.pop('class_', '')
        if c:
            kwargs['class'] = u'%s %s' % ('richtext', c)
        else:
            kwargs['class'] = 'richtext'
        return super(RichText, self).__call__(field, **kwargs)


class SubmitInput(wtf.SubmitInput):
    """
    Submit input with pre-defined classes.
    """
    def __init__(self, *args, **kwargs):
        self.css_class = kwargs.pop('class', '') or kwargs.pop('class_', '')
        super(SubmitInput, self).__init__(*args, **kwargs)

    def __call__(self, field, **kwargs):
        c = kwargs.pop('class', '') or kwargs.pop('class_', '')
        kwargs['class'] = u'%s %s' % (self.css_class, c)
        return super(SubmitInput, self).__call__(field, **kwargs)


class DateTimeInput(wtf.Input):
    """
    Render date and time inputs.
    """
    input_type = 'datetime'

    def __call__(self, field, **kwargs):
        kwargs.setdefault('id', field.id)
        field_id = kwargs.pop('id')
        kwargs.pop('type', None)
        value = kwargs.pop('value', None)
        if value is None:
            value = field._value()
        if not value:
            value = ' '
        date_value, time_value = value.split(' ', 1)
        return Markup(u'<input type="date" data-datepicker="datepicker" %s /> <input type="time" data-provide="timepicker" %s />' % (
            html_params(name=field.name, id=field_id + '-date', value=date_value, **kwargs),
            html_params(name=field.name, id=field_id + '-time', value=time_value, **kwargs)
            ))


class RichTextField(wtf.TextAreaField):
    """
    Rich text field.
    """
    widget = RichText()

    # TODO: Accept valid_tags as a init parameter

    def process_formdata(self, valuelist):
        super(RichTextField, self).process_formdata(valuelist)
        # Sanitize data
        self.data = sanitize_html(self.data)


class DateTimeField(wtf.DateTimeField):
    """
    A text field which stores a `datetime.datetime` matching a format.
    """
    widget = DateTimeInput()

    def __init__(self, label=None, validators=None, format='%Y-%m-%d %I:%M %p', **kwargs):
        super(DateTimeField, self).__init__(label, validators, **kwargs)
        self.format = format


class Form(wtf.Form):
    """
    Form with additional methods.
    """
    def __init__(self, *args, **kwargs):
        super(Form, self).__init__(*args, **kwargs)
        # Make editing objects easier
        self.edit_obj = kwargs.get('obj')


class ConfirmDeleteForm(Form):
    """
    Confirm a delete operation
    """
    # The labels on these widgets are not used. See delete.html.
    delete = wtf.SubmitField(u"Delete")
    cancel = wtf.SubmitField(u"Cancel")


def render_form(form, title, message='', formid='form', submit=u"Submit", cancel_url=None, ajax=False):
    multipart = False
    for field in form:
        if isinstance(field.widget, wtf.FileInput):
            multipart = True
    if request.is_xhr and ajax:
        return render_template('baseframe/ajaxform.html', form=form, title=title,
            message=message, formid=formid, submit=submit,
            cancel_url=cancel_url, multipart=multipart)
    else:
        return render_template('baseframe/autoform.html', form=form, title=title,
            message=message, formid=formid, submit=submit,
            cancel_url=cancel_url, ajax=ajax, multipart=multipart)


def render_message(title, message):
    if request.is_xhr:
        return Markup("<p>%s</p>" % escape(message))
    else:
        return render_template('baseframe/message.html', title=title, message=message)


def render_redirect(url, code=302):
    if request.is_xhr:
        return render_template('baseframe/redirect.html', quoted_url=Markup(json.dumps(url)))
    else:
        return redirect(url, code=code)


def render_delete_sqla(ob, db, title, message, success=u'', next=None):
    if not ob:
        abort(404)
    form = ConfirmDeleteForm()
    if form.validate_on_submit():
        if 'delete' in request.form:
            db.session.delete(ob)
            db.session.commit()
            if success:
                flash(success, "success")
        return render_redirect(next or url_for('index'))
    return render_template('baseframe/delete.html', form=form, title=title, message=message)
