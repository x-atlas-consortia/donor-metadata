# Context login form
from flask import Blueprint, request, render_template, jsonify

# The form used to build request bodies for PUT and POST endpoints of the entity-api
from models.editform import EditForm

index_blueprint = Blueprint('index', __name__, url_prefix='/')

@index_blueprint.route('', methods=['GET','POST'])
def index():

    # Get the application context using a form.
    form = EditForm(request.form)

    # Set defaults for SelectFields, using the UMLS CUIs
    form.source_name.data='PROMPT'
    form.race.data='C0439673' # Unknown
    form.sex.data='C0421467 ' # Unknown
    form.ethnicity.data='PROMPT'
    form.ageunits.data = 'C0001779' # years

    form.cause.data='PROMPT'
    form.mechanism.data='PROMPT'
    form.event.data='PROMPT'

    form.heightunit.data='0'
    form.weightunit.data='0'

    if request.method == 'POST' and form.validate():
        # Obtain selected context from form.
        context = form.context.choices[0][1]
        donorid = form.donorid.data
        dictret = {'id': donorid}
        return jsonify(dictret)

    return render_template( 'index.html', form=form)
