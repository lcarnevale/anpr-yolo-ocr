# -*- coding: utf-8 -*-
#!/usr/bin/env python

"""
This implementation does its best to follow the Robert Martin's Clean code guidelines.
The comments follows the Google Python Style Guide:
    https://github.com/google/styleguide/blob/gh-pages/pyguide.md
"""

__copyright__ = 'Copyright 2023, FCRlab at University of Messina'
__author__ = 'Lorenzo Carnevale <lcarnevale@unime.it>'
__credits__ = ''
__description__ = 'Writer class'

import os
import logging
import threading
from flask_api import status
from flask import Flask, request, make_response
from werkzeug.utils import secure_filename

class Writer:
    """
    """
    __ALLOWED_EXTENSIONS = {
        'png',
        'jpg',
        'jpeg'
    }

    def __init__(self, host, port, static_files, mutex, verbosity, logging_path) -> None:
        self.__host = host
        self.__port = port
        self.__static_files = static_files
        self.__mutex = mutex
        self.__writer = None
        self.__verbosity = verbosity
        self.__setup_logging(verbosity, logging_path)

    def __setup_logging(self, verbosity, path):
        format = "%(asctime)s %(filename)s:%(lineno)d %(levelname)s - %(message)s"
        filename=path
        datefmt = "%d/%m/%Y %H:%M:%S"
        level = logging.INFO
        if (verbosity):
            level = logging.DEBUG
        logging.basicConfig(filename=filename, filemode='a', format=format, level=level, datefmt=datefmt)


    def setup(self):
        if not os.path.exists(self.__static_files):
            os.makedirs(self.__static_files)

        self.__writer = threading.Thread(
            target = self.__writer_job, 
            args = (self.__host, self.__port, self.__verbosity)
        )

    def __writer_job(self, host, port, verbosity):
        app = Flask(__name__)

        app.add_url_rule('/api/v1/frame-upload', 'frame-upload', self.__frame_upload, methods=['POST'])
        print(host, port)
        app.run(host=host, port=port, debug=verbosity, threaded=True, use_reloader=False)


    def __frame_upload(self):
        if request.method == 'POST':
            if 'upload' not in request.files:
                response = make_response("File not found", status.HTTP_400_BAD_REQUEST)
            file = request.files['upload']
            if file and self.__allowed_file(file.filename):
                filename = secure_filename(file.filename)
                absolute_path = '%s/%s' % (self.__static_files, filename)
                self.__mutex.acquire()
                file.save(absolute_path)
                self.__mutex.release()
                response = make_response("File is stored", status.HTTP_201_CREATED)
            return response

    def __allowed_file(self, filename):
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in self.__ALLOWED_EXTENSIONS


    def start(self):
        self.__writer.start()