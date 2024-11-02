"""
Donor metadata edit route.
Second page in the curation workflow.
Works with editform.py.

Does the following:
1. Obtains any existing metadata for the donor from provenance.
2. Sets input forms with defaults that match the existing metadata.
3. Tranlsates form data into the donor metadata schema.
4. Routes the existing and changed metadata to the review page.
"""

from flask import Blueprint, request, render_template, flash, session, abort
from wtforms import SelectField, Field
import base64
import pickle
import deepdiff
import json

# Helper classes
# Represents the metadata for a donor in a consortium database
from models.donor import DonorData
# The form used to build request bodies for PUT and POST endpoints of the entity-api
from models.editform import EditForm

edit_blueprint = Blueprint('edit', __name__, url_prefix='/edit')


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


@edit_blueprint.route('', methods=['POST', 'GET'])
def edit():

    form = EditForm(request.form)
    # Obtain current donor metadata from provenance.
    # First, obtain the authentication token from the session cookie.
    if 'groups_token' in session:
        token = session['groups_token']
    else:
        abort(401)

    # Obtain the donor id from the session cookie.
    donorid = session['donorid']

    form.currentdonordata = DonorData(donorid=donorid, token=token, isforupdate=False)

    if request.method == 'GET':
        # This is from the redirect from the login page.
        # Populate the edit form with current metadata for the donor.
        setdefaults(form)

    if request.method == 'POST' and form.validate():
        # Translate revised donor metadata fields into the encoded donor metadata schema.

        form.newdonordata = buildnewdonordata(form, token=token, donorid=donorid)

        # Prepare a base64-encoded string version of the new metadata dictionary that will be decoded
        # by the review.html for the update post to entity-api.
        form.newdonor = base64.b64encode(pickle.dumps(form.newdonordata.metadata)).decode()  # Base64 encoded string

        # Add a second instance of the encoded dictionary for the export to tsv feature, which requires
        # an additional form inside the export_review.html.
        # Flatten the dictionary for export.

        form.newdonortsv = base64.b64encode(pickle.dumps(form.newdonordata.metadata)).decode()

        # Identify all differences between the current and new donor metadata.
        if form.currentdonordata.metadata is None:
            form.deepdiff = {'Change': 'from no metadata to some metadata'}
        else:
            diff = deepdiff.DeepDiff(form.currentdonordata.metadata, form.newdonordata.metadata)
            if diff == {}:
                # A return of None is translated by review.html as no change.
                form.deepdiff = None
            else:
                form.deepdiff = json.loads(diff.to_json())

        # Pass existing and changed metadata to the review/update form.
        return render_template('review.html', donorid=donorid,
                               form=form)
    else:
        # Donor id
        form.donorid.data = form.currentdonordata.donorid
        setinputdisabled(form.donorid, disabled=True)

        # Consortium
        form.consortium.data = form.currentdonordata.consortium
        setinputdisabled(form.consortium, disabled=True)

    return render_template('edit.html', donorid=donorid, form=form)


def setdefaults(form):
    """
    Sets default values in form fields.

    """

    # The donor id (and by extension the consortium) are passed to the form via the search form. The fields
    # will be read-only.

    # Donor id
    form.donorid.data = form.currentdonordata.donorid
    setinputdisabled(form.donorid, disabled=True)

    # Consortium
    form.consortium.data = form.currentdonordata.consortium
    setinputdisabled(form.consortium, disabled=True)

    # Set defaults for SelectFields, using either the current metadata values for the user or:
    # 1. default UMLS CUIs for required fields
    # 2. 'PROMPT' for optional fields
    # 3. default unit for unit fields

    # Age
    # The Age valueset has its own tab.
    age_concept = form.valuesetmanager.getcolumnvalues(tab='Age', col='concept_id')[0]
    age_grouping_concept = 'C0001779'
    agelist = form.currentdonordata.getmetadatavalues(list_concept=age_concept,
                                                      grouping_concept=age_grouping_concept, key='data_value')
    if len(agelist) > 0:
        form.agevalue.data = float(agelist[0])

    # Age Units
    # The default age unit is years.
    ageunitlist = form.currentdonordata.getmetadatavalues(grouping_concept=age_grouping_concept, key='units')
    if len(ageunitlist) > 0:
        form.ageunit.data = ageunitlist[0]
    else:
        form.ageunit.data = 'C0001779'  # years

    # Race
    # The Race valueset has its own tab. The default value is Unknown.
    race_grouping_concept = form.valuesetmanager.getcolumnvalues(tab='Race', col='grouping_concept')[0]
    print(race_grouping_concept)
    racelist = form.currentdonordata.getmetadatavalues(grouping_concept=race_grouping_concept, key='concept_id')
    print(racelist)
    if len(racelist) > 0:
        form.race.data = racelist[0]
    else:
        form.race.data = 'C0439673'  # Unknown

    # Ethnicity
    # The Ethnicity valueset has its own tab. There is no default value.
    eth_grouping_concept = form.valuesetmanager.getcolumnvalues(tab='Ethnicity', col='grouping_concept')[0]
    ethlist = form.currentdonordata.getmetadatavalues(grouping_concept=eth_grouping_concept, key='concept_id')
    if len(ethlist) > 0:
        form.ethnicity.data = ethlist[0]
    else:
        form.ethnicity.data = 'PROMPT'

    # Sex
    # The Sex valueset has its own tab. The default value is Unknown.
    sex_grouping_concept = form.valuesetmanager.getcolumnvalues(tab='Sex', col='grouping_concept')[0]
    sexlist = form.currentdonordata.getmetadatavalues(grouping_concept=sex_grouping_concept, key='concept_id')
    if len(sexlist) > 0:
        form.sex.data = sexlist[0]
    else:
        form.sex.data = 'C0421467'  # Unknown

    # Source name
    # The source name is not encoded in a valueset.
    # The source name is the first key of the metadata dictionary, and can be either 'living_donor_data'
    # or 'organ_donor_data'.
    if form.currentdonordata.metadata is not None:
        source = 'living_donor_data'
        if source in form.currentdonordata.metadata.keys():
            form.source.data = '0'
        else:
            source = 'organ_donor_data'
            if source in form.currentdonordata.metadata.keys():
                form.source.data = '1'
            else:
                abort(500,'Unknown donor metadata key')
    else:
        # No existing metadata.
        form.source.data = 'PROMPT'

    # Cause of Death
    # The Cause of Death valueset has its own tab. There is no default value.
    cod_concepts = form.valuesetmanager.getcolumnvalues(tab='Cause of Death', col='concept_id')
    grouping_concept = 'C0007465'  # Cause of Death
    codlist = form.currentdonordata.getmetadatavalues(list_concept=cod_concepts,
                                                      grouping_concept=grouping_concept, key='concept_id')
    if len(codlist) > 0:
        form.cause.data = codlist[0]
    else:
        form.cause.data = 'PROMPT'

    # Mechanism of Injury
    # The Mechanism of Injury valueset has its own tab. There is no default value.
    # mech_grouping_concept = form.valuesetmanager.getcolumnvalues(tab='Mechanism of Injury',
    # col='grouping_concept')[0]
    # mechlist = form.currentdonordata.getmetadatavalues(grouping_concept=mech_grouping_concept, key='concept_id')

    # Future development note: Some existing donor records use an incorrect grouping_concept_id for
    # mechanism of injury. After these donors are corrected, change mech_concepts to use group_concept.
    mech_concepts = form.valuesetmanager.getcolumnvalues(tab='Mechanism of Injury', col='concept_id')
    grouping_concept = 'C0449413'  # Mechanism of Injury
    mechlist = form.currentdonordata.getmetadatavalues(list_concept=mech_concepts,
                                                       grouping_concept=grouping_concept, key='concept_id')
    if len(mechlist) > 0:
        form.mechanism.data = mechlist[0]
    else:
        form.mechanism.data = 'PROMPT'

    # Death Event
    # The Death Event valueset has its own tab. There is no default value.
    # event_grouping_concept = form.valuesetmanager.getcolumnvalues(tab='Death Event', col='grouping_concept')[0]
    # eventlist = form.currentdonordata.getmetadatavalues(grouping_concept=event_grouping_concept, key='concept_id')
    event_concepts = form.valuesetmanager.getcolumnvalues(tab='Death Event', col='concept_id')
    grouping_concept = 'C0011065'  # Death Event
    eventlist = form.currentdonordata.getmetadatavalues(list_concept=event_concepts,
                                                        grouping_concept=grouping_concept, key='concept_id')
    if len(eventlist) > 0:
        form.event.data = eventlist[0]
    else:
        form.event.data = 'PROMPT'

    # Height
    # The Height valueset has only one concept, on the "Measurements" tab.
    height_concept = 'C0005890'
    heightvaluelist = form.currentdonordata.getmetadatavalues(grouping_concept=height_concept, key='data_value')
    if len(heightvaluelist) > 0:
        form.heightvalue.data = float(heightvaluelist[0])

    # Height unit
    # The Height unit is currently linked to the Height valueset, and has a default of cm.
    heightunitlist = form.currentdonordata.getmetadatavalues(grouping_concept=height_concept, key='units')

    if len(heightunitlist) > 0:
        # Translate the metadata value into its corresponding selection in the list. Convert known variances in
        # unit.
        dictchoices = dict(form.heightunit.choices)
        if heightunitlist[0] == 'inches':
            heightunitlist[0] = 'in'
        if heightunitlist[0] not in ['in', 'cm']:
            form.heightunit.data = '0'  # cm
        else:
            form.heightunit.data = list(dictchoices.keys())[list(dictchoices.values()).index(heightunitlist[0])]
    else:
        form.heightunit.data = '0'  # cm

    # Weight
    # The Weight valueset has only one concept, on the "Measurements" tab.
    weight_concept = 'C0005910'
    weightvaluelist = form.currentdonordata.getmetadatavalues(grouping_concept=weight_concept, key='data_value')
    if len(weightvaluelist) > 0:
        form.weightvalue.data = float(weightvaluelist[0])

    # Weight unit
    # The Weight unit is currently linked to the Height valueset, and has a default of kg.
    weightunitlist = form.currentdonordata.getmetadatavalues(grouping_concept=weight_concept, key='units')
    if len(weightunitlist) > 0:
        # Translate the metadata value into its corresponding selection in the list. Convert known variances in
        # unit.
        dictchoices = dict(form.weightunit.choices)
        print(dictchoices)
        if weightunitlist[0] == 'pounds':
            weightunitlist[0] = 'lb'
        if weightunitlist[0] not in ['lb', 'kg']:
            form.heightunit.data = '0'  # cm
        else:
            form.weightunit.data = list(dictchoices.keys())[list(dictchoices.values()).index(weightunitlist[0])]
    else:
        form.weightunit.data = '0'  # kg

    # Body Mass Index
    # The BMI has no default value.
    bmi_concept = 'C1305855'
    bmilist = form.currentdonordata.getmetadatavalues(grouping_concept=bmi_concept, key='data_value')
    if len(bmilist) > 0:
        form.bmi.data = float(bmilist[0])

    # ABO Blood Type
    # The ABO Blood type is categorical. Its valueset is a subset of rows on the "Blood Type" tab.
    bloodtype_grouping_concept = 'C0000778'
    bloodtypelist = form.currentdonordata.getmetadatavalues(grouping_concept=bloodtype_grouping_concept,
                                                            key='concept_id')
    if len(bloodtypelist) > 0:
        form.bloodtype.data = bloodtypelist[0]
    else:
        form.bloodtype.data = 'PROMPT'

    # Rh Blood Group
    # The RH Blood Group is categorical. Its valueset is a subset of rows on the "Blood Type" tab.
    bloodrh_grouping_concept = 'C0035406'
    bloodrhlist = form.currentdonordata.getmetadatavalues(grouping_concept=bloodrh_grouping_concept, key='concept_id')
    if len(bloodrhlist) > 0:
        form.bloodrh.data = bloodrhlist[0]
    else:
        form.bloodrh.data = 'PROMPT'

    # Waist Circumference
    # The Waist Circumference valueset has only one concept, on the "Measurements" tab.
    waist_concept = 'C0455829'
    waistvaluelist = form.currentdonordata.getmetadatavalues(grouping_concept=waist_concept, key='data_value')
    if len(waistvaluelist) > 0:
        form.waistvalue.data = float(waistvaluelist[0])

    # Waist Circumference unit
    # The Waist Circumference unit is currently linked to the Height valueset, and has a default of cm.
    # Convert known variances in unit.
    waistunitlist = form.currentdonordata.getmetadatavalues(grouping_concept=waist_concept, key='units')
    if len(waistunitlist) > 0:
        # Translate the metadata value into its corresponding selection in the list.
        dictchoices = dict(form.waistunit.choices)
        if waistunitlist[0] == 'inches':
            waistunitlist[0] = 'in'
        if waistunitlist[0] not in ['in', 'cm']:
            form.heightunit.data = '0'  # cm
        else:
            form.waistunit.data = list(dictchoices.keys())[list(dictchoices.values()).index(waistunitlist[0])]
    else:
        form.waistunit.data = '0'  # cm

    # Age at menarche
    # The age at menarche has no default value.
    agemenarche_concept = 'C1314691'
    agemenarchelist = form.currentdonordata.getmetadatavalues(grouping_concept=agemenarche_concept, key='data_value')
    if len(agemenarchelist) > 0:
        form.agemenarche.data = float(agemenarchelist[0])

    # Age at first birth
    # The age at first birth has no default value.
    agefirstbirth_concept = 'C1510831'
    agefirstbirthlist = form.currentdonordata.getmetadatavalues(grouping_concept=agefirstbirth_concept,
                                                                key='data_value')
    if len(agefirstbirthlist) > 0:
        form.agefirstbirth.data = float(agefirstbirthlist[0])

    # Gestational age
    # The gestational age has no default value.
    gestationalage_concept = 'C0017504'
    gestationalagelist = form.currentdonordata.getmetadatavalues(grouping_concept=gestationalage_concept,
                                                                 key='data_value')
    if len(gestationalagelist) > 0:
        form.gestationalage.data = float(gestationalagelist[0])

    # KDPI
    # The KDPI has no default value.
    kdpi_concept = 'C4330523'
    kdpilist = form.currentdonordata.getmetadatavalues(grouping_concept=kdpi_concept, key='data_value')
    if len(kdpilist) > 0:
        form.kdpi.data = float(kdpilist[0])

    # Cancer risk
    # The Cancer risk has no default value.
    cancer_concept = 'C0596244'
    cancerlist = form.currentdonordata.getmetadatavalues(grouping_concept=cancer_concept, key='data_value')
    if len(cancerlist) > 0:
        form.cancerrisk.data = float(cancerlist[0])

    # Hba1c
    # The Hba1c has no default value.
    hba1c_concept = 'C2707530'
    hba1clist = form.currentdonordata.getmetadatavalues(grouping_concept=hba1c_concept, key='data_value')
    if len(hba1clist) > 0:
        form.hba1c.data = float(hba1clist[0])

    # Amylase
    # The Amylase has no default value.
    amylase_concept = 'C0201883'
    amlyaselist = form.currentdonordata.getmetadatavalues(grouping_concept=amylase_concept, key='data_value')
    if len(amlyaselist) > 0:
        form.amylase.data = float(amlyaselist[0])

    # Lipase
    # The Lipase has no default value.
    lipase_concept = 'C0373670'
    lipaselist = form.currentdonordata.getmetadatavalues(grouping_concept=lipase_concept, key='data_value')
    if len(lipaselist) > 0:
        form.lipase.data = float(lipaselist[0])

    # eGFR
    # The eGFR has no default value.
    egfr_concept = 'C3274401'
    egfrlist = form.currentdonordata.getmetadatavalues(grouping_concept=egfr_concept, key='data_value')
    if len(egfrlist) > 0:
        form.egfr.data = float(egfrlist[0])

    # Serum creatinine
    # No default value.
    secr_concept = 'C0600061'
    secrlist = form.currentdonordata.getmetadatavalues(grouping_concept=secr_concept, key='data_value')
    if len(secrlist) > 0:
        form.secr.data = float(secrlist[0])

    # Pathology note
    # The Pathology note has no default value.
    path_concept = 'C0807321'
    pathlist = form.currentdonordata.getmetadatavalues(grouping_concept=path_concept, key='data_value')
    if len(pathlist) > 0:
        form.pathologynote.data = pathlist[0]

    # APOE phenotype
    # The APOE phenotype has no default value.
    apoe_concept = 'C0428504'
    apoelist = form.currentdonordata.getmetadatavalues(grouping_concept=apoe_concept, key='data_value')
    if len(apoelist) > 0:
        form.apoephenotype.data = apoelist[0]

    # Fitzpatrick Skin Type
    # The Fitzpatrick scale is categorical. For the original set of donors that had Fitzpatrick scores,
    # the grouping concept was the same as the valueset concept, so it is necessary to build a group of
    # concepts manually. If these donors are re-ingested with the corrected valuesets, the logic
    # can revert to using a common grouping_concept.
    fitz_concepts = ['C2700185', 'C2700186', 'C2700187', 'C2700188', 'C2700189', 'C2700190']
    fitzlist = form.currentdonordata.getmetadatavalues(list_concept=fitz_concepts, key='concept_id')
    if len(fitzlist) > 0:
        form.fitzpatrick.data = fitzlist[0]
    else:
        form.fitzpatrick.data = 'PROMPT'

    # Other Anatomic Site
    # Other Anatomic Site is categorical.
    other_anatomical_concepts = ['C4331357']
    otherlist = form.currentdonordata.getmetadatavalues(list_concept=other_anatomical_concepts,
                                                        grouping_concept='C1518643', key='concept_id')
    if len(otherlist) > 0:
        form.other_anatomic.data = otherlist[0]
    else:
        form.other_anatomic.data = 'PROMPT'

    # Smoking
    # Smoking is categorical. Its valueset is a subset of rows on the "Social History" tab. The
    # valueset concepts do not share a grouping concept.
    smoking_concepts = ['C0337664', 'C0337672', 'C0337671']
    grouping_concept = 'C0424945'
    smokinglist = form.currentdonordata.getmetadatavalues(list_concept=smoking_concepts,
                                                          grouping_concept=grouping_concept, key='concept_id')
    if len(smokinglist) > 0:
        form.smoking.data = smokinglist[0]
    else:
        form.smoking.data = 'PROMPT'

    # Tobacco
    # Tobacco is categorical. Its valueset is a subset of rows on the "Social History" tab. The
    # valueset concepts do not share a grouping concept.
    tobacco_concepts = ['C3853727']
    grouping_concept = 'C0424945'
    tobaccolist = form.currentdonordata.getmetadatavalues(list_concept=tobacco_concepts,
                                                          grouping_concept=grouping_concept, key='concept_id')
    if len(tobaccolist) > 0:
        form.tobacco.data = tobaccolist[0]
    else:
        form.tobacco.data = 'PROMPT'

    # Alcohol
    # Alcohol is categorical. Its valueset is a subset of rows on the "Social History" tab. The
    # valueset concepts do not share a grouping concept.
    alcohol_concepts = ['C0001948', 'C0457801']
    grouping_concept = 'C0424945'
    alcohollist = form.currentdonordata.getmetadatavalues(list_concept=alcohol_concepts,
                                                          grouping_concept=grouping_concept, key='concept_id')
    if len(alcohollist) > 0:
        form.alcohol.data = alcohollist[0]
    else:
        form.alcohol.data = 'PROMPT'

    # Drug
    # Drug is categorical. Its valueset is a subset of rows on the "Social History" tab. The
    # valueset concepts do not share a grouping concept.
    drug_concepts = ['C4518790', 'C0524662', 'C0242566', 'C1456624', 'C3266350',
                     'C0281875', 'C0013146', 'C0239076']
    grouping_concept = 'C0424945'
    druglist = form.currentdonordata.getmetadatavalues(list_concept=drug_concepts,
                                                       grouping_concept=grouping_concept, key='concept_id')
    if len(druglist) > 0:
        form.drug.data = druglist[0]
    else:
        form.drug.data = 'PROMPT'

    # Medical History
    # The Medical History valueset has its own tab. There is no default value.
    # Display information for up to 10 conditions.
    formmedhxdata = [form.medhx_0, form.medhx_1,
                     form.medhx_2, form.medhx_3,
                     form.medhx_4, form.medhx_5,
                     form.medhx_6, form.medhx_7,
                     form.medhx_8, form.medhx_9]
    # Future development note: Some existing records incorrectly use concept_id for grouping_concept_id. After
    # these donors are corrected, change medhxlist to use group_concept.
    medhx_concepts = form.valuesetmanager.getcolumnvalues(tab='Medical History', col='concept_id')
    grouping_concept = 'C0262926'
    medhxlist = form.currentdonordata.getmetadatavalues(list_concept=medhx_concepts,
                                                        grouping_concept=grouping_concept, key='concept_id')

    for medhx in medhxlist:
        idx = medhxlist.index(medhx)
        if idx < 10:
            formmedhxdata[idx].data = medhx

    # Set defaults for any medhx list that was not set by donor data.
    for m in range(len(medhxlist), 10):
        formmedhxdata[m].data = 'PROMPT'

    # Error conditions that result in disabling of the form.
    has_error = False

    if len(medhxlist) > 10:
        msg = (f'Donor {form.currentdonordata.donorid} currently has more than 10 Medical History Conditions. '
               f'Edit manually.')
        flash(msg)
        has_error = True

    #if form.currentdonordata.descendantcount > 10:
        #msg = (f'Donor {form.currentdonordata.donorid} is associated with {form.currentdonordata.descendantcount} descendants.')
        #flash(msg)
        # has_error = True
    #elif form.currentdonordata.has_published_datasets:
        #msg = (f'Donor {form.currentdonordata.donorid} is associated with one or more published datasets.')
        #flash(msg)
        # has_error = True

    if len(heightunitlist) > 0:
        if heightunitlist[0] not in ['in', 'cm']:
            msg = (f'Donor {form.currentdonordata.donorid} has metadata with an unexpected height '
                   f'unit {heightunitlist[0]}. Edit manually.')
            flash(msg)
            has_error = True

    if len(weightunitlist) > 0:
        if weightunitlist[0] not in ['lb', 'kg']:
            msg = (f'Donor {form.currentdonordata.donorid} has metadata with an unexpected weight '
                   f'unit {weightunitlist[0]}. Edit manually.')
            flash(msg)
            has_error = True

    if len(waistunitlist) > 0:
        if waistunitlist[0] not in ['in', 'cm']:
            msg = (f'Donor {form.currentdonordata.donorid} has metadata with an unexpected waist '
                   f'circumference unit {waistunitlist[0]}. Edit manually.')
            flash(msg)
            has_error = True

    if has_error:
        for field in form:
            setinputdisabled(field, disabled=True)


def translate_age_to_metadata(form) -> dict:
    """
    Translates the combination of age and age unit fields in the Edit form to a metadata dict.

    Age differs from other valuesets in that the age unit field actually encodes the valueset.

    Numeric values in the donor
    metadata object are strings.
    :param form: the edit form
    :return: dict
    """

    agevalue = form.agevalue.data
    # Units are not encoded in metadata.
    unit_concept_id = form.ageunit.data
    dictvalueset = form.valuesetmanager.getvaluesetrow(tab='Age', concept_id=unit_concept_id)
    dictvalueset['data_value'] = str(agevalue)
    return dictvalueset


def translate_selectfield_to_metadata(form, formfield: SelectField, tab: str) -> dict:
    """
    Translates a SelectField value to metadata.
    :param form: the edit form
    :param formfield: the field
    :param tab: tab in the valueset sheet
    :return: dict
    """

    # Get the concept for the selected value. The concept is the choice, not the data.
    concept_id = formfield.data
    if concept_id == 'PROMPT':
        return {}

    return form.valuesetmanager.getvaluesetrow(tab=tab, concept_id=concept_id)


def translate_field_value_to_metadata(form, formfield: Field, tab: str, concept_id, unitfield=None) -> dict:
    """
        Translates a combination of value and unit fields in the Edit form to a metadata dict.

        Converts to metric units.

        Corrects legacy data entry issues with respect to:
        1. Medical History

        Numeric values in the donor
        metadata object are strings.
        :param form: the edit form
        :param formfield: field in a form
        :param unitfield: optional field for unit.
        :param tab: tab on the valueset manager sheet
        :param concept_id: concept id for the value in the tab
        :return: dict
        """

    if formfield.data is None:
        return {}
    if formfield.data == '':
        return {}

    # Get schema information for metadata from valueset.
    dictvalueset = form.valuesetmanager.getvaluesetrow(tab=tab, concept_id=concept_id)

    # Get values from form.
    value = formfield.data

    # Unit is not encoded.
    if unitfield is None:
        # Look for a default unit.
        dictdefaultunit = form.valuesetmanager.getvaluesetrow(tab='Measurements',concept_id=concept_id)
        if dictdefaultunit == {}:
            abort(500,f'Valueset manager does not have default units for field {form.formfield.name}')
        else:
            unit_value=dictdefaultunit['units']
    else:
        unit_value = dict(unitfield.choices).get(unitfield.data)

    # Convert to metric:
    # 1. Height
    # 2. Weight
    # 3. Waist circumfernce
    if concept_id in ['C0005890', 'C0455829']:
        if unitfield.data == '1':  # in
            unit_value = 'cm'
            value = round(float(value) * 2.54,2)

    if concept_id == 'C0005910':
        if unitfield.data == '1':  # lb
            unit_value = 'kg'
            value = round(float(value) / 2.2,2)


    # Some legacy metadata incorrectly coded:
    # 1. Race
    # 2. Sex
    # 3. Medical History
    if formfield.name in ['race', 'sex', 'medhx']:
        dictvalueset['data_value'] = dictvalueset['preferred_term']


    dictvalueset['data_value'] = str(value)
    dictvalueset['units'] = unit_value

    return dictvalueset


def buildnewdonordata(form, token: str, donorid: str) -> DonorData:

    """
    Builds a new DonorData object from form data. This includes populating a list of metadata dicts.
    :param form: a WTForms Form object
    :param donorid: donor id
    :param token: globus groups_token for consortium entity-api
    :return: a DonorData object.
    """
    donor = DonorData(donorid=donorid, token=token, isforupdate=True)

    # organ_donor_data or living_donor_data key.
    donor_data_key = dict(form.source.choices).get(form.source.data)
    donor.metadata[donor_data_key] = []

    # Age
    age = translate_age_to_metadata(form)
    if age != {}:
        donor.metadata[donor_data_key].append(age)

    # Race
    race = translate_selectfield_to_metadata(form, formfield=form.race, tab='Race')
    if race != {}:
        donor.metadata[donor_data_key].append(race)

    # Ethnicity
    ethnicity = translate_selectfield_to_metadata(form, formfield=form.ethnicity, tab='Ethnicity')
    if ethnicity != {}:
        donor.metadata[donor_data_key].append(ethnicity)

    # Sex
    sex = translate_selectfield_to_metadata(form, formfield=form.sex, tab='Sex')
    if sex != {}:
        donor.metadata[donor_data_key].append(sex)

    # Cause of Death
    cause = translate_selectfield_to_metadata(form, formfield=form.cause, tab='Cause of Death')
    if cause != {}:
        donor.metadata[donor_data_key].append(cause)

    # Mechanism of Injury
    mechanism = translate_selectfield_to_metadata(form, formfield=form.mechanism, tab='Mechanism of Injury')
    if mechanism != {}:
        donor.metadata[donor_data_key].append(mechanism)

    # Death Event
    event = translate_selectfield_to_metadata(form, formfield=form.event, tab='Death Event')
    if event != {}:
        donor.metadata[donor_data_key].append(event)

    # Height
    height = translate_field_value_to_metadata(form, formfield=form.heightvalue, unitfield=form.heightunit,
                                               tab='Measurements', concept_id='C0005890')
    if height != {}:
        donor.metadata[donor_data_key].append(height)

    # Weight
    weight = translate_field_value_to_metadata(form, formfield=form.weightvalue, unitfield=form.weightunit,
                                               tab='Measurements', concept_id='C0005910')
    if weight != {}:
        donor.metadata[donor_data_key].append(weight)

    # BMI
    bmi = translate_field_value_to_metadata(form, formfield=form.bmi, tab='Measurements', concept_id='C1305855')
    if bmi != {}:
        donor.metadata[donor_data_key].append(bmi)


    # waist circumference
    waist = translate_field_value_to_metadata(form, formfield=form.waistvalue, unitfield=form.waistunit,
                                              tab='Measurements', concept_id='C0455829')
    if waist != {}:
        donor.metadata[donor_data_key].append(waist)

    # KDPI
    kdpi = translate_field_value_to_metadata(form, formfield=form.kdpi, tab='Measurements', concept_id='C4330523')
    if kdpi != {}:
        donor.metadata[donor_data_key].append(kdpi)

    # Hba1c
    hba1c = translate_field_value_to_metadata(form, formfield=form.hba1c, tab='Measurements', concept_id='C2707530')
    if hba1c != {}:
        donor.metadata[donor_data_key].append(hba1c)

    # amylase
    amylase = translate_field_value_to_metadata(form, formfield=form.amylase, tab='Measurements',
                                                concept_id='C0201883')
    if amylase != {}:
        donor.metadata[donor_data_key].append(amylase)

    # lipase
    lipase = translate_field_value_to_metadata(form, formfield=form.lipase, tab='Measurements',
                                               concept_id='C0373670')
    if lipase != {}:
        donor.metadata[donor_data_key].append(lipase)

    # eGFR
    egfr = translate_field_value_to_metadata(form, formfield=form.lipase, tab='Measurements',
                                             concept_id='C3274401')
    if egfr != {}:
        donor.metadata[donor_data_key].append(egfr)

    # Creatinine
    secr = translate_field_value_to_metadata(form, formfield=form.lipase, tab='Measurements',
                                             concept_id='C0600061')
    if secr != {}:
        donor.metadata[donor_data_key].append(secr)

    # age at menarche
    agemenarche = translate_field_value_to_metadata(form, formfield=form.agemenarche, tab='Measurements',
                                                    concept_id='C1314691')
    if agemenarche != {}:
        donor.metadata[donor_data_key].append(agemenarche)

    # age at first birth
    agefirstbirth = translate_field_value_to_metadata(form, formfield=form.agefirstbirth, tab='Measurements',
                                                      concept_id='C1510831')
    if agefirstbirth != {}:
        donor.metadata[donor_data_key].append(agefirstbirth)

    # gestational age
    gestationalage = translate_field_value_to_metadata(form, formfield=form.gestationalage, tab='Measurements',
                                                       concept_id='C0017504')
    if gestationalage != {}:
        donor.metadata[donor_data_key].append(gestationalage)

    # cancer risk
    cancerrisk = translate_field_value_to_metadata(form, formfield=form.cancerrisk, tab='Measurements',
                                                   concept_id='C0596244')
    if cancerrisk != {}:
        donor.metadata[donor_data_key].append(cancerrisk)

    # Pathology note
    pathologynote = translate_field_value_to_metadata(form, formfield=form.pathologynote, tab='Measurements',
                                                      concept_id='C0807321')
    if pathologynote != {}:
        donor.metadata[donor_data_key].append(pathologynote)

    # Apolipoprotein E phenotype
    apoephenotype = translate_field_value_to_metadata(form, formfield=form.apoephenotype, tab='Measurements',
                                                      concept_id='C0428504')
    if apoephenotype != {}:
        donor.metadata[donor_data_key].append(apoephenotype)

    # Fitzpatrick Skin Type
    fitzpatrick = translate_selectfield_to_metadata(form, formfield=form.fitzpatrick, tab='Measurements')
    if fitzpatrick != {}:
        donor.metadata[donor_data_key].append(fitzpatrick)

    # Other Anatomic Site
    other_anatomic = translate_selectfield_to_metadata(form, formfield=form.other_anatomic, tab='Measurements')
    if other_anatomic != {}:
        donor.metadata[donor_data_key].append(other_anatomic)

    # Blood Type
    bloodtype = translate_selectfield_to_metadata(form, formfield=form.bloodtype, tab='Blood Type')
    if bloodtype != {}:
        donor.metadata[donor_data_key].append(bloodtype)

    # Blood Type
    bloodrh = translate_selectfield_to_metadata(form, formfield=form.bloodrh, tab='Blood Type')
    if bloodrh != {}:
        donor.metadata[donor_data_key].append(bloodrh)

    # Smoking status
    smoking = translate_selectfield_to_metadata(form, formfield=form.smoking, tab='Social History')
    if smoking != {}:
        donor.metadata[donor_data_key].append(smoking)

    # Tobacco use
    tobacco = translate_selectfield_to_metadata(form, formfield=form.tobacco, tab='Social History')
    if tobacco != {}:
        donor.metadata[donor_data_key].append(tobacco)

    # Alcohol use
    alcohol = translate_selectfield_to_metadata(form, formfield=form.alcohol, tab='Social History')
    if alcohol != {}:
        donor.metadata[donor_data_key].append(alcohol)

    # Drug use
    drug = translate_selectfield_to_metadata(form, formfield=form.drug, tab='Social History')
    if drug != {}:
        donor.metadata[donor_data_key].append(drug)

    # Medical History - up to 10 conditions.
    for field in form:
        if 'medhx' in field.name:
            medhx = translate_selectfield_to_metadata(form, formfield=field, tab='Medical History')
            if medhx != {}:
                donor.metadata[donor_data_key].append(medhx)

    return donor
