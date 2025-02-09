import pygame
import os

def load_image(path, scale, colorkey=None, size=None):
    image = pygame.image.load(path)
    w, h = image.get_width(), image.get_height()
    w, h = int(w * scale), int(h * scale)
    if size:
        image = pygame.transform.scale(image, size)
    else:
        image = pygame.transform.scale(image, (w, h))
    if colorkey is not None:
        image.set_colorkey(colorkey)
    return image

def load_images(directory, scale, colorkey=None):
    images = []
    for filename in sorted(os.listdir(directory)):
        if filename.endswith('.png') or filename.endswith('.jpg'):
            path = os.path.join(directory, filename)
            image = load_image(path, scale, colorkey)
            images.append(image)
    return images

def sign(x):
    return 1 if x >= 0 else -1