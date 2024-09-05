# Context login form
from flask import Blueprint, request, render_template, jsonify

# The form used to build request bodies for PUT and POST endpoints of the entity-api
from models.editform import EditForm

index_blueprint = Blueprint('index', __name__, url_prefix='/')



@index_blueprint.route('', methods=['GET', 'POST'])
def index():

    # Get the application context using a form.
    form = EditForm(request.form)

    # Set defaults for SelectFields, using:
    # 1. UMLS CUIs for required fields
    # 2. 'PROMPT' for optional fields
    # 3. default unit for unit fields

    form.source_name.data = 'PROMPT'
    form.race.data = 'C0439673'  # Unknown
    form.sex.data = 'C0421467 '  # Unknown
    form.ethnicity.data = 'PROMPT'
    form.ageunits.data = 'C0001779'  # years
    form.cause.data = 'PROMPT'
    form.mechanism.data = 'PROMPT'
    form.event.data = 'PROMPT'
    form.heightunit.data = '0'  # cm
    form.weightunit.data = '0'  # kg
    form.waistunit.data = '0'  # cm
    form.fitzpatrick.data = 'PROMPT'
    form.bloodtype.data = 'PROMPT'
    form.bloodrh.data = 'PROMPT'
    form.smoking.data = 'PROMPT'
    form.tobacco.data = 'PROMPT'
    form.alcohol.data = 'PROMPT'
    form.drug.data = 'PROMPT'
    form.medhx_0.data = 'PROMPT'
    form.medhx_1.data = 'PROMPT'
    form.medhx_2.data = 'PROMPT'
    form.medhx_3.data = 'PROMPT'
    form.medhx_4.data = 'PROMPT'
    form.medhx_5.data = 'PROMPT'
    form.medhx_6.data = 'PROMPT'
    form.medhx_7.data = 'PROMPT'
    form.medhx_8.data = 'PROMPT'
    form.medhx_9.data = 'PROMPT'

    if request.method == 'POST' and form.validate():
        # Translate fields into the encoded donor metadata schema.
        context = form.context.choices[0][1]
        donorid = form.donorid.data
        dictret = {'id': donorid}
        return jsonify(dictret)

        # Execute appropriate endpoint of entity-api.

    return render_template('index.html', form=form)
