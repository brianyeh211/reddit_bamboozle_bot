import praw
import logging
import re
import os
import google.cloud.vision
from pathlib import Path
from PIL import Image
import io

logger = logging.getLogger('myapp')
hdlr = logging.FileHandler('./myapp_log')
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
hdlr.setFormatter(formatter)
logger.addHandler(hdlr)
logger.setLevel(logging.WARNING)
# logger = logging.getLogger('prawcore')
# logger.setLevel(logging.DEBUG)
# logger.addHandler(handler)



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

caps = "([A-Z])"
prefixes = "(Mr|St|Mrs|Ms|Dr)[.]"
suffixes = "(Inc|Ltd|Jr|Sr|Co)"
starters = "(Mr|Mrs|Ms|Dr|He\s|She\s|It\s|They\s|Their\s|Our\s|We\s|But\s|However\s|That\s|This\s|Wherever)"
acronyms = "([A-Z][.][A-Z][.](?:[A-Z][.])?)"
websites = "[.](com|net|org|io|gov)"

def main():
    reddit = praw.Reddit('bamboozle_bot', user_agent='bamboozle_bot user agent')
    subreddit = reddit.subreddit('test')
    for comment in subreddit.stream.comments():
            process_submission(comment)

def split_into_sentences(text):
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
    if "”" in text: text = text.replace(".”","”.")
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
    if "link" in comment.body and "?" in comment.body:
        sentences = split_into_sentences(comment.body)
        for sentence in sentences:
            if "?" in sentence and "link" in sentence:
                # print("this is the sentence")
                # print(sentence)
                # print('replies')
                # print(comment.refresh().replies.list())
                for reply in comment.refresh().replies.list():
                    if has_hyperlink(reply.body):
                        print(reply.body)
    #print(split_into_sentences(submission.body))
    # normalized_title = submission.title.lower()
    # print(normalized_title)
    # for question_phrase in QUESTIONS:
    #     if question_phrase in normalized_title:
    #         url_title = quote_plus(submission.title)
    #         reply_text = REPLY_TEMPLATE.format(url_title)
    #         print('Replying to: {}'.format(submission.title))
    #         submission.reply(reply_text)
    #         # A reply has been made so do not attempt to match other phrases.
    #         break
#Find replies with links
def has_hyperlink(text):
    has_hyperlink = False
    reddit_hyperlink_regex = ".*\[.*\]\(.*\).*"
    if re.match(reddit_hyperlink_regex, text):
        print("Found a link reply")
        logger.info("loggin info")
        has_hyperlink = True

    return has_hyperlink
if __name__ == '__main__':
    main()