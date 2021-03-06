# -*- coding: utf-8 -*-
"""proyecto_final_equipo2.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1Q11XBceWMJl2HSH_3uoTPiL3_yDMz_QQ

# Equipo 2
## Miembros:
### Jorge Arturo Torres Cruz - A01176590
### Juan Manuel Pérez Font - A00819815
### Sergio López Madriz - A01064725

## Librerías
"""

# Utilizaremos urllib para descargar las imagenes utilizando URLs obtenidos de ImageNet
import urllib.request
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
import uuid
from itertools import repeat
from pathlib import Path
import socket
import cv2
import numpy as np
from keras.utils import to_categorical
from keras.models import Sequential
from keras.layers import Dense, Conv2D, MaxPooling2D, Dropout, Flatten
socket.setdefaulttimeout(10)

"""## Recolección de datos"""

# Para uso en colab
from google.colab import drive
drive.mount('/content/drive')

data_directory = './drive/My Drive/food_classification/data'
data_path = Path(data_directory)
url_files = [x for x in data_path.iterdir() if x.is_file()]
categories = ['wines', 'bubble_gums', 'dumplings', 'pizza', 'sandwich']

# Iteramos por cada uno de los archivos y obtenemos los URLs de las imagenes.
print("Reading files containing images urls")
urls = {}
for file_path in url_files:
    category = file_path.stem
    with file_path.open() as f:
        content = f.readlines()
        content = [url.strip() for url in content]
        print("Reading {} image urls ({})".format(len(content), file_path))
        urls[category] = content

working_urls = {
    'bubble_gums': [],
    'dumplings': [],
    'pizza': [],
    'sandwich': [],
    'wines': []
}

def download_from_url(category_url):
    category, url = category_url
    print(f'Downloading {url} for category {category}')
    try:
        urllib.request.urlretrieve(url, f'{data_path}/{category}/{uuid.uuid4()}.jpg')
        working_urls[category].append(url)
        return url
    except Exception as e:
        print('Error')
        return f'Error: {e}'

def download_category_from_url(category, urls):
    try:
        print(f'Creating directory to store {category} images')
        category_dir_path = data_path / category
        category_dir_path.mkdir(parents=True)
    except FileExistsError:
        print(f'{category_dir_path} directory exists, continuing...')
    except Exception as e:
        print(e)
    else:
        print(f'Succesfully created {category}/ directory')
    results = None
    print(f'Downloading images for category {category}')
    with ThreadPoolExecutor() as executor:
        executor.map(download_from_url, zip(repeat(category), urls), timeout=10)
    print(f'All images downloaded for category {category}')

try:
    data_path.mkdir()
except FileExistsError:
    print('data directory exists, continuing...')
for category, category_urls in urls.items():
    download_category_from_url(category, category_urls)
print('All images downloaded into data folder')

for category, urls in working_urls.items():
    print(f'{category}: {len(urls)}')
    # f=open(f'{category}.txt','w')
    # l1 = map(lambda x:x+'\n', urls)
    # f.writelines(l1)
    # f.close()

"""## Generación de datos"""

# The default version of imgaug doesn't correctly support loading a 1d numpy array to augmenters
!pip install imgaug==0.4.0

import numpy as np
import imgaug.augmenters as iaa
import cv2
import glob

def augment_data():
  """
  Generates new data based on downloaded images by applying left-to-right flip
  and Gaussian Blur.
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

  for category in categories:
    batch = []
    for filename in glob.iglob(f'{data_directory}/{category}/*'):
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
      cv2.imwrite(f'{data_directory}/{category}/{uuid.uuid4()}.jpg', image)
      print(f'Artificial data saved for category {category}')
    print(f'=== {len(batch)} new images added to category {category} ===')

augment_data()

"""## Separar train, test y validate
### Separamos 80% train, 10% validate y 10% test para cada clase
"""

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
# import os
# import shutil
# import random
# import glob
import matplotlib.pyplot as plt
# import warnings

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
  print('valid directory already exists, continuing...')

for category in categories:
  try:
    os.mkdir(f'{data_directory}/train/{category}')
    os.mkdir(f'{data_directory}/valid/{category}')
    os.mkdir(f'{data_directory}/test/{category}')
  except FileExistsError as e:
    print(f'{category} directory already exists, continuing...')

  images = glob.glob(f'{data_directory}/{category}/*')
  for i in random.sample(images, int(len(images) * 0.8)):
    shutil.move(i, f'{data_directory}/train/{category}/')

  images = glob.glob(f'{data_directory}/{category}/*') # Get files again, since they were moved
  for i in random.sample(images, int(len(images) * 0.5)):
    shutil.move(i, f'{data_directory}/valid/{category}/')

  images = glob.glob(f'{data_directory}/{category}/*')
  for i in random.sample(images, int(len(images))):
    shutil.move(i, f'{data_directory}/test/{category}/')

  # ====== Ocasiona problemas si se utiliza con Drive =========
  # os.remove(f'{data_directory}/{category}')

"""# Aprendizaje"""

# Creamos la CNN
model = Sequential()
model.add(Conv2D(32, kernel_size=3, activation='relu', input_shape=(150, 150, 3)))
model.add(MaxPooling2D(2, 2))
model.add(Conv2D(64, kernel_size=3, activation='relu'))
model.add(MaxPooling2D(2, 2))
model.add(Conv2D(128, kernel_size=3, activation='relu'))
model.add(MaxPooling2D(2, 2))
model.add(Conv2D(256, kernel_size=3, activation='relu'))
model.add(MaxPooling2D(2, 2))
model.add(Flatten())
model.add(Dropout(0.5))
model.add(Dense(5, activation='softmax'))

from keras.models import load_model
from keras.callbacks import ModelCheckpoint

save_path = './drive/My Drive/food_classification/data/model/checkpoint'

def load_saved_model():
  loaded_model = None
  try:
    loaded_model = load_model(save_path)
  except Exception as e:
    print("An error ocurred while loading the model:")
    print(e)
  return loaded_model

# ======= Correr si ya se tiene un modelo parcialmente o completamente entrenado.
model = load_saved_model()

# image width
rows = 150
# image height
cols = 150 
channels = 3

X_train = []
y_train = []
X_val = []
y_val = []

def get_category_class(category):
  class_num = { 'wines': 0, 'bubble_gums': 1, 'dumplings': 2, 'pizza': 3, 'sandwich': 4}
  return class_num[category]

# Lee todos los nombres de las imagenes de un directorio y las guarda en una lista
def read_imgs_and_set_class(dir_name, category):
  path = '{}/{}/{}/'.format(data_directory, dir_name, category)
  img_filenames = ['{}{}'.format(path, name) for name in os.listdir(path)]
  print("Fetched {} image filenames for category {}".format(len(img_filenames), category))
  X = []
  y = []
  debug_counter = 0
  for image in img_filenames:
    try:
      X.append(cv2.resize(cv2.imread(image, cv2.IMREAD_COLOR), (rows, cols), interpolation=cv2.INTER_CUBIC))
      y.append(get_category_class(category))
    except Exception as e:
      pass
    finally:
      debug_counter += 1
      if debug_counter % 150 == 0:
        print("X is {} size and y is {} size".format(len(X), len(y)))
  print("Loaded X ({} data points) and y ({} data points) [{}]".format(len(X), len(y), dir_name))
  return (X, y)

# Genera los datos para X_train y y_train
def create_data_sets():
  # Obtenemos la data de entrenamiento
  for category in categories:
    X, y = read_imgs_and_set_class('train', category)
    X_train.extend(X)
    y_train.extend(y)
  
  for category in categories:
    X, y = read_imgs_and_set_class('valid', category)
    X_val.extend(X)
    y_val.extend(y)
  
  print("Final X_train size: {}".format(len(X_train)))
  print("Final y_train size: {}".format(len(y_train)))

create_data_sets()

# Checamos de que clases agregamos data
print(set(y_train))
print(set(y_val))

# Copy de data por si se aplican transformaciones que no deve
X_copy = X_train
y_copy = y_train
X_val_copy = X_val
y_val_copy = y_val

# Np array transformations
X_train = np.array(X_train)
y_train = np.array(y_train)
X_val = np.array(X_val)
y_val = np.array(y_val)

# Convertimos la data a valores categoricos (para no tener 0,1,2,3,4)
y_train = to_categorical(y_train)
y_val = to_categorical(y_val)

print(model.summary())

"""## Entrenamiento"""

# Definimos la política para guardar a un modelo
model_checkpoint_callback = ModelCheckpoint(
    filepath=save_path,
    save_weights_only=False,
    monitor='val_acc',
    mode='max',
    save_best_only=False)

# Entrenamos al modelo
model.compile(optimizer='adam', loss='categorical_crossentropy', metrics=['accuracy'])
model.fit(X_train, y_train, validation_data=(X_val, y_val), epochs=61, callbacks=[model_checkpoint_callback])

"""# Probar el modelo"""

X_test = []
y_test = []

def create_test_data():
  # Obtenemos la data de entrenamiento
  for category in categories:
    X, y = read_imgs_and_set_class('test', category)
    X_test.extend(X)
    y_test.extend(y)

create_test_data()

X_test = np.array(X_test)
y_test = np.array(y_test)
y_test = to_categorical(y_test)

loss, acc = model.evaluate(X_test, y_test, verbose=2)
print('Restored model, accuracy: {:5.2f}%'.format(100*acc))
