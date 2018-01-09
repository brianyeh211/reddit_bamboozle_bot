              
import io
import os

import google.cloud.vision
from pathlib import Path
from PIL import Image
def resize(file):
    print("Resizing")
    size = 1000,1000
    foo = Image.open(file)
    foo.thumbnail(size, Image.ANTIALIAS)
    foo.save(file, optimize=True,quality=95)

# Create a Vision client.
vision_client = google.cloud.vision.ImageAnnotatorClient()

# TODO (Developer): Replace this with the name of the local image
# file to analyze.
image_file_name = './link.jpg'
directory = "/home/brianyeh211/links" 
pathlist = Path(directory).glob('*')

for image in pathlist:
    is_link = False
    is_fictional_char = False
    print(image)
    image = str(image)
    with open(image, "rb") as image_file:
            size = os.path.getsize(image)
            if (size > 5000000):
                print("size too big")
                resize(image)
            content = image_file.read()
            request = {
                         'image': {
                                  'content': content,
                                      },
                                       }
            response = vision_client.annotate_image(request)
            web = response.web_detection
            #print(web)
            labels = response.label_annotations
            for label in labels:
                if (label.description == "fictional character" or label.description == "action figure"):
                    is_fictional_char = True
            for entity in web.web_entities:
                if (entity.description == "Link"):
                    is_link = True
            #print(web.web_entities)
            #if (web.web_entities.description == "Link"
            if (is_fictional_char is not True and is_link is not True):
                print(labels)
            print("########################")
"""
            # Use Vision to label the image based on content.
            image = google.cloud.vision.types.Image(content=content)
            response = vision_client.label_detection(image=image)

            print('Labels:')
            for label in response.label_annotations:
                    print(label.description)
            print(response)
   """                              
                                         
