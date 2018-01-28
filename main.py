import pprint
import praw
import logging
import re
import os
import google.cloud.vision
from pathlib import Path
from PIL import Image
import io

logger = logging.getLogger()
handler = logging.StreamHandler()
formatter = logging.Formatter(
                '%(levelname)-8s %(message)s')
handler.setFormatter(formatter)
file_handler = logging.FileHandler('myapp_log')
file_handler.setFormatter(formatter)
logger.addHandler(handler)
logger.addHandler(file_handler)
logger.setLevel(logging.WARNING)

def resize(file):
    print("Resizing")
    size = 1000,1000
    foo = Image.open(file)
    foo.thumbnail(size, Image.ANTIALIAS)
    foo.save(file, optimize=True,quality=95)
def process_images():
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
def split_into_sentences(text):
    caps = "([A-Z])"
    prefixes = "(Mr|St|Mrs|Ms|Dr)[.]"
    suffixes = "(Inc|Ltd|Jr|Sr|Co)"
    starters = "(Mr|Mrs|Ms|Dr|He\s|She\s|It\s|They\s|Their\s|Our\s|We\s|But\s|However\s|That\s|This\s|Wherever)"
    acronyms = "([A-Z][.][A-Z][.](?:[A-Z][.])?)"
    websites = "[.](com|net|org|io|gov)"
    text = " " + text + "  "
    text = text.replace("\n"," ")
    text = re.sub(prefixes,"\\1<prd>",text)
    text = re.sub(websites,"<prd>\\1",text)
    if "Ph.D" in text: text = text.replace("Ph.D.","Ph<prd>D<prd>")
    text = re.sub("\s" + caps + "[.] "," \\1<prd> ",text)
    text = re.sub(acronyms+" "+starters,"\\1<stop> \\2",text)
    text = re.sub(caps + "[.]" + caps + "[.]" + caps + "[.]","\\1<prd>\\2<prd>\\3<prd>",text)
    text = re.sub(caps + "[.]" + caps + "[.]","\\1<prd>\\2<prd>",text)
    text = re.sub(" "+suffixes+"[.] "+starters," \\1<stop> \\2",text)
    text = re.sub(" "+suffixes+"[.]"," \\1<prd>",text)
    text = re.sub(" " + caps + "[.]"," \\1<prd>",text)
    if "\"" in text: text = text.replace(".\"","\".")
    if "!" in text: text = text.replace("!\"","\"!")
    if "?" in text: text = text.replace("?\"","\"?")
    text = text.replace(".",".<stop>")
    text = text.replace("?","?<stop>")
    text = text.replace("!","!<stop>")
    text = text.replace("<prd>",".")
    sentences = text.split("<stop>")
    sentences = sentences[:-1]
    sentences = [s.strip() for s in sentences]
    return sentences

def process_submission(comment):
    if has_link_and_question(comment.body):
        if has_link_and_question_in_sentence(comment.body):
                #logger.debug("https://www.reddit.com" + comment.permalink)
                for reply in comment.refresh().replies.list():
                    logger.debug("All replies" + str(reply))
                    if has_hyperlink(reply.body):
                        logger.info("Saving this")
                        logger.info("https://www.reddit.com" + reply.permalink)
                        logger.info(reply.body)
def has_link_and_question(text):
    if "?" in text and "LINK" in text.upper():
        return True
    else:
        return False
def has_link_and_question_in_sentence(text):
    sentences = split_into_sentences(text)
    for sentence in sentences:
        if has_link_and_question(sentence):
            return True
        else:
            return False
#Find replies with links
def has_hyperlink(text):
    has_hyperlink = False
    reddit_hyperlink_regex = ".*\[.*\]\(.*\).*"
    if re.match(reddit_hyperlink_regex, text):
        has_hyperlink = True
        logger.info("This text has a link:" + text)
    return has_hyperlink
def process_comment(comment):
    logger.info("Processing comment")
    if has_hyperlink(comment.body) and has_link_and_question_in_sentence(comment.parent().body):
            logger.info("Saving this")
            logger.warning("https://www.reddit.com" + comment.permalink)
            logger.warning(comment.body)

def main():
    reddit = praw.Reddit('bamboozle_bot', user_agent='bamboozle_bot user agent')
    subreddit = reddit.subreddit('test')
    for comment in subreddit.stream.comments():
            logger.info(comment.body)
            if comment.is_root:
                logger.info('This is a parent comment')
                process_submission(comment)
            else:
                logger.info('This is not a parent comment')
                if has_hyperlink(comment.body):
                    while not comment.is_root:
                        process_comment(comment)
                        comment = comment.parent()
            #pprint.pprint(vars(comment))


if __name__ == '__main__':
    main()
