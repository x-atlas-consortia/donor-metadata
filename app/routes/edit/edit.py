# Context login form
from flask import Blueprint, request, render_template, jsonify, abort

# Represents the metadata for a donor in a consortium database
from models.donor import DonorData
# The form used to build request bodies for PUT and POST endpoints of the entity-api
from models.editform import EditForm


edit_blueprint = Blueprint('edit', __name__, url_prefix='/edit/<donorid>')

def setinputdisabled(inputField, disabled: bool = True):
    """
    Disables the given field.
    :param inputField: the WTForms input to disable
    :param disabled: if true set the disabled attribute of the input
    :return: nothing
    """

    if inputField.render_kw is None:
        inputField.render_kw = {}
    if disabled:
        inputField.render_kw['disabled'] = 'disabled'
    else:
        inputField.render_kw.pop('disabled')

def getconsortiumfromdonorid(donorid: str) ->str:
    """
    Tranlates the donorid into a consortium
    :param donorid: ID for a donor
    :return: consortium identifier
    """

    contextid = donorid[0:3]
    if contextid == "HBM":
        consortium = 'hubmapconsortium'
    elif contextid == "SNT":
        consortium = 'sennetconsortium'
    else:
        msg = (f'Invalid donor id format: {donorid}. The first three characters of the id should be either '
               f'"HBM (for HuBMAP) or SNT (for SenNet).')
        abort(400, msg)

    return consortium

def setdefaults(form, donorid: str):
    """
    Sets default values in form fields.

    """

    # The donor id (and by extension the consortium) are passed to the form via the search form. The fields
    # will be read-only.

    # Donor id
    form.donorid.data = donorid
    setinputdisabled(form.donorid, disabled=True)

    # Consortium
    consortium = getconsortiumfromdonorid(donorid=donorid)
    form.consortium.data = consortium
    setinputdisabled(form.consortium, disabled=True)

    # Set defaults for SelectFields, using either the current metadata values for the user or:
    # 1. default UMLS CUIs for required fields
    # 2. 'PROMPT' for optional fields
    # 3. default unit for unit fields

    # Get current metadata for donor. The auth token is obtained from the app.cfg file.
    CurrentDonorData = DonorData(donorid=donorid, consortium=consortium, token=form.token)

    print(CurrentDonorData.metadata)
    # age
    age_grouping_concept = form.valuesetmanager.getcolumnvalues(tab='Age', col='grouping_concept')[0]
    agelist = CurrentDonorData.getmetadatavalues(grouping_concept=age_grouping_concept, key='data_value')
    if len(agelist) > 0:
        form.agevalue.data = float(agelist[0])

    # age units
    ageunitlist = CurrentDonorData.getmetadatavalues(grouping_concept=age_grouping_concept, key='units')
    if len(ageunitlist) > 0:
        form.ageunits.data = ageunitlist[0]
    else:
        form.ageunits.data = 'C0001779'  # years

    # race
    race_grouping_concept = form.valuesetmanager.getcolumnvalues(tab='Race', col='grouping_concept')[0]
    racelist = CurrentDonorData.getmetadatavalues(grouping_concept=race_grouping_concept, key='concept_id')
    if len(racelist) > 0:
        form.race.data = racelist[0]
    else:
        form.race.data = 'C0439673'  # Unknown

    # ethnicity
    eth_grouping_concept = form.valuesetmanager.getcolumnvalues(tab='Ethnicity', col='grouping_concept')[0]
    ethlist = CurrentDonorData.getmetadatavalues(grouping_concept=eth_grouping_concept, key='concept_id')
    if len(ethlist) > 0:
        form.ethnicity.data = ethlist[0]
    else:
        form.race.data = 'PROMPT'
    # sex
    sex_grouping_concept = form.valuesetmanager.getcolumnvalues(tab='Sex', col='grouping_concept')[0]
    sexlist = CurrentDonorData.getmetadatavalues(grouping_concept=sex_grouping_concept, key='concept_id')
    if len(sexlist) > 0:
        form.sex.data = sexlist[0]
    else:
        form.race.data = 'C0421467'  # Unknown

    # Organ donor switch
    # if CurrentDonorData.metadata_type == 'organ_donor_data':

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



@edit_blueprint.route('', methods=['GET', 'POST'])
def edit(donorid):

    form = EditForm(request.form)

    setdefaults(form, donorid=donorid)

    if request.method == 'POST' and form.validate():
        # Translate fields into the encoded donor metadata schema.
        return "OK"

        # Execute appropriate endpoint of entity-api.

    return render_template('edit.html', form=form)
