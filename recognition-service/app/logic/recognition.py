# -*- coding: utf-8 -*-
#!/usr/bin/env python

__copyright__ = 'Copyright 2023, FCRlab at University of Messina'
__author__ = 'Lorenzo Carnevale <lcarnevale@unime.it>'
__credits__ = ''
__description__ = 'Recognition class'

import os
import logging
import threading
import time
from flask import Flask, request, make_response, jsonify
from flask_api import status

class Recognition:
    """A class used to represent the Flask recognitionlication."""

    def __init__(self, host, port, static_files, mutex, verbosity, logging_path) -> None:
        """
        Initialize the Recognition class with the specified parameters.

        Args:
            host (str): The host on which the Flask recognition will run.
            port (int): The port on which the Flask recognition will run.
            static_files (str): The path to the static files.
            mutex (threading.Lock): A mutex for thread-safe operations.
            verbosity (bool): The verbosity level for logging.
            logging_path (str): The path to the log file.
        """
        self.__recognition = Flask(__name__)
        self.__host = host
        self.__port = port
        self.__verbosity = verbosity
        self.__setup_logging(verbosity, logging_path)

        self.__static_files = static_files
        self.__csv_path = os.path.join(static_files, 'results.csv')
        self.__mutex = mutex

    def __setup_logging(self, verbosity, path):
        """
        Setup logging for the recognitionlication.

        Args:
            verbosity (bool): The verbosity level for logging.
            path (str): The path to the log file.
        """
        format = "%(asctime)s %(filename)s:%(lineno)d %(levelname)s - %(message)s"
        datefmt = "%d/%m/%Y %H:%M:%S"
        level = logging.DEBUG if verbosity else logging.INFO
        logging.basicConfig(filename=path, filemode='a', format=format, level=level, datefmt=datefmt)

    def __write_to_csv(self, csv_path, data):
        logging.info(f"Received CSV results at {csv_path}...")

        time.sleep(2)

        logging.info("Finished writing into CSV!")

    def __recognition_thread(self, detected_frame, recognition_event, recognition_result):
        logging.info("Recognition started!")
        
        # Simulate OCR recognition
        time.sleep(3)
        recognition_result['result'] = 'XYZ1234'
        recognition_event.set()

    def __detection_thread(self, potential_frame, detection_event, detection_result, recognition_event, recognition_result):
        logging.info("Detection started!")
        
        time.sleep(5)
        detected_frame = 'detected_plate.jpg'

        recognition_thread = threading.Thread(target=self.__recognition_thread, args=(detected_frame, recognition_event, recognition_result))
        recognition_thread.start()
        logging.info("Waiting for recognition thread to end...")

        recognition_event.wait()
        detection_result['result'] = detected_frame
        detection_event.set()

    def __download_thread(self, potential_frame, detection_event, detection_result, recognition_event, recognition_result):
        logging.info("Downloading frame...")

        time.sleep(3)

        detection_thread = threading.Thread(target=self.__detection_thread, args=(potential_frame, detection_event, detection_result, recognition_event, recognition_result))
        detection_thread.start()
        logging.info("Plate detection thread started...")

        detection_event.wait()
        logging.info("Detection finished!")

    def setup(self):
        @self.__recognition.route('/api/v1/frame-download', methods=['POST'])
        def frame_download():
            logging.info("POST request received, started detection...")

            detection_event = threading.Event()
            recognition_event = threading.Event()
            detection_result = {}
            recognition_result = {}

            # frame_download -> download_thread -> detection_thread -> recognition_thread 
            time.sleep(3)
            potential_frame = 'potential_frame.jpeg'

            download_thread = threading.Thread(target=self.__download_thread, args=(potential_frame, detection_event, detection_result, recognition_event, recognition_result))
            download_thread.start()
            download_thread.join()  # waiting

            logging.info("Building results...")
            results = {
                "original_plate": potential_frame,
                "detected_plate": detection_result.get('result'),
                "plate_number": recognition_result.get('result'),
                "confidence": "1.0"
            }

            logging.info("Writing results into CSV file...")
            self.__write_to_csv(self.__csv_path, results)

            logging.info("Returning results!")
            return make_response(jsonify(results), status.HTTP_201_CREATED)

    def start(self):
        """Start the Flask recognition."""
        self.__recognition.run(host=self.__host, port=self.__port, debug=self.__verbosity, threaded=True, use_reloader=True)

if __name__ == '__main__':
    host = '0.0.0.0'
    port = 5001
    static_files = './static'
    mutex = threading.Lock()
    verbosity = True
    logging_path = './recognition.log'
    recognition = Recognition(host, port, static_files, mutex, verbosity, logging_path)
    recognition.setup()
    recognition.start()
