# Context login form
from flask import Blueprint, request, render_template, jsonify, abort
from wtforms import Field, DecimalField, SelectField

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
    form.currentdonordata = DonorData(donorid=donorid, consortium=consortium, token=form.token)

    # Age
    # The Age valueset has its own tab.
    age_grouping_concept = form.valuesetmanager.getcolumnvalues(tab='Age', col='grouping_concept')[0]
    agelist = form.currentdonordata.getmetadatavalues(grouping_concept=age_grouping_concept, key='data_value')
    if len(agelist) > 0:
        form.agevalue.data = float(agelist[0])

    # Age Units
    # The default age unit is years.
    ageunitlist = form.currentdonordata.getmetadatavalues(grouping_concept=age_grouping_concept, key='units')
    if len(ageunitlist) > 0:
        form.ageunits.data = ageunitlist[0]
    else:
        form.ageunits.data = 'C0001779'  # years

    # Race
    # The Race valueset has its own tab. The default value is Unknown.
    race_grouping_concept = form.valuesetmanager.getcolumnvalues(tab='Race', col='grouping_concept')[0]
    racelist = form.currentdonordata.getmetadatavalues(grouping_concept=race_grouping_concept, key='concept_id')
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
    # The source name is not encoded in a valuset.
    if form.currentdonordata.metadata_type == 'living_donor_data':
        form.source.data = '0'
    elif form.currentdonordata.metadata_type == 'organ_donor_data':
        form.source.data = '1'
    else:
        form.source.data = 'PROMPT'

    # Cause of Death
    # The Cause of Death valueset has its own tab. There is no default value.
    # cod_grouping_concept = form.valuesetmanager.getcolumnvalues(tab='Cause of Death', col='grouping_concept')[0]
    # codlist = form.currentdonordata.getmetadatavalues(grouping_concept=cod_grouping_concept, key='concept_id')
    cod_concepts = form.valuesetmanager.getcolumnvalues(tab='Cause of Death', col='concept_id')
    codlist = form.currentdonordata.getmetadatavalues(list_concept=cod_concepts, key='concept_id')
    if len(codlist) > 0:
        form.cause.data = codlist[0]
    else:
        form.cause.data = 'PROMPT'

    # Mechanism of Injury
    # The Mechanism of Injury valueset has its own tab. There is no default value.
    # mech_grouping_concept = form.valuesetmanager.getcolumnvalues(tab='Mechanism of Injury', col='grouping_concept')[0]
    # mechlist = form.currentdonordata.getmetadatavalues(grouping_concept=mech_grouping_concept, key='concept_id')

    # Future development note: Some existing donor records use an incorrect grouping_concept_id for mechanism of injury. After
    # these donors are corrected, change medhxlist to use group_concept.
    mech_concepts = form.valuesetmanager.getcolumnvalues(tab='Mechanism of Injury', col='concept_id')
    mechlist = form.currentdonordata.getmetadatavalues(list_concept=mech_concepts, key='concept_id')
    if len(mechlist) > 0:
        form.mechanism.data = mechlist[0]
    else:
        form.mechanism.data = 'PROMPT'

    # Death Event
    # The Death Event valueset has its own tab. There is no default value.
    # event_grouping_concept = form.valuesetmanager.getcolumnvalues(tab='Death Event', col='grouping_concept')[0]
    # eventlist = form.currentdonordata.getmetadatavalues(grouping_concept=event_grouping_concept, key='concept_id')
    event_concepts = form.valuesetmanager.getcolumnvalues(tab='Death Event', col='concept_id')
    eventlist = form.currentdonordata.getmetadatavalues(list_concept=event_concepts, key='concept_id')
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
        # Translate the metadata value into its corresponding selection in the list.
        dictchoices = dict(form.heightunit.choices)
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
        # Translate the metadata value into its corresponding selection in the list.
        dictchoices = dict(form.weightunit.choices)
        form.weightunit.data = list(dictchoices.keys())[list(dictchoices.values()).index(weightunitlist[0])]

    else:
        form.heightunit.data = '0'  # kg

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
    waistunitlist = form.currentdonordata.getmetadatavalues(grouping_concept=waist_concept, key='units')
    if len(waistunitlist) > 0:
        # Translate the metadata value into its corresponding selection in the list.
        dictchoices = dict(form.waistunit.choices)
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

    # Smoking
    # Smoking is categorical. Its valueset is a subset of rows on the "Social History" tab. The
    # valueset concepts do not share a grouping concept.
    smoking_concepts = ['C0337664', 'C0337672', 'C0337671']
    smokinglist = form.currentdonordata.getmetadatavalues(list_concept=smoking_concepts, key='concept_id')
    if len(smokinglist) > 0:
        form.smoking.data = smokinglist[0]
    else:
        form.smoking.data = 'PROMPT'

    # Tobacco
    # Tobacco is categorical. Its v
    # alueset is a subset of rows on the "Social History" tab. The
    # valueset concepts do not share a grouping concept.
    tobacco_concepts = ['C3853727']
    tobaccolist = form.currentdonordata.getmetadatavalues(list_concept=tobacco_concepts, key='concept_id')
    if len(tobaccolist) > 0:
        form.tobacco.data = tobaccolist[0]
    else:
        form.tobacco.data = 'PROMPT'

    # Alcohol
    # Alcohol is categorical. Its valueset is a subset of rows on the "Social History" tab. The
    # valueset concepts do not share a grouping concept.
    alcohol_concepts = ['C0001948', 'C0457801']
    alcohollist = form.currentdonordata.getmetadatavalues(list_concept=alcohol_concepts, key='concept_id')
    if len(alcohollist) > 0:
        form.alcohol.data = alcohollist[0]
    else:
        form.alcohol.data = 'PROMPT'

    # Drug
    # Drug is categorical. Its valueset is a subset of rows on the "Social History" tab. The
    # valueset concepts do not share a grouping concept.
    drug_concepts = ['C4518790', 'C0524662', 'C0242566', 'C1456624', 'C3266350',
                     'C0281875', 'C0013146', 'C0239076']
    druglist = form.currentdonordata.getmetadatavalues(list_concept=drug_concepts, key='concept_id')
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
    medhxlist = form.currentdonordata.getmetadatavalues(list_concept=medhx_concepts, key='concept_id')

    if len(medhxlist) > 10:
        msg = f'Donor {donorid} has more than 10 Medical History Conditions. Edit manually.'
        abort(400, msg)

    for medhx in medhxlist:
        idx = medhxlist.index(medhx)
        formmedhxdata[idx].data = medhx

    # Set defaults for any medhx list that was not set by donor data.
    for m in range(len(medhxlist), 10):
        formmedhxdata[m].data = 'PROMPT'


def translate_age_to_metadata(form, formfield: DecimalField, formunitfield: SelectField) -> dict:
    """
    Translates the combination of age and age unit fields in the Edit form to a metadata dict.

    Age differs from other valuesets in that the age unit field actually encodes the valueset.

    Numeric values in the donor
    metadata object are strings.
    :param form: the edit form
    :param formfield: field in a form
    :param formunitfield: optional field for unit.
    :return: dict
    """

    agevalue = formfield.data
    # Units are not encoded in metadata.
    unit_concept_id = formunitfield.data
    dictvalueset = form.valuesetmanager.getvaluesetrow(tab='Age', concept_id=unit_concept_id)
    dictvalueset['datavalue'] = str(agevalue)
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
        return None

    return form.valuesetmanager.getvaluesetrow(tab=tab, concept_id=concept_id)

def translate_field_value_to_metadata(form, formfield: Field, tab: str, concept_id, unitfield=None) -> dict:
    """
        Translates a combination of value and unit fields in the Edit form to a metadata dict.

        Numeric values in the donor
        metadata object are strings.
        :param form: the edit form
        :param formfield: field in a form
        :param formunitfield: optional field for unit.
        :param tab: tab on the valueset manager sheet
        :param concept_id: concept id for the value in the tab
        :return: dict
        """

    if formfield.data is None:
        return None
    if formfield.data == '':
        return None

    value = formfield.data
    dictvalueset = form.valuesetmanager.getvaluesetrow(tab=tab, concept_id=concept_id)
    dictvalueset['data_value'] = str(value)

    if unitfield is not None:
        # Unit is not encoded.
        unit_value = dict(unitfield.choices).get(unitfield.data)
        dictvalueset['units'] = unit_value


    return dictvalueset



def buildnewdonordata(form) -> DonorData:

    """
    Builds a new DonorData object from form data. This includes populating a list of metadata dicts.
    :return: a DonorData object.
    """
    donor = DonorData(consortium=form.consortium.data, donorid=form.donorid, token=form.token, isforupdate=True)

    # organ_donor_data or living_donor_data key.
    donor_data_key = dict(form.source.choices).get(form.source.data)
    donor.metadata[donor_data_key] = []

    # Age
    age = translate_age_to_metadata(form, formfield=form.agevalue, formunitfield=form.ageunit)
    if age is not None:
        donor.metadata[donor_data_key].append(age)

    # Race
    race = translate_selectfield_to_metadata(form, formfield=form.race, tab='Race')
    if race is not None:
        donor.metadata[donor_data_key].append(race)

    # Ethnicity
    ethnicity = translate_selectfield_to_metadata(form, formfield=form.ethnicity, tab='Ethnicity')
    if ethnicity is not None:
        donor.metadata[donor_data_key].append(ethnicity)

    # Sex
    sex = translate_selectfield_to_metadata(form, formfield=form.sex, tab='Sex')
    if sex is not None:
        donor.metadata[donor_data_key].append(sex)

    # Cause of Death
    cause = translate_selectfield_to_metadata(form, formfield=form.cause, tab='Cause of Death')
    if cause is not None:
        donor.metadata[donor_data_key].append(cause)

    # Mechanism of Injury
    mechanism = translate_selectfield_to_metadata(form, formfield=form.mechanism, tab='Mechanism of Injury')
    if mechanism is not None:
        donor.metadata[donor_data_key].append(mechanism)

    # Death Event
    event = translate_selectfield_to_metadata(form, formfield=form.event, tab='Death Event')
    if event is not None:
        donor.metadata[donor_data_key].append(event)

    # Height
    height = translate_field_value_to_metadata(form, formfield=form.heightvalue, unitfield=form.heightunit,
                                                     tab='Measurements', concept_id='C0005890')
    if height is not None:
        donor.metadata[donor_data_key].append(height)

    # Weight
    weight = translate_field_value_to_metadata(form, formfield=form.weightvalue, unitfield=form.weightunit,
                                                     tab='Measurements', concept_id='C0005910')
    if weight is not None:
        donor.metadata[donor_data_key].append(weight)

    # BMI
    bmi = translate_field_value_to_metadata(form, formfield=form.bmi, tab='Measurements', concept_id='C1305855')
    if bmi is not None:
        donor.metadata[donor_data_key].append(bmi)

    # waist circumference
    waist = translate_field_value_to_metadata(form, formfield=form.waistvalue, unitfield=form.waistunit,
                                                    tab='Measurements', concept_id='C0455829')
    if waist is not None:
        donor.metadata[donor_data_key].append(waist)

    # KDPI
    kdpi = translate_field_value_to_metadata(form, formfield=form.kdpi, tab='Measurements', concept_id='C4330523')
    if kdpi is not None:
        donor.metadata[donor_data_key].append(kdpi)

    # Hba1c
    hba1c = translate_field_value_to_metadata(form, formfield=form.hba1c, tab='Measurements', concept_id='C2707530')
    if hba1c is not None:
        donor.metadata[donor_data_key].append(hba1c)

    # amylase
    amylase = translate_field_value_to_metadata(form, formfield=form.amylase, tab='Measurements',
                                                    concept_id='C0201883')
    if amylase is not None:
        donor.metadata[donor_data_key].append(amylase)

    # lipase
    lipase = translate_field_value_to_metadata(form, formfield=form.lipase, tab='Measurements',
                                                      concept_id='C0373670')
    if lipase is not None:
        donor.metadata[donor_data_key].append(lipase)

    # age at menarche
    agemenarche = translate_field_value_to_metadata(form, formfield=form.agemenarche, tab='Measurements',
                                                     concept_id='C1314691')
    if agemenarche is not None:
        donor.metadata[donor_data_key].append(agemenarche)

    # age at first birth
    agefirstbirth = translate_field_value_to_metadata(form, formfield=form.agefirstbirth, tab='Measurements',
                                                            concept_id='C1510831')
    if agefirstbirth is not None:
        donor.metadata[donor_data_key].append(agefirstbirth)

    # gestational age
    gestationalage = translate_field_value_to_metadata(form, formfield=form.gestationalage, tab='Measurements',
                                                            concept_id='C0017504')
    if gestationalage is not None:
        donor.metadata[donor_data_key].append(gestationalage)

    # cancer risk
    cancerrisk = translate_field_value_to_metadata(form, formfield=form.cancerrisk, tab='Measurements',
                                                             concept_id='C0596244')
    if cancerrisk is not None:
        donor.metadata[donor_data_key].append(cancerrisk)

    # Pathology note
    pathologynote = translate_field_value_to_metadata(form, formfield=form.pathologynote, tab='Measurements',
                                                         concept_id='C0807321')
    if pathologynote is not None:
        donor.metadata[donor_data_key].append(pathologynote)

    # Apolipoprotein E phenotype
    apoephenotype = translate_field_value_to_metadata(form, formfield=form.apoephenotype, tab='Measurements',
                                                            concept_id='C0428504')
    if apoephenotype is not None:
        donor.metadata[donor_data_key].append(apoephenotype)

    # Fitzpatrick Skin Type
    fitzpatrick = translate_selectfield_to_metadata(form, formfield=form.fitzpatrick, tab='Measurements')
    if fitzpatrick is not None:
        donor.metadata[donor_data_key].append(fitzpatrick)

    # Blood Type
    bloodtype = translate_selectfield_to_metadata(form, formfield=form.bloodtype, tab='Blood Type')
    if bloodtype is not None:
        donor.metadata[donor_data_key].append(bloodtype)

    # Blood Type
    bloodrh = translate_selectfield_to_metadata(form, formfield=form.bloodrh, tab='Blood Type')
    if bloodrh is not None:
        donor.metadata[donor_data_key].append(bloodrh)

    # Smoking status
    smoking = translate_selectfield_to_metadata(form, formfield=form.smoking, tab='Social History')
    if smoking is not None:
        donor.metadata[donor_data_key].append(smoking)

    # Tobacco use
    tobacco = translate_selectfield_to_metadata(form, formfield=form.tobacco, tab='Social History')
    if tobacco is not None:
        donor.metadata[donor_data_key].append(tobacco)

    # Alcohol use
    alcohol = translate_selectfield_to_metadata(form, formfield=form.alcohol, tab='Social History')
    if alcohol is not None:
        donor.metadata[donor_data_key].append(alcohol)

    # Drug use
    drug = translate_selectfield_to_metadata(form, formfield=form.drug, tab='Social History')
    if drug is not None:
        donor.metadata[donor_data_key].append(drug)

    # Medical History - up to 10 conditions.
    for field in form:
        if 'medhx' in field.name:
            medhx = translate_selectfield_to_metadata(form, formfield=field, tab='Medical History')
            if medhx is not None:
                donor.metadata[donor_data_key].append(medhx)


    return donor

@edit_blueprint.route('', methods=['GET', 'POST'])
def edit(donorid):

    form = EditForm(request.form)

    # Populate the edit form with current metadata for the donor.
    setdefaults(form, donorid=donorid)

    if request.method == 'POST' and form.validate():
        # Translate revised donor metadata fields into the encoded donor metadata schema.
        form.newdonordata = buildnewdonordata(form)
        return jsonify(form.newdonordata.metadata)

    return render_template('edit.html', form=form)
