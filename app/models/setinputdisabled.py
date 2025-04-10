# Function to disable a WTForms field.

from wtforms import Field
def setinputdisabled(inputfield:Field, disabled: bool = True):
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
