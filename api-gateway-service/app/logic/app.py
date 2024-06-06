# -*- coding: utf-8 -*-
#!/usr/bin/env python

__copyright__ = 'Copyright 2023, FCRlab at University of Messina'
__author__ = 'Lorenzo Carnevale <lcarnevale@unime.it>'
__credits__ = ''
__description__ = 'App class'

import os
import logging
from threading import Lock
import requests
from flask import Flask, request, make_response, render_template, redirect, jsonify
from flask_api import status
from werkzeug.utils import secure_filename

class App:
    """A class used to represent the Flask application."""

    __ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

    def __init__(self, host, port, static_files, mutex, verbosity, logging_path) -> None:
        """
        Initialize the App class with the specified parameters.

        Args:
            host (str): The host on which the Flask app will run.
            port (int): The port on which the Flask app will run.
            static_files (str): The path to the static files.
            mutex (threading.Lock): A mutex for thread-safe operations.
            verbosity (bool): The verbosity level for logging.
            logging_path (str): The path to the log file.
        """
        self.__host = host
        self.__port = port
        self.__static_files = static_files
        self.__mutex = mutex
        self.__verbosity = verbosity
        self.__setup_logging(verbosity, logging_path)
        self.__app = Flask(__name__)

    def __setup_logging(self, verbosity, path):
        """
        Setup logging for the application.

        Args:
            verbosity (bool): The verbosity level for logging.
            path (str): The path to the log file.
        """
        format = "%(asctime)s %(filename)s:%(lineno)d %(levelname)s - %(message)s"
        datefmt = "%d/%m/%Y %H:%M:%S"
        level = logging.DEBUG if verbosity else logging.INFO
        logging.basicConfig(filename=path, filemode='a', format=format, level=level, datefmt=datefmt)

    def __allowed_file(self, filename):
        """
        Check if the file is allowed based on its extension.

        Args:
            filename (str): The name of the file.

        Returns:
            bool: True if the file is allowed, False otherwise.
        """
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in self.__ALLOWED_EXTENSIONS

    def __call_recognition_service(self):
        url = "http://recognition-service:5001/api/v1/frame-download"
        logging.info("Calling recognition service at %s", url)
        try:
            response = requests.post(url)
            response.raise_for_status()  # This will raise an HTTPError for bad responses
        except requests.exceptions.RequestException as e:
            logging.error("Error calling recognition service: %s", e)
            return None
        return response.json()
    
    def setup(self):
        """Set up the Flask app with routes and configurations."""
        @self.__app.route('/', methods=['GET'])
        def home():
            return render_template('web/index.html')

        @self.__app.route('/api/v1/frame-upload', methods=['POST'])
        def upload_file():
            logging.info("Uploading frame...")

            if 'frame-upload' not in request.files:
                return make_response("No file part", status.HTTP_400_BAD_REQUEST)
            
            file = request.files['frame-upload']
            
            if file.filename == '':
                return make_response("No selected file", status.HTTP_400_BAD_REQUEST)
            
            if file and self.__allowed_file(file.filename):
                filename = secure_filename(file.filename)
                
                self.__mutex.acquire()
                try:
                    file.save(os.path.join(self.__static_files, filename))
                finally:
                    self.__mutex.release()

                result = self.__call_recognition_service()
                
                if result is None:
                    return make_response("Error calling recognition service", status.HTTP_500_INTERNAL_SERVER_ERROR)

                return make_response(jsonify(result), status.HTTP_201_CREATED)
            else:
                return make_response("File type not allowed", status.HTTP_400_BAD_REQUEST)

    def start(self):
        """Start the Flask app."""
        self.__app.run(host=self.__host, port=self.__port, debug=self.__verbosity, threaded=True, use_reloader=True)
