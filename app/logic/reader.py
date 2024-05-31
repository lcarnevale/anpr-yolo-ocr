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
__description__ = 'Reader class'

import os
import cv2
import time
import torch
import logging
import threading
import numpy as np
from PIL import Image
import torch.backends.cudnn as cudnn
from models.experimental import attempt_load
from utils.general import non_max_suppression
from utils.params import Parameters

class Reader:

    def __init__(self, static_files_potential, static_files_detection, model_path, mutex, verbosity, logging_path) -> None:
        self.__static_files_potential = static_files_potential
        self.__static_files_detection = static_files_detection
        self.__mutex = mutex
        self.__reader = None
        self.__params = Parameters(model_path)
        self.__model, self.__labels = self.__load_yolov5_model()
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
        if not os.path.exists(self.__static_files_detection):
            os.makedirs(self.__static_files_detection)

        self.__reader = threading.Thread(
            target = self.__reader_job, 
            args = ()
        )

    def __reader_job(self):
        while True:
            # If the folder is not empty it acquire the mutex to safely access the dir
            if not self.__potential_folder_is_empty():
                self.__mutex.acquire()
                oldest_frame_path = self.__oldest()

                # Picking the oldest frame
                frame =  self.__get_frame(oldest_frame_path)

                # Storing the output and label
                detected, _ = self.__detection(frame, self.__model, self.__labels)
                os.remove(oldest_frame_path)

                # Releasing the mutex
                self.__mutex.release()

                # Saving the processed image
                image = Image.fromarray(detected)
                filename = os.path.basename(oldest_frame_path)
                absolute_path = '%s/%s' % (self.__static_files_detection, filename)
                image.save(absolute_path)
                time.sleep(0.1)       

    def __potential_folder_is_empty(self):
        path = self.__static_files_potential
        return True if not len(os.listdir(path)) else False

    def __oldest(self):
        path = self.__static_files_potential
        files = os.listdir(path)
        paths = [os.path.join(path, basename) for basename in files]
        return min(paths, key=os.path.getctime)

    def __load_yolov5_model(self):
        """
        It loads the model and returns the model and the names of the classes.
        :return: model, names
        """
        model = attempt_load(self.__params.model, map_location=self.__params.device)
        print("device",self.__params.device)
        stride = int(model.stride.max())  # model stride
        names = model.module.names if hasattr(model, 'module') else model.names  # get class names

        return model, names

    def __get_frame(self, filename):
        """ Read image from file using opencv.

            Args:
                filename(str): relative or absolute path of the image

            Returns:
                (numpy.ndarray) frame read from file 
        """
        return cv2.imread(filename)

    def __detection(self, frame, model, names):
        """
        It takes an image, runs it through the model, and returns the image with bounding boxes drawn around
        the detected objects
        
        :param frame: The frame of video or webcam feed on which we're running inference
        :param model: The model to use for detection
        :param names: a list of class names
        :return: the image with the bounding boxes and the label of the detected object.
        """
        out = frame.copy()

        frame = cv2.resize(frame, (self.__params.pred_shape[1], self.__params.pred_shape[0]), interpolation=cv2.INTER_LINEAR)
        frame = np.transpose(frame, (2, 1, 0))


        cudnn.benchmark = True  # set True to speed up constant image size inference

        if self.__params.device.type != 'cpu':
            model(torch.zeros(1, 3, self.__params.imgsz, self.__params.imgsz).to(self.__params.device).type_as(next(model.parameters())))  # run once

        frame = torch.from_numpy(frame).to(self.__params.device)
        frame = frame.float()
        frame /= 255.0
        if frame.ndimension() == 3:
            frame = frame.unsqueeze(0)

        frame = torch.transpose(frame, 2, 3)


        pred = model(frame, augment=False)[0]
        pred = non_max_suppression(pred, self.__params.conf_thres, max_det=self.__params.max_det)

        label=""
        # detections per image
        for i, det in enumerate(pred):

            img_shape = frame.shape[2:]
            out_shape = out.shape

            s_ = f'{i}: '
            s_ += '%gx%g ' % img_shape  # print string

            if len(det):

                gain = min(img_shape[0] / out_shape[0], img_shape[1] / out_shape[1])  # gain  = old / new

                coords = det[:, :4]


                pad = (img_shape[1] - out_shape[1] * gain) / 2, (
                        img_shape[0] - out_shape[0] * gain) / 2  # wh padding

                coords[:, [0, 2]] -= pad[0]  # x padding
                coords[:, [1, 3]] -= pad[1]  # y padding
                coords[:, :4] /= gain

                coords[:, 0].clamp_(0, out_shape[1])  # x1
                coords[:, 1].clamp_(0, out_shape[0])  # y1
                coords[:, 2].clamp_(0, out_shape[1])  # x2
                coords[:, 3].clamp_(0, out_shape[0])  # y2

                det[:, :4] = coords.round()

                for c in det[:, -1].unique():
                    n = (det[:, -1] == c).sum()  # detections per class
                    s_ += f"{n} {names[int(c)]}{'s' * (n > 1)}, "  # add to string

                for *xyxy, conf, cls in reversed(det):

                    x1 = int(xyxy[0].item())
                    y1 = int(xyxy[1].item())
                    x2 = int(xyxy[2].item())
                    y2 = int(xyxy[3].item())

                    confidence_score = conf
                    class_index = cls
                    object_name = names[int(cls)]
                    
                    detected_plate = frame[:,:,y1:y2, x1:x2].squeeze().permute(1, 2, 0).cpu().numpy()
                    # cv2.imshow("Crooped Plate ",detected_plate)

                    #rect_size= (detected_plate.shape[0]*detected_plate.shape[1])
                    c = int(cls)  # integer class
                    label = names[c] if self.__params.hide_conf else f'{names[c]} {conf:.2f}'

                    tl = self.__params.rect_thickness

                    c1, c2 = (int(xyxy[0]), int(xyxy[1])), (int(xyxy[2]), int(xyxy[3]))
                    cv2.rectangle(out, c1, c2, self.__params.color, thickness=tl, lineType=cv2.LINE_AA)

                    if label:
                        tf = max(tl - 1, 1)  # font thickness
                        t_size = cv2.getTextSize(label, 0, fontScale=tl / 3, thickness=tf)[0]
                        c2 = c1[0] + t_size[0], c1[1] - t_size[1] - 3
                        cv2.rectangle(out, c1, c2, self.__params.color, -1, cv2.LINE_AA)  # filled
                        cv2.putText(out, label, (c1[0], c1[1] - 2), 0, tl / 3, [225, 255, 255], thickness=tf,
                                    lineType=cv2.LINE_AA)

        return out, label

    def start(self):
        self.__reader.start()
