# Context login form
from flask import Blueprint, request, render_template, jsonify, abort

# Represents the metadata for a donor in a consortium database
from models.donor import DonorData
# The form used to build request bodies for PUT and POST endpoints of the entity-api
from models.editform import EditForm


edit_blueprint = Blueprint('edit', __name__, url_prefix='/edit/<donorid>')


def setinputdisabled(inputfield, disabled: bool = True):
    """
    Disables the given field.
    :param inputfield: the WTForms input to disable
    :param disabled: if true set the disabled attribute of the input
    :return: nothing
    """

    if inputfield.render_kw is None:
        inputfield.render_kw = {}
    if disabled:
        inputfield.render_kw['disabled'] = 'disabled'
    else:
        inputfield.render_kw.pop('disabled')


def getconsortiumfromdonorid(donorid: str) -> str:
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
    currentdonordata = DonorData(donorid=donorid, consortium=consortium, token=form.token)

    #print(currentdonordata.metadata)

    # Age
    # The Age valueset has its own tab.
    age_grouping_concept = form.valuesetmanager.getcolumnvalues(tab='Age', col='grouping_concept')[0]
    agelist = currentdonordata.getmetadatavalues(grouping_concept=age_grouping_concept, key='data_value')
    if len(agelist) > 0:
        form.agevalue.data = float(agelist[0])

    # Age Units
    # The default age unit is years.
    ageunitlist = currentdonordata.getmetadatavalues(grouping_concept=age_grouping_concept, key='units')
    if len(ageunitlist) > 0:
        form.ageunits.data = ageunitlist[0]
    else:
        form.ageunits.data = 'C0001779'  # years

    # Race
    # The Race valueset has its own tab. The default value is Unknown.
    race_grouping_concept = form.valuesetmanager.getcolumnvalues(tab='Race', col='grouping_concept')[0]
    racelist = currentdonordata.getmetadatavalues(grouping_concept=race_grouping_concept, key='concept_id')
    if len(racelist) > 0:
        form.race.data = racelist[0]
    else:
        form.race.data = 'C0439673'  # Unknown

    # Ethnicity
    # The Ethnicity valueset has its own tab. There is no default value.
    eth_grouping_concept = form.valuesetmanager.getcolumnvalues(tab='Ethnicity', col='grouping_concept')[0]
    ethlist = currentdonordata.getmetadatavalues(grouping_concept=eth_grouping_concept, key='concept_id')
    if len(ethlist) > 0:
        form.ethnicity.data = ethlist[0]
    else:
        form.ethnicity.data = 'PROMPT'

    # Sex
    # The Sex valueset has its own tab. The default value is Unknown.
    sex_grouping_concept = form.valuesetmanager.getcolumnvalues(tab='Sex', col='grouping_concept')[0]
    sexlist = currentdonordata.getmetadatavalues(grouping_concept=sex_grouping_concept, key='concept_id')
    if len(sexlist) > 0:
        form.sex.data = sexlist[0]
    else:
        form.sex.data = 'C0421467'  # Unknown

    # Cause of Death
    # The Cause of Death valuest has its own tab. There is no default value.
    cod_grouping_concept = form.valuesetmanager.getcolumnvalues(tab='Cause of Death', col='grouping_concept')[0]
    codlist = currentdonordata.getmetadatavalues(grouping_concept=cod_grouping_concept, key='concept_id')
    if len(codlist) > 0:
        form.cause.data = codlist[0]
    else:
        form.cause.data = 'PROMPT'

    # Mechanism of Injury
    # The Mechanism of Injury valueset has its own tab. There is no default value.
    mech_grouping_concept = form.valuesetmanager.getcolumnvalues(tab='Mechanism of Injury', col='grouping_concept')[0]
    mechlist = currentdonordata.getmetadatavalues(grouping_concept=mech_grouping_concept, key='concept_id')
    if len(mechlist) > 0:
        form.mechanism.data = mechlist[0]
    else:
        form.mechanism.data = 'PROMPT'

    # Death Event
    # The Death Event valueset has its own tab. There is no default value.
    event_grouping_concept = form.valuesetmanager.getcolumnvalues(tab='Death Event', col='grouping_concept')[0]
    eventlist = currentdonordata.getmetadatavalues(grouping_concept=event_grouping_concept, key='concept_id')
    if len(eventlist) > 0:
        form.event.data = eventlist[0]
    else:
        form.event.data = 'PROMPT'

    # Height
    # The Height valueset has only one concept, on the "Measurements" tab.
    height_concept = 'C0005890'
    heightvaluelist = currentdonordata.getmetadatavalues(grouping_concept=height_concept, key='data_value')
    if len(heightvaluelist) > 0:
        form.heightvalue.data = float(heightvaluelist[0])

    # Height unit
    # The Height unit is currently linked to the Height valueset, and has a default of cm.
    heightunitlist = currentdonordata.getmetadatavalues(grouping_concept=height_concept, key='units')
    if len(heightunitlist) > 0:
        form.heightunit.data = heightunitlist[0]
    else:
        form.heightunit.data = '0'  # cm

    # Weight
    # The Weight valueset has only one concept, on the "Measurements" tab.
    weight_concept = 'C0005910'
    weightvaluelist = currentdonordata.getmetadatavalues(grouping_concept=weight_concept, key='data_value')
    if len(weightvaluelist) > 0:
        form.weightvalue.data = float(weightvaluelist[0])

    # Weight unit
    # The Weight unit is currently linked to the Height valueset, and has a default of kg.
    weightunitlist = currentdonordata.getmetadatavalues(grouping_concept=weight_concept, key='units')
    if len(weightunitlist) > 0:
        form.weightunit.data = heightunitlist[0]
    else:
        form.heightunit.data = '0'  # kg

    # Body Mass Index
    # The BMI has no default value.
    bmi_concept = 'C1305855'
    bmilist = currentdonordata.getmetadatavalues(grouping_concept=bmi_concept, key='data_value')
    if len(bmilist) > 0:
        form.bmi.data = float(bmilist[0])

    # Waist Circumference
    # The Waist Circumference valueset has only one concept, on the "Measurements" tab.
    waist_concept = 'C0455829'
    waistvaluelist = currentdonordata.getmetadatavalues(grouping_concept=waist_concept, key='data_value')
    if len(waistvaluelist) > 0:
        form.waistvalue.data = float(waistvaluelist[0])

    # Waist Circumference unit
    # The Waist Circumference unit is currently linked to the Height valueset, and has a default of cm.
    waistunitlist = currentdonordata.getmetadatavalues(grouping_concept=waist_concept, key='units')
    if len(waistunitlist) > 0:
        form.waistunit.data = waistunitlist[0]
    else:
        form.waistunit.data = '0'  # cm

    # Age at menarche
    # The age at menarche has no default value.
    agemenarche_concept = 'C1314691'
    agemenarchelist = currentdonordata.getmetadatavalues(grouping_concept=agemenarche_concept, key='data_value')
    if len(agemenarchelist) > 0:
        form.agemenarche.data = float(agemenarchelist[0])

    # Age at first birth
    # The age at first birth has no default value.
    agefirstbirth_concept = 'C1510831'
    agefirstbirthlist = currentdonordata.getmetadatavalues(grouping_concept=agefirstbirth_concept, key='data_value')
    if len(agefirstbirthlist) > 0:
        form.agefirstbirth.data = float(agefirstbirthlist[0])

    # Gestational age
    # The gestational age has no default value.
    gestationalage_concept = 'C0017504'
    gestationalagelist = currentdonordata.getmetadatavalues(grouping_concept=gestationalage_concept, key='data_value')
    if len(gestationalagelist) > 0:
        form.gestationalage.data = float(gestationalagelist[0])

    # Fitzpatrick Skin Type
    # The Fitzpatrick scale is categorical. For the original set of donors that had Fitzpatrick scores,
    # the grouping concept was the same as the valueset concept, so it is necessary to build a group of
    # concepts manually. If these donors are re-ingested with the corrected valuesets, the logic
    # can revert to using a common grouping_concept.

    fitz_concepts = ['C2700185', 'C2700186', 'C2700187', 'C2700188', 'C2700189', 'C2700190']
    fitzlist = currentdonordata.getmetadatavalues(list_concept=fitz_concepts, key='concept_id')
    if len(fitzlist) > 0:
        form.fitzpatrick.data = fitzlist[0]
    else:
        form.fitzpatrick.data = 'PROMPT'

    # ABO Blood Type
    # The ABO Blood type is categorical. Its valueset is a subset of rows on the "Blood Types" tab.
    bloodtype_concept = 'C0000778'
    bloodtypelist = currentdonordata.getmetadatavalues(grouping_concept=bloodtype_concept, key='concept_id')
    print('bloodtypelist',bloodtypelist)
    if len(bloodtypelist) > 0:
        form.bloodtypes.data = bloodtypelist[0]
    else:
        form.bloodtypes.data = 'PROMPT'
    print('form.bloodtypes.data',form.bloodtypes.data)

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
