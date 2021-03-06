# -*- coding: utf-8 -*-
"""proyecto_final_equipo2.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1_EmRwV9EdPQ-q7OZJcV1WQGyKgWejbm1

# Equipo 2
## Miembros:
### Jorge Arturo Torres Cruz - A01176590
### Juan Manuel Pérez Font - A00819815

## Recolección de datos
"""

# Para uso en colab
# from google.colab import drive
# drive.mount('/content/drive')

# ==== FOR REFERENCE =====
# ['wines.txt', 'bubble_gums.txt', 'dumplings.txt', 'pizza_urls.txt', 'sandwich.txt']
# =========== ============
url_files = ['wines.txt', 'bubble_gums.txt', 'dumplings.txt', 'pizza.txt', 'sandwich.txt']

# ==== FOR REFERENCE =====
# ['wine','bubble_gum', 'dumplings', 'pizza', 'sandwich']
# ========================
categories = ['wine', 'bubble_gum', 'dumpling', 'pizza', 'sandwich']

data_directory = './data' # Where image data and models will be stored

def read_urls_from_txt(files):
  """Reads all urls from the txt files in files

  Args:
      files (list): List of txt files

  Returns:
      array: an array with all urls extracted by category 
  """
  # Iteramos por cada uno de los archivos y obtenemos los URLs de las imagenes.
  print("Reading files containing images urls")
  urls = []
  for file_name in files:
    with open(f'{data_directory}/{file_name}') as f:
      content = f.readlines()
      content = [url.strip() for url in content]
      print(f'Reading {len(content)} image urls ({file_name})')
      urls.append(content)
  return urls

# Utilizaremos urllib para descargar las imagenes utilizando URLs obtenidos de ImageNet
import urllib.request
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
import uuid
from itertools import repeat

def download_from_url(category_url):
  """Downloads a single an image from the given url with urllib.

  Args:
      category_url (tuple): A tuple containing a url and its category in the form (category, url)

  Returns:
      str: A string with the url if success, an error string otherwise
  """
  category, url = category_url
  print(f'Downloading {url} for category {category}')
  try:
    urllib.request.urlretrieve(url, f'{data_directory}/{category}/{uuid.uuid4()}.jpg')
    return url
  except Exception as e:
    print('Error')
    return f'Error: {e}'

def download_category_from_url(category, urls):
  """Download images from all urls from a given category

  Args:
      category (str): The category name
      urls (list): A list of urls from the category

  Returns:
      A ThreadPoolExecutor results: The results from the ThreadPoolExecutor
  """
  try:
    print(f'Creating directory to store {category} images')
    os.mkdir(f'{data_directory}/{category}')
  except FileExistsError:
    print(f'{data_directory}/{category} directory exists, continuing...')
  except Exception as e:
    print(e)
  else:
    print(f'Succesfully created {category}/ directory')
  results = None
  with ThreadPoolExecutor(max_workers=5) as executor:
    return executor.map(download_from_url, zip(repeat(category), urls), timeout=0.5)

try:
  os.mkdir(data_directory)
except FileExistsError:
  print('data directory exists, continuing...')

# Download data. Commented in order to work out of the box for training.
# urls = read_urls_from_txt(url_files)
# for idx, category in enumerate(categories):
#   download_category_from_url(category, urls[idx])

"""## Generación de datos"""
import numpy as np
import imgaug.augmenters as iaa
import cv2
import glob

def augment_data():
  """
  Generates new data based on downloaded images by applying left-to-right flip, Gaussian Blur,
  Salt and Pepper, GammaContrast and Additive gaussian noise with varying probabilities. Each image
  is augmented twice, resulting in triple the original data.
  """
  print('Augmenting data by flipping and Gaussian Blur...')
  seq = iaa.Sequential([
    iaa.Fliplr(0.65),
    iaa.Sometimes(then_list=[
      iaa.OneOf([
        iaa.GammaContrast(gamma=(0.5, 1.75)),
        iaa.GaussianBlur(sigma=(0, 2.0))
      ])
    ]),
    iaa.Sometimes(p=0.55, then_list=[
      iaa.AdditiveGaussianNoise(scale=0.10*255)
    ]),
    iaa.Sometimes(p=0.3, then_list=[
      iaa.SaltAndPepper(p=0.05)
    ])
  ], random_order=True)

  for sec in ['test', 'train', 'valid']:
    for category in categories:
      batch = []
      for filename in glob.iglob(f'{data_directory}/{sec}/{category}/*'):
        print(f'Reading {filename}')
        try:
          im = cv2.imread(filename)
          cv2.cvtColor(im, cv2.COLOR_BGR2RGB)
          batch.append(im)
          batch.append(im)
        except Exception as e:
          print(f'Error on image: {filename}, continuing...')
      images_aug = seq(images=np.array(batch))
      for image in images_aug:
        cv2.imwrite(f'{data_directory}/{sec}/{category}/{uuid.uuid4()}.jpg', image)
        print(f'Artificial data saved for category {category}')
      print(f'=== {len(batch)} new images added to category {category} ===')

# Augment data. Commented in order to work out of the box for training.
# augment_data()

"""## Separar train, test y validate"""

import random
import shutil
from tensorflow.keras.preprocessing.image import ImageDataGenerator
import tensorflow as tf
import matplotlib.pyplot as plt

from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Activation, Dense, Flatten, BatchNormalization, Conv2D, MaxPool2D, MaxPooling2D, Dropout
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.metrics import categorical_crossentropy
from tensorflow.keras.models import load_model
from sklearn.metrics import confusion_matrix
import itertools
import matplotlib.pyplot as plt

try:
  os.mkdir(f'{data_directory}/train')
except FileExistsError as e:
  print('train directory already exists, continuing...')
try:
  os.mkdir(f'{data_directory}/test')
except FileExistsError as e:
  print('test directory already exists, continuing...')
try:
  os.mkdir(f'{data_directory}/valid')
except FileExistsError as e:
  print('validate directory already exists, continuing...')

for category in categories:
  try:
    os.mkdir(f'{data_directory}/train/{category}')
    os.mkdir(f'{data_directory}/valid/{category}')
    os.mkdir(f'{data_directory}/test/{category}')
  except FileExistsError as e:
    print(f'{category} directory already exists, continuing...')

  try:
    images = glob.glob(f'{data_directory}/{category}/*')
    for i in random.sample(images, int(len(images) * 0.8)):
      shutil.move(i, f'{data_directory}/train/{category}/')
    images = glob.glob(f'{data_directory}/{category}/*')
    for i in random.sample(images, int(len(images) * 0.5)):
      shutil.move(i, f'{data_directory}/valid/{category}/')
    images = glob.glob(f'{data_directory}/{category}/*')
    for i in random.sample(images, int(len(images))):
      shutil.move(i, f'{data_directory}/test/{category}/')

    os.rmdir(f'{data_directory}/{category}')
  except FileNotFoundError as e:
    print('Directory already deleted, continuing...')

def clean_images():
  dirs = ['train', 'test', 'valid']
  for d in dirs:
    for category in categories:
      for f in glob.glob(f'{data_directory}/{d}/{category}/*'):
        try:
          im = cv2.imread(f)
          cv2.cvtColor(im, cv2.COLOR_BGR2RGB)
          with open(f, 'rb') as fl:
            check_chars = fl.read()[-2:]
          if check_chars != b'\xff\xd9':
            print('Not complete image')
            os.remove(f)
          else:
            print(f'{f} image ok')
        except Exception as e:
          os.remove(f)
          print(f'{f} image erased')

# Clean corrupted jpg images. Commented in order to work out of the box for training.
# clean_images()

train_data = f'{data_directory}/train'
test_data = f'{data_directory}/test'
valid_data = f'{data_directory}/valid'

batch_size = 10

train_batches = ImageDataGenerator(preprocessing_function=tf.keras.applications.vgg16.preprocess_input) \
  .flow_from_directory(directory=train_data, target_size=(224,224), classes=['wine', 'pizza', 'bubble_gum', 'dumpling', 'sandwich'], batch_size=batch_size)
test_batches = ImageDataGenerator(preprocessing_function=tf.keras.applications.vgg16.preprocess_input) \
  .flow_from_directory(directory=test_data, target_size=(224,224), classes=['wine', 'pizza', 'bubble_gum', 'dumpling', 'sandwich'], batch_size=batch_size, shuffle=False)
valid_batches = ImageDataGenerator(preprocessing_function=tf.keras.applications.vgg16.preprocess_input) \
  .flow_from_directory(directory=valid_data, target_size=(224,224), classes=['wine', 'pizza', 'bubble_gum', 'dumpling', 'sandwich'], batch_size=batch_size)

vgg16_model = tf.keras.applications.vgg16.VGG16()

model = Sequential()
for layer in vgg16_model.layers[:-1]:
  model.add(layer)

for layer in model.layers:
  layer.trainable = False

model.add(Dense(units=5, activation='softmax'))

model.compile(optimizer=Adam(learning_rate=0.0001), loss='categorical_crossentropy', metrics=['accuracy'])

# Train model
model.fit(
  x=train_batches,
  validation_data=valid_batches,
  epochs=10,
  verbose=2
)
model.save('fourth_try.h5')

def plot_confusion_matrix(cm, classes,
                          normalize=False,
                          title='Confusion matrix',
                          cmap=plt.cm.Blues):
  """
  This function prints and plots the confusion matrix.
  Normalization can be applied by setting `normalize=True`.
  """
  plt.imshow(cm, interpolation='nearest', cmap=cmap)
  plt.title(title)
  plt.colorbar()
  tick_marks = np.arange(len(classes))
  plt.xticks(tick_marks, classes, rotation=45)
  plt.yticks(tick_marks, classes)

  if normalize:
      cm = cm.astype('float') / cm.sum(axis=1)[:, np.newaxis]
      print("Normalized confusion matrix")
  else:
      print('Confusion matrix, without normalization')

  print(cm)

  thresh = cm.max() / 2.
  for i, j in itertools.product(range(cm.shape[0]), range(cm.shape[1])):
      plt.text(j, i, cm[i, j],
          horizontalalignment="center",
          color="white" if cm[i, j] > thresh else "black")

  plt.tight_layout()
  plt.ylabel('True label')
  plt.xlabel('Predicted label')

# Load model
model = load_model('first_try.h5')

# Make predictions with model
predictions = model.predict(x=test_batches, verbose=0)

cm = confusion_matrix(y_true=test_batches.classes, y_pred=np.argmax(predictions, axis=-1))

# Plot confusion matrix
plot_confusion_matrix(cm=cm, classes=categories, title='Confusion Matrix')
