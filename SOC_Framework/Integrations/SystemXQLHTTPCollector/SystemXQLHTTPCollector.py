import demistomock as demisto  # noqa: F401
from CommonServerPython import *  # noqa: F401

import json


def test_module_command() -> str:
    """
    A placeholder function to implement testing - doesn't actually do anything (yet).

    Returns:
        (str) 'ok' if success.
    """
    return 'ok'

def main() -> None:
    """
    main function, parses params and runs command functions
    """

    params = demisto.params()
    args = demisto.args()
    command = demisto.command()

    demisto.debug(f'Command being called is {command}')

    try:
        if command == 'test-module':
            return_results(test_module_command())

        elif command == 'xql-post-to-dataset':
            VENDOR = args.get('vendor') if args.get('vendor') else params.get('vendor')
            PRODUCT = args.get('product)') if args.get('product') else params.get('product')

            events = json.loads(args.get('JSON'))
            events = json.loads(args.get('JSON'))
            events = events if type(events) == list else [events]

            send_events_to_xsiam(
                events,
                vendor=VENDOR,
                product=PRODUCT
            )

    except Exception as e:
        return_error(f'Failed to execute {command} command.\nError:\n{e}')


''' ENTRY POINT '''

if __name__ in ('__main__', '__builtin__', 'builtins'):
    main()

