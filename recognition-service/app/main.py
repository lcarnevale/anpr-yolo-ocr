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
from logic.recognition import RecognitionService

def main():
    """
    Main function to parse arguments, set up logging, and start the recognition service.
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
    os.makedirs(logdir_name, exist_ok=True)

    static_files_path = os.path.join(os.getcwd(), 'static-files')
    os.system(f"rm -rf {static_files_path}")

    recognition_service = setup_recognition_service(config['restful'], config['static_files'], config['results'], mutex, verbosity, logging_path)
    recognition_service.start()

def setup_recognition_service(restful_config, static_files_config, results_config, mutex, verbosity, logging_path):
    """
    Set up the Flask recognition service.

    Args:
        restful_config (dict): Configuration for the RESTful API.
        static_files_config (dict): Configuration for static files.
        mutex (Lock): A mutex for thread-safe operations.
        verbosity (bool): The verbosity level for logging.
        logging_path (str): The path to the log file.

    Returns:
        RecognitionService: The initialized Flask recognition service.
    """
    recognition_service = RecognitionService(
        host = restful_config['host'],
        port = restful_config['port'],
        static_files_path = static_files_config['potential'],
        detected_frames_path = static_files_config['detected'],
        cropped_frames_path = static_files_config['cropped'],
        results_path = results_config['results_folder'],
        results_filename = results_config['results_filename'],
        mutex = mutex,
        verbosity = verbosity,
        logging_path = logging_path
    )
    recognition_service.setup_routes()
    return recognition_service

if __name__ == '__main__':
    main()
