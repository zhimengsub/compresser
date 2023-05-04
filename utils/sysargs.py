import argparse


def get_sysargs():
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--work-path', help='full path of the folder to be compressed')
    parser.add_argument('-c', '--conf-path', default='conf.ini', help='path to config file')
    args = parser.parse_args()

    return args
