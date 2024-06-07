import cv2
import numpy as np
import pytesseract
import matplotlib.pyplot as plt
import easyocr

def easyocr_model_load():
    """
    It takes in an image and returns the text in the image
    :return: The text_reader is being returned.
    """

    text_reader = easyocr.Reader(["en"])  # Initialzing the ocr
    return text_reader


def easyocr_model_works(text_reader, images, visualization=False):
    """
    It takes a list of images and returns a list of texts
    
    :param text_reader: The text reader object
    :param images: list of images
    :param visualization: If True, it will show the images with the bounding boxes and the text,
    defaults to False (optional)
    """

    texts = list()
    for i in range(len(images)):
        results = text_reader.recognize(
            images[i]
        )  # reader.recognize sadece recognize, text detection yok
        for (bbox, text, prob) in results:
            texts.append(text)
        if visualization:
            plt.imshow(images[i])
            plt.title("{} Image".format(str(i)))
            plt.show()
    return texts

def preprocess_image(image):
    """
    Preprocess the image for better OCR results.
    
    :param image: The input image
    :return: The preprocessed image
    """
    if not isinstance(image, np.ndarray):
        raise ValueError("Input image is not a valid numpy array")
    
    # Convert to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # Apply Gaussian blur
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    
    # Apply thresholding
    _, thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    return thresh

def pytesseract_model_works(images, visualization=False):
    """
    It takes in a list of images and returns a list of predictions.
    
    :param images: list of images
    :param visualization: If True, it will show the image and the predicted text, defaults to False
    (optional)
    """
    tesseract_preds = []
    
    for img in images:
        # Check if the image is a valid numpy array
        if isinstance(img, str):
            # If the image is a path, read the image
            img = cv2.imread(img)
            if img is None:
                raise ValueError(f"Could not read image from path: {img}")
        
        # Preprocess the image
        preprocessed_img = preprocess_image(img)
        # Perform OCR with custom configurations
        custom_config = r'--oem 3 --psm 6'
        tesseract_preds.append(pytesseract.image_to_string(preprocessed_img, config=custom_config))
        
        if visualization:
            plt.imshow(preprocessed_img, cmap='gray')
            plt.title(f"Preprocessed Image {images.index(img)}")
            plt.show()
    
    return tesseract_preds
