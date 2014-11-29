import os
from flask import Flask, send_file, render_template

import brewer2mpl
import matplotlib.pyplot as pl
import numpy as np
from cStringIO import StringIO
from PIL import Image

import requests
from BeautifulSoup import BeautifulSoup

import logging      
from logging import FileHandler

app = Flask(__name__)


@app.errorhandler(404)
def page_not_found(error):
  return render_template('404.html'), 404

@app.errorhandler(500)
def page_had_error(error):
  print error
  return render_template('500.html'), 500

def get_user_topics(username):
  r = requests.get('http://www.quora.com/%s/topics?share=1' % username)
  if r.status_code != 200:
    return False
  else:
    return r.text

def parse_user_topics(text):
  soup = BeautifulSoup(text)
  boxes = soup.findAll("div", {"class": "ObjectCard UserTopicPagedListItem PagedListItem"})
  profile_image_url = soup.find("img", {"class": "profile_photo_img"})['src'].encode('utf-8')
  is_topWriter = bool(soup.find("span", {"class": "CurrentTopWriterIcon TopWriterIcon"}))
  topic_data = []
  for box in boxes:
    topic_box = box.find("span", {"class":"TopicName"})
    if not topic_box:
      continue
    topic_name = topic_box.text.encode('utf-8')
    answer_box = box.find("div", {"class":"ObjectCard-body"})
    if not answer_box:
      continue
    answer_count_box = answer_box.a
    if not answer_count_box:
      continue
    answer_count = int(answer_count_box.text.split(' ')[0])
    topic_data.append([topic_name, answer_count])
  return [np.array(topic_data), profile_image_url, is_topWriter]

@app.route('/')
def index():
  return render_template('index.html')

@app.route('/pie/<username>.png')
def chart(username='Giordon-Stark'):
  text = get_user_topics(username)
  if not text: 
    return 'That was not a valid Quora user.', 400

  topic_data, pro_img_url, is_topWriter = parse_user_topics(text)
  if topic_data.size == 0:
    return 'We seem to not be able to find any answers for you.', 400

  # These are the "Tableau 20" colors as RGB.  
  tableau20 = np.array([(31, 119, 180), (174, 199, 232), (255, 127, 14), (255, 187, 120),  
               (44, 160, 44), (152, 223, 138), (214, 39, 40), (255, 152, 150),  
               (148, 103, 189), (197, 176, 213), (140, 86, 75), (196, 156, 148),  
               (227, 119, 194), (247, 182, 210), (127, 127, 127), (199, 199, 199),  
               (188, 189, 34), (219, 219, 141), (23, 190, 207), (158, 218, 229)])
  fontColors = []
  for red, green, blue in tableau20:
    if (red*0.299 + green*0.587 + blue*0.114) > 125:
      fontColors.append((0,0,0))
    else:
      fontColors.append((255, 255, 255))

  # not enough, maxes at 9-12 depending on map
  # colors = brewer2mpl.get_map('Set1', 'qualitative', topic_data.size)
  bgcolors = tableau20[:topic_data.size]/255.
  fgcolors = np.array(fontColors)[:topic_data.size]/255.


  fig, ax = pl.subplots(1,1, figsize=(12,12))
  patches, texts, autotexts = ax.pie(topic_data[:,1],
                                     labels=topic_data[:,0],
                                     colors=bgcolors,
                                     autopct='%1.1f%%',
                                     pctdistance=0.9,
                                     counterclock=False,
                                     wedgeprops={"linewidth":0},
                                     startangle=135,
                                     radius=1.1)
  for t, c, l in zip(autotexts, fgcolors, texts):
    t.set_color(c)
    t.set_size('x-small')
    t.set_weight('bold')
    l.set_size('x-small')

  ax.set_title(username)

  shift = 50
  pro_img_width = 128
  pro_img_height = 128
  img = requests.get(pro_img_url)
  profile_image = Image.open(StringIO(img.content))
  profile_image.thumbnail((pro_img_width, pro_img_height), Image.ANTIALIAS)
  profile_image = np.array(profile_image).astype(np.float) / 255.
  # add profile image
  fig.figimage(profile_image, 0 + shift, ax.bbox.ymax + 9 - shift, alpha=0.75, zorder=50)

  if is_topWriter:
    top_writer_image = Image.open(StringIO(requests.get('https://qsf.is.quoracdn.net/-2e1550e50db8b15f.png').content))
    tw_img_w, tw_img_h = top_writer_image.size
    top_writer_image = np.array(top_writer_image).astype(np.float) / 255.
    fig.figimage(top_writer_image, 0 + shift + pro_img_width - tw_img_w, ax.bbox.ymax + 9 - shift + pro_img_height - tw_img_h, alpha=1.0, zorder=60)

  # dump into a fake filestream
  output = StringIO()
  fig.savefig(output, bbox_inches='tight', transparent=True)
  # point to the correct location for reading
  output.seek(0)
  # output as if it was a file
  return send_file(output,
                   attachment_filename='%s.png' % username,
                   mimetype='image/png'), 200
    
if __name__ == "__main__":
  file_handler = FileHandler("debug.log","a")                                                                                             
  file_handler.setLevel(logging.WARNING)
  app.logger.addHandler(file_handler)

  app.run(debug=False)

