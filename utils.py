
def set_test_argument():
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('-t', action='store_true', help='run in test mode')
    args = parser.parse_args()


def json2dict(json_str):
    import json

    return json.loads(json_str)[0]

