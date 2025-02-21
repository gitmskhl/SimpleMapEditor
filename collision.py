import pygame
import sys

pygame.init()

screen = pygame.display.set_mode((800, 600), pygame.NOFRAME)
clock = pygame.time.Clock()

wizard_img = pygame.image.load('Idle.png')
width = wizard_img.get_width() // 6
height = wizard_img.get_height()
surf = pygame.Surface((width, height))
surf.blit(wizard_img, (0, 0), (0, 0, width, height))
surf.set_colorkey((0,) * 3)
wizard1 = surf
wizard2 = surf.copy()

rect1 = wizard1.get_bounding_rect()
rect2 = wizard2.get_bounding_rect()

mask1 = pygame.mask.from_surface(wizard1)
mask2 = pygame.mask.from_surface(wizard2)

x1, y1 = 0, 0
x2, y2 = 200, 200
l1, r1, u1, d1 = (False,) * 4
speed = 5

def collision():
    global x1, y1
    rect1.topleft = (x1, y1)
    rect2.topleft = (x2, y2)
    if not rect1.colliderect(rect2): return
    overlap = mask1.overlap_mask(mask2, (x2 - x1, y2 - y1))
    if overlap.count() == 0: return
    dx = dy = 5
    x1 -=  (r1 - l1) * dx
    y1 -= (d1 - u1) * dy
    print('collision detected')

while True:
    clock.tick(60)
    screen.fill((0,) * 3)

    x1 += (r1 - l1) * speed
    y1 += (d1 - u1) * speed
    screen.blit(wizard1, (x1, y1))
    screen.blit(wizard2, (x2, y2))

    collision()

    for event in pygame.event.get():
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                pygame.quit()
                sys.exit()
            elif event.key == pygame.K_LEFT:
                l1 = True
            elif event.key == pygame.K_RIGHT:
                r1 = True
            elif event.key == pygame.K_UP:
                u1 = True
            elif event.key == pygame.K_DOWN:
                d1 = True
        elif event.type == pygame.KEYUP:
            if event.key == pygame.K_LEFT:
                l1 = False
            if event.key == pygame.K_RIGHT:
                r1 = False
            if event.key == pygame.K_UP:
                u1 = False
            if event.key == pygame.K_DOWN:
                d1 = False

    pygame.display.flip()