import sys
sys.path.insert(1, '../src/')
sys.path.insert(1, 'src/')

import matplotlib.pyplot as plt
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure

from PIL import Image as im

import cv2
import numpy as np

import overlay_handler

def draw_image(image, title='Sample Image'):
  plt.title(title)
  # plt.plot(image)
  plt.imshow(image)
  plt.show()

# h = 320
# w = 240

h = 1012
w = 760
img = np.array(overlay_handler.generate_overlay_image(h,w))

print(img.size)
# img_cv2 = cv2.imdecode(img, cv2.IMREAD_UNCHANGED)
# rgba = cv2.cvtColor(img, cv2.COLOR_RGB2RGBA)
# img_cv2 = cv2.imdecode(rgba, cv2.IMREAD_UNCHANGED)

data = im.fromarray(img)
data.save('c:\\development\\test.png')

draw_image(cv2.imread('c:\\development\\test.png'))
