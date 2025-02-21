import pygame
import os

def load_image(path, scale, colorkey=None, size=None, bounding=False):
    image = pygame.image.load(path).convert_alpha()
    if size is not None:
        image = pygame.transform.scale(image, size)
    else:
        image = pygame.transform.scale(image, (int(image.get_width() * scale), int(image.get_height() * scale)))
    if bounding:
        brect = image.get_bounding_rect()
        surf = pygame.Surface(brect.size)
        surf.blit(image, (0, 0), (brect.x, brect.y, brect.width, brect.height))
        image = surf
    if colorkey:
        image.set_colorkey(colorkey)
    return image

def load_images(directory, scale, colorkey=None, size=None, bounding=True):
    images = []
    for filename in sorted(os.listdir(directory)):
        if filename.endswith('.png') or filename.endswith('.jpg'):
            path = os.path.join(directory, filename)
            image = load_image(path, scale, colorkey, size=size, bounding=bounding)
            images.append(image)
    return images

def sign(x):
    return 1 if x >= 0 else -1