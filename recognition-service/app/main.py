# -*- coding: utf-8 -*-
#!/usr/bin/env python

"""License Plate Detection
This implementation does its best to follow the Robert Martin's Clean code guidelines.
The comments follow the Google Python Style Guide:
    https://github.com/google/styleguide/blob/gh-pages/pyguide.md
"""

__copyright__ = 'Copyright 2023, FCRlab at University of Messina'
__author__ = 'Lorenzo Carnevale <lcarnevale@unime.it>'
__credits__ = ''
__description__ = 'License Plate Detection'

import os
import yaml
import argparse
import logging
from threading import Lock
from logic.recognition import Recognition

def main():
    """
    Main function to parse arguments, set up logging, and start the recognition.
    """
    description = f'{__author__}\n{__description__}'
    epilog = f'{__credits__}\n{__copyright__}'
    
    parser = argparse.ArgumentParser(description=description, epilog=epilog)
    parser.add_argument('-c', '--config', dest='config', help='YAML configuration file', type=str, required=True)
    parser.add_argument('-v', '--verbosity', dest='verbosity', help='Logging verbosity level', action="store_true")
    
    options = parser.parse_args()
    verbosity = options.verbosity
    mutex = Lock()
    
    with open(options.config) as f:
        config = yaml.load(f, Loader=yaml.FullLoader)
    
    logdir_name = config['logging']['logging_folder']
    logging_path = os.path.join(logdir_name, config['logging']['logging_filename'])
    
    if not os.path.exists(logdir_name):
        os.makedirs(logdir_name, exist_ok=True)

    recognition = setup_recognition(config['restful'], config['static_files'], mutex, verbosity, logging_path)
    recognition.start()

def setup_recognition(restful_config, static_files_config, mutex, verbosity, logging_path):
    """
    Set up the Flask recognition.

    Args:
        restful_config (dict): Configuration for the RESTful API.
        static_files_config (dict): Configuration for static files.
        mutex (Lock): A mutex for thread-safe operations.
        verbosity (bool): The verbosity level for logging.
        logging_path (str): The path to the log file.

    Returns:
        Recognition: The initialized Flask recognition.
    """
    recognition = Recognition(
        host=restful_config['host'],
        port=restful_config['port'],
        static_files=static_files_config['potential'],
        mutex=mutex,
        verbosity=verbosity,
        logging_path=logging_path
    )
    recognition.setup()
    return recognition

if __name__ == '__main__':
    main()
