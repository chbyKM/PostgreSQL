import flask
from flask import request
import models
import forms


app = flask.Flask(__name__)
app.config["SECRET_KEY"] = "This is secret key"
app.config["SQLALCHEMY_DATABASE_URI"] = (
    "postgresql://coe:CoEpasswd@localhost:5432/coedb"
)

models.init_app(app)


@app.route("/")
def index():
    db = models.db
    notes = db.session.execute(
        db.select(models.Note).order_by(models.Note.title)
    ).scalars()
    return flask.render_template("index.html", notes=notes)


# Create note
@app.route("/notes/create", methods=["GET", "POST"])
def notes_create():
    form = forms.NoteForm()
    if form.validate_on_submit():
        note = models.Note(title=form.title.data, description=form.description.data)
        note.tags = []

        db = models.db
        tag_names = (
            [name.strip() for name in form.tags.data.split(",")]
            if form.tags.data
            else []
        )
        for tag_name in tag_names:
            tag = db.session.execute(
                db.select(models.Tag).where(models.Tag.name == tag_name)
            ).scalar_one_or_none()

            if not tag:
                tag = models.Tag(name=tag_name)
                db.session.add(tag)

            note.tags.append(tag)

        db.session.add(note)
        db.session.commit()
        return flask.redirect(flask.url_for("index"))

    return flask.render_template("notes-create.html", form=form)


# create tag
@app.route("/tags/<tag_name>")
def tags_view(tag_name):
    db = models.db
    tag = (
        db.session.execute(db.select(models.Tag).where(models.Tag.name == tag_name))
        .scalars()
        .first()
    )
    notes = db.session.execute(
        db.select(models.Note).where(models.Note.tags.any(id=tag.id))
    ).scalars()

    return flask.render_template(
        "tags-view.html",
        tag_name=tag_name,
        notes=notes,
    )


# edit note
@app.route("/notes/<int:note_id>/edit", methods=["GET", "POST"])
def notes_edit(note_id):
    db = models.db
    note = db.get_or_404(models.Note, note_id)
    form = forms.NoteForm(obj=note)

    if form.validate_on_submit():
        # Update only the fields that are not empty
        if form.title.data:
            note.title = form.title.data
        if form.description.data:
            note.description = form.description.data

        db.session.commit()
        return flask.redirect(flask.url_for("index"))

    return flask.render_template("notes-edit.html", form=form, note=note)


# delete note
@app.route("/notes/<int:note_id>/delete", methods=["POST"])
def notes_delete(note_id):
    db = models.db
    note = db.get_or_404(models.Note, note_id)
    db.session.delete(note)
    db.session.commit()
    return flask.redirect(flask.url_for("index"))


# edit tag
@app.route("/tags/<tag_name>/edit", methods=["GET", "POST"])
def tags_edit(tag_name):
    db = models.db
    tag = db.session.execute(
        db.select(models.Tag).where(models.Tag.name == tag_name)
    ).scalar_one_or_none()

    form = forms.TagForm(obj=tag)

    if form.validate_on_submit():
        if form.name.data and form.name.data != tag.name:
            tag.name = form.name.data
            db.session.commit()
            return flask.redirect(flask.url_for("tags_view", tag_name=tag.name))

    return flask.render_template("tags-edit.html", form=form, tag=tag)


# delete tag
@app.route("/tags/<tag_name>/delete", methods=["POST"])
def tags_delete(tag_name):
    db = models.db
    tag = db.session.execute(
        db.select(models.Tag).where(models.Tag.name == tag_name)
    ).scalar_one_or_none()

    if tag:
        db.session.delete(tag)
        db.session.commit()

    return flask.redirect(flask.url_for("index"))


if __name__ == "__main__":
    app.run(debug=True)