from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import Length, DataRequired, ValidationError


class Search_Video(FlaskForm):
    video_id = StringField(label="Video ID", validators=[DataRequired(), Length(min=1)])
    send = SubmitField()
