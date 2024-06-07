# -*- coding: utf-8 -*-
#!/usr/bin/env python

__copyright__ = 'Copyright 2023, FCRlab at University of Messina'
__author__ = 'Lorenzo Carnevale <lcarnevale@unime.it>'
__credits__ = ''
__description__ = 'Recognition class'

import logging
import threading
import os
import uuid
import cv2
import torch

from flask import Flask, request, make_response, jsonify
from flask_api import status
from werkzeug.utils import secure_filename

from PIL import Image
from ai.ai_model import detection as detection, load_yolov5_model
from ai.ocr_model import pytesseract_model_works, easyocr_model_works, easyocr_model_load
from helper.general_utils import save_results

# Load YOLOv5 model
model_yolo, labels = load_yolov5_model()

# Configure YOLOv5 model
model = torch.hub.load(
    "ultralytics/yolov5", "custom", path="model/best.pt", force_reload=True
)
model.eval()
model.conf = 0.5
model.iou = 0.45
#Easy OCR text reader 
ocr_text_reader = easyocr_model_load()

class RecognitionService:

    __ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

    def __init__(self, host, port, static_files_path, detected_frames_path, cropped_frames_path, results_path, results_filename, mutex, verbosity, logging_path):
        self.app = Flask(__name__)
        self.host = host
        self.port = port
        self.verbosity = verbosity
        self.logging_path = logging_path
        self.setup_logging(verbosity, logging_path)
        self.results_path = results_path
        self.results_filename = results_filename
        self.static_files_path = static_files_path
        self.detected_frames_path = detected_frames_path
        self.cropped_frames_path = cropped_frames_path
        self.mutex = mutex

    def setup_logging(self, verbosity, log_file_path):
        log_format = "%(asctime)s %(filename)s:%(lineno)d %(levelname)s - %(message)s"
        date_format = "%d/%m/%Y %H:%M:%S"
        log_level = logging.DEBUG if verbosity else logging.INFO
        logging.basicConfig(filename=log_file_path, filemode='a', format=log_format, level=log_level, datefmt=date_format)

    def is_allowed_file(self, filename):
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in self.__ALLOWED_EXTENSIONS

    def read_image(self, filename):
        return cv2.imread(filename)

    def perform_ocr(self, cropped_frame_path, ocr_event, ocr_result):
        logging.info("OCR recognition started!")
        logging.info(f"Received cropped frame {cropped_frame_path}")

        frames = [cropped_frame_path]
        predictions = pytesseract_model_works(frames, False)

        test = easyocr_model_works(ocr_text_reader, frames, False)

        logging.info(f"Detected plate number {predictions} and {test}")

        ocr_result['result'] = predictions[0].strip() if predictions else None
        ocr_event.set()

    def perform_detection(self, potential_frame_path, detection_event, detection_result, ocr_event, ocr_result, unique_id):
        logging.info("Detection started!")

        frame = self.read_image(potential_frame_path)

        if frame is not None:
            logging.info("Detecting image...!")
            detected_plate, detected_plate_cropped = detection(frame, model_yolo, labels)

            if detected_plate_cropped is not None:
                detected_filename = f"{unique_id}_detected.jpg"
                detected_frame_path = os.path.join(self.detected_frames_path, detected_filename)
                detected_plate_image = Image.fromarray(detected_plate)
                detected_plate_image.save(detected_frame_path, format="JPEG")

                cropped_filename = f"{unique_id}_cropped.jpg"
                cropped_frame_path = os.path.join(self.cropped_frames_path, cropped_filename)
                detected_plate_cropped_image = Image.fromarray(detected_plate_cropped)
                detected_plate_cropped_image.save(cropped_frame_path, format="JPEG")

                ocr_thread = threading.Thread(target=self.perform_ocr, args=(cropped_frame_path, ocr_event, ocr_result))
                ocr_thread.start()
                logging.info("Waiting for OCR thread to complete...")

                ocr_event.wait()
                detection_result['result'] = detected_frame_path
            else:
                logging.error("No plate detected, detection failed!")
                detection_result['result'] = None
        else:
            logging.error("Frame is None, detection failed!")
            detection_result['result'] = None

        detection_event.set()


    def save_potential_frame(self, potential_frame, detection_event, detection_result, ocr_event, ocr_result):
        logging.info("Saving potential frame...")

        if potential_frame and self.is_allowed_file(potential_frame.filename):
            unique_id = uuid.uuid4().hex
            file_extension = secure_filename(potential_frame.filename).rsplit('.', 1)[1].lower()
            potential_filename = f"{unique_id}_potential.{file_extension}"
            potential_frame_path = os.path.join(self.static_files_path, potential_filename)

            self.mutex.acquire()
            try:
                logging.info(f"Saving potential frame at: {potential_frame_path}")
                potential_frame.save(potential_frame_path)
            finally:
                self.mutex.release()

            detection_thread = threading.Thread(target=self.perform_detection, args=(potential_frame_path, detection_event, detection_result, ocr_event, ocr_result, unique_id))
            detection_thread.start()
            logging.info("Detection thread started...")
        else:
            logging.error("Invalid file received!")
            detection_result['result'] = None
            detection_event.set()

        detection_event.wait()
        logging.info("Detection completed!")

    def setup_routes(self):
        os.makedirs(self.static_files_path, exist_ok=True)
        os.makedirs(self.detected_frames_path, exist_ok=True)
        os.makedirs(self.cropped_frames_path, exist_ok=True)

        @self.app.route('/api/v1/frame-download', methods=['POST'])
        def receive_frame():
            if request.method != 'POST' or 'potential-frame' not in request.files:
                return make_response("Not a POST request or 'potential-frame' missing!\n", status.HTTP_400_BAD_REQUEST)

            logging.info("POST request received, starting detection...")

            potential_frame = request.files['potential-frame']

            detection_event = threading.Event()
            ocr_event = threading.Event()
            detection_result = {}
            ocr_result = {}

            download_thread = threading.Thread(target=self.save_potential_frame, args=(potential_frame, detection_event, detection_result, ocr_event, ocr_result))
            download_thread.start()
            download_thread.join()

            plate_num = ocr_result.get('result')

            logging.info("Building results...")
            results = {
                #"detected_plate": detection_result.get('result'),
                "plate_number": plate_num
            }

            logging.info("Returning results!")

            logging.info("Writing result into CSV...")
            save_results(plate_num, self.results_filename, self.results_path)

            return make_response(jsonify(results), status.HTTP_201_CREATED)

    def start(self):
        self.app.run(host=self.host, port=self.port, debug=self.verbosity, threaded=True, use_reloader=True)
