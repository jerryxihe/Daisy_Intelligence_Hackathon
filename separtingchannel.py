try:
    from PIL import Image
except ImportError:
    import Image
import pytesseract
from shutil import copyfile, copy, move

# If you don't have tesseract executable in your PATH, include the following:
# pytesseract.pytesseract.tesseract_cmd = r'<full_path_to_your_tesseract_executable>'
# Example tesseract_cmd = r'C:\Program Files (x86)\Tesseract-OCR\tesseract'

# Simple image to string
#print(pytesseract.image_to_string(Image.open('week_1_page_2.jpg')))

# Get bounding box estimates
#print(pytesseract.image_to_boxes(Image.open('week_1_page_2.jpg')))



# Before running the script, use ImageMagick to do the color channel separation: (follow are the code for running ImageMagick)
#For black: mogrify -fill white -fuzz 15% +opaque ‘#000000’ *
#For Grey: mogrify -fill black -fuzz 10% +opaque '#454545'
#For Red: mogrify -fill black -fuzz 25% +opaque '#ff0000' *

import cv2
import pytesseract
import os
curdir = os.getcwd()

def merge_folder():
    outdirpath = os.path.join(curdir, '3_color_dir')
    if not os.path.exists(outdirpath):
        os.mkdir(outdirpath)

    blackdir = os.path.join(curdir, 'flyer_images_black')
    greydir = os.path.join(curdir, 'flyer_images_grey')
    reddir = os.path.join(curdir, 'flyer_images_red')

    for item in os.listdir(blackdir):
        print(item)
        filename, file_extension = os.path.splitext(item)
        root = os.path.join(outdirpath, str(filename)[0:-7])

        if not os.path.exists(root):
            os.mkdir(root)

        nextroot = os.path.join(root, str(filename)+'_black'+file_extension)
        move(os.path.join(blackdir, item), nextroot)

    for item in os.listdir(greydir):
        print(item)
        filename, file_extension = os.path.splitext(item)
        root = os.path.join(outdirpath, str(filename)[0:-7])

        if not os.path.exists(root):
            os.mkdir(root)

        nextroot = os.path.join(root, str(filename)+'_grey'+file_extension)
        move(os.path.join(greydir, item), nextroot)

    for item in os.listdir(reddir):
        print(item)
        filename, file_extension = os.path.splitext(item)
        root = os.path.join(outdirpath, str(filename)[0:-7])

        if not os.path.exists(root):
            os.mkdir(root)

        nextroot = os.path.join(root, str(filename) + '_red' + file_extension)
        move(os.path.join(reddir, item), nextroot)

#merge_folder()