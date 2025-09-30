
from flask_wtf import FlaskForm
from wtforms import StringField, FloatField, DateTimeLocalField, SelectField, SubmitField
from wtforms.validators import DataRequired, NumberRange

class StationForm(FlaskForm):
    name = StringField('Nome da Estação', validators=[DataRequired()])
    submit = SubmitField('Salvar')

class RunForm(FlaskForm):
    station_id = SelectField('Estação', coerce=int, validators=[DataRequired()])
    start_dt = DateTimeLocalField('Início', format='%Y-%m-%dT%H:%M', validators=[DataRequired()])
    end_dt = DateTimeLocalField('Fim', format='%Y-%m-%dT%H:%M', validators=[DataRequired()])
    miles = FloatField('Milhagem (mi)', default=0.0, validators=[NumberRange(min=0)])
    cost = FloatField('Custo (US$)', default=0.0)
    revenue = FloatField('Receita (US$)', default=0.0)
    tips = FloatField('Gorjetas (US$)', default=0.0)
    submit = SubmitField('Salvar')
