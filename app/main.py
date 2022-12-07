import cv2
from ai.ai_model import load_yolov5_model
from ai.ai_model import detection

def get_frame(filename):
    """ Read image from file using opencv.

        Args:
            filename(str): relative or absolute path of the image

        Returns:
            (numpy.ndarray) frame read from file 
    """
    return cv2.imread(filename)

def main():
    model, labels = load_yolov5_model() # loading model and labels
    frame =  get_frame('../test.jpg')

    detected, _ = detection(frame, model, labels)

    from PIL import Image
    im = Image.fromarray(detected)
    im.save("../your_file.jpeg")

if __name__ == '__main__':
    main()