import os
from flask import Flask
from flask import send_file

import matplotlib.pyplot as pl
import numpy as np

import StringIO

import logging      
from logging import FileHandler

app = Flask(__name__)

@app.route('/')
def index():
  return 'Get image <img src="/pie?user=Giordon-Stark" />'

@app.route('/pie/<user>')
def chart(user='Test'):
  fig, ax = pl.subplots(1,1, figsize=(8,6))
  ax.scatter(np.random.randn(100), np.random.randn(100))
  ax.set_title(user)

  # dump into a fake filestream
  output = StringIO.StringIO()
  fig.savefig(output)
  # point to the correct location for reading
  output.seek(0)
  # output as if it was a file
  return send_file(output,
                   attachment_filename='%s.png' % user,
                   mimetype='image/png')

if __name__ == "__main__":
  file_handler = FileHandler("debug.log","a")                                                                                             
  file_handler.setLevel(logging.WARNING)
  app.logger.addHandler(file_handler)

  app.run()

