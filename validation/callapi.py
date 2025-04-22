"""
Routines for working with the REST APIs used by the validation scripts
"""

import argparse

class RawTextArgumentDefaultsHelpFormatter(
    argparse.ArgumentDefaultsHelpFormatter,
    argparse.RawTextHelpFormatter
):
    pass


def getconsortiumfromargs() -> str:

    # Obtains the base for urls to the search-api from the -c argument.

    # Get consortium.
    parser = argparse.ArgumentParser(
        description='Compare DOI titles with donor metadata terms',
        formatter_class=RawTextArgumentDefaultsHelpFormatter)
    parser.add_argument("-c", "--consortium", type=str,
                        help='consortium', required=True)

    args = parser.parse_args()
    if args.consortium == 'h':
        return 'CONTEXT_HUBMAP'
    elif args.consortium == 's':
        return 'CONTEXT_SENNET'
    else:
        print(f'Unknown consortium {args.consortium}')
        exit(-1)


def readglobustoken() -> str:
    """
    Reads a temporary Globus token from a text file.
    """

    with open('globus.token', 'r') as file:
        content = file.read()

    return content
