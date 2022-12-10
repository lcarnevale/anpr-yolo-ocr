# Automatic Number Plate Recognition - Microservices

**Automatic Number Plate Recognition** (ANPR) is the process of reading the characters on the plate with various **optical character recognition** (OCR) methods by separating the plate region on the vehicle image obtained from automatic plate recognition.

This repository forks the [Automatic_Number_Plate_Recognition_YOLO_OCR
](https://github.com/mftnakrsu/Automatic_Number_Plate_Recognition_YOLO_OCR) one by [mftnakrsu](https://github.com/mftnakrsu) to create two microservices deployable as Docker containers.

## How to build
Build the image using the Docker command.

```
docker build -t lcarnevale/platedetection .
```

## How to run
Run the image as following.

```
docker run -d --name platedetection \
    -v /var/log/platedetection:/opt/app/log \
    -v ~/static-files:/opt/app/static-files \
    lcarnevale/platedetection
```

## Credits
University of Messina, Messina, Italy