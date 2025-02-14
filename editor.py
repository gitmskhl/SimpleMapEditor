import pygame
import os
import json
from collections import deque
import copy

from scripts import utils

if __name__ == "__main__":
    pygame.init()
    HISTORY_MAX=10000
    GRAY = (50,) * 3

    SCREEN_WIDTH = 800
    SCREEN_HEIGHT = 600

    MAX_FILLED_SECTOR = 500

# 16 x 16 is the base
class Editor:
    TRANSFORM_TILES = {'grass', 'stone'}
    TRANSFORM_RULES = {
        ((1, 0),): 0,
        ((-1, 0), (1, 0)): 1,
        ((-1, 0),): 2,
        ((0, -1), (0, 1), (-1, 0)): 3,
        ((0, -1), (-1, 0)): 4,
        ((0, -1), (-1, 0), (1, 0)): 5,
        ((0, -1), (1, 0)): 6,
        ((0, -1), (1, 0), (0, 1)): 7,
        ((0, -1), (0, 1), (1, 0), (-1, 0)): 5
    }
    TRANSFORM_RULES = {tuple(sorted(k)): v for k, v in TRANSFORM_RULES.items()}

    def __init__(self):
        self.base_tile_size = 16
        self.tile_size = 16
        self.k = 1
        self.tile_map = {}
        self.nogrid_tiles = []
        self._load_resources()
        self.resource_names = list(self.resources.keys())
        self.current_resource = self.resource_names[0]
        self.current_variant = 0
        # mouse
        self.clicked = [False, False, False]
        self.pressed = [False, False, False]
        self.shift = False
        # grid  
        self.grid = True
        # camera
        self.camera = [0, 0]
        self.move = [0, 0]
        #history
        self.history = []
        self.history_index = 0
        self.load()
        # fill
        self.last_ij_filled = None
        self.last_filled = None
        # select area
        self.start_selected_area = []
        self.selected_area = []
        self.moving_selected_area = False
        self.moving_tiles = None
        self.start_mouse_position = None

    def transform(self):
        sarect = self._get_selected_area_rect()
        for pos, tile in self.tile_map.items():
            tilerect = pygame.Rect(pos[0] * self.tile_size, pos[1] * self.tile_size, self.tile_size, self.tile_size)
            if sarect and not tilerect.colliderect(sarect): continue
            if tile['resource'] in Editor.TRANSFORM_TILES:
                neighbours = []
                for i in range(-1, 2):
                    for j in range(-1, 2):
                        if i == 0 and j == 0 or i != 0 and j != 0: continue
                        if (pos[0] + i, pos[1] + j) in self.tile_map and self.tile_map[(pos[0] + i, pos[1] + j)]['resource'] == tile['resource']:
                            neighbours.append((i, j))
                situation = tuple(sorted(neighbours))
                if situation in Editor.TRANSFORM_RULES:
                    tile['variant'] = Editor.TRANSFORM_RULES[situation]
                else:
                    suits = []
                    for req_situation in Editor.TRANSFORM_RULES:
                        if all([x in situation for x in req_situation]):
                            suits.append(req_situation)
                    if suits:
                        suit_situation = sorted(suits, key=lambda x: -len(x))[0]
                        tile['variant'] = Editor.TRANSFORM_RULES[suit_situation]

    def _resize_resources(self):
        for dirname in os.listdir('resources'):
            self.resources[dirname] = utils.load_images('resources/' + dirname, self.tile_size / 16, (0, 0, 0))

    def _load_resources(self):
        self.resources = {}
        self.resource_props = {}
        for dirname in os.listdir('resources'):
            self.resources[dirname] = utils.load_images('resources/' + dirname, 1, (0, 0, 0))
            res_count = len(self.resources[dirname])
            info_path = os.path.join('resources', dirname, 'info.txt')
            self.resource_props[dirname] = {}
            if os.path.exists(info_path):
                with open(info_path, 'r') as f:
                    for line in f:
                        lst = line.split(':')
                        prop = lst[0].strip()
                        if len(lst) == 1:
                            self.resource_props[dirname][prop] = [True] * res_count
                        else:
                            self.resource_props[dirname][prop] = [False] * res_count
                            idxs = [int(i) for i in lst[1].split(' ') if i]
                            for i in idxs:
                                self.resource_props[dirname][prop][int(i)] = True
        self._resize_resources()

    def _draw_grid(self, screen, i_start, j_start, i_end, j_end):
        for j in range(j_start, j_end):
            pygame.draw.line(
                screen,
                GRAY,
                (0, j * self.tile_size - self.camera[1]),
                (SCREEN_WIDTH, j * self.tile_size - self.camera[1])
            )
        for i in range(i_start, i_end):
            pygame.draw.line(
                screen,
                GRAY,
                (i * self.tile_size - self.camera[0], 0),
                (i * self.tile_size - self.camera[0], SCREEN_HEIGHT)
            )


    def _get_filled(self, pos):
        result = []
        i, j = pos[0] // self.tile_size, pos[1] // self.tile_size
        if (i, j) in self.tile_map: return []
        d = deque()
        d.append((i, j))
        while len(d) > 0 and len(result) < MAX_FILLED_SECTOR:
            i_, j_ = d.popleft()
            result.append((i_, j_))
            for p, q in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                tup = (i_ + p, j_ + q)
                if (tup not in result) and (tup not in d) and (tup not in self.tile_map):
                    d.append(tup)
        self.last_ij_filled = (i, j)
        self.last_filled = result
        return result

    def _render_moving_tiles(self):
        if not self.moving_tiles: return
        mx, my = pygame.mouse.get_pos()
        mx += self.camera[0]
        my += self.camera[1]
        shiftx = mx - self.start_mouse_position[0]
        shifty = my - self.start_mouse_position[1]
        for pos, tile in self.moving_tiles:
            xrel = pos[0] * self.tile_size + shiftx
            yrel = pos[1] * self.tile_size + shifty
            tx = xrel // self.tile_size
            ty = yrel // self.tile_size
            tile_img = self.resources[tile['resource']][tile['variant']]
            tile_img.set_alpha(100)
            screen.blit(tile_img, (tx * self.tile_size - self.camera[0], ty * self.tile_size - self.camera[1]))
            tile_img.set_alpha(255)

    def render(self, screen):
        i_start = int(self.camera[0] // self.tile_size)
        j_start = int(self.camera[1] // self.tile_size)
        i_end = int((self.camera[0] + SCREEN_WIDTH) // self.tile_size + 1)
        j_end = int((self.camera[1] + SCREEN_HEIGHT) // self.tile_size + 1)
        if self.grid:
            self._draw_grid(screen, i_start, j_start, i_end, j_end)
        moving_tiles_positions = set([x for x, _ in self.moving_tiles]) if self.moving_selected_area else set()
        for i in range(i_start - 1, i_end + 1):
            for j in range(j_start - 1, j_end + 1):
                if (i, j) in moving_tiles_positions: continue
                if (i, j) in self.tile_map:
                    tile = self.tile_map[(i, j)]
                    img = self.resources[tile['resource']][tile['variant']]
                    screen.blit(img, (i * self.tile_size - self.camera[0], j * self.tile_size - self.camera[1]))
        for tile in self.nogrid_tiles:
            img = self.resources[tile['resource']][tile['variant']]
            if tile['pos'][0] * self.k - self.camera[0] + img.get_width() < 0 or tile['pos'][0] * self.k - self.camera[0] > SCREEN_WIDTH:
                continue
            if tile['pos'][1] * self.k - self.camera[1] + img.get_height() < 0 or tile['pos'][1] * self.k - self.camera[1] > SCREEN_HEIGHT:
                continue
            screen.blit(img, (tile['pos'][0] * self.k - self.camera[0], tile['pos'][1] * self.k - self.camera[1]))
        
        selected_img = self.resources[self.current_resource][self.current_variant]
        selected_img.set_alpha(100)
        mpos = pygame.mouse.get_pos()
        if not self.grid or not fill_activated:
            if self.grid:
                pos = ((mpos[0] + self.camera[0])//self.tile_size*self.tile_size - self.camera[0], (mpos[1] + self.camera[1])//self.tile_size*self.tile_size - self.camera[1])
            else: 
                pos=mpos
            screen.blit(selected_img, pos)
        elif fill_activated:
            pos = (mpos[0] + self.camera[0], mpos[1] + self.camera[1])
            if (pos[0] // self.tile_size * self.tile_size, pos[1] // self.tile_size * self.tile_size) == self.last_ij_filled:
                filled = self.last_filled
            else:
                filled = self._get_filled(pos)
            for i, j in filled:
                screen.blit(selected_img, (i * self.tile_size - self.camera[0], j * self.tile_size - self.camera[1]))
        selected_img.set_alpha(255)
        self._render_selected_area()
        if self.moving_selected_area:
            self._render_moving_tiles()
                
    def _render_selected_area(self):
        if not self.selected_area or self.selected_area[0] == self.selected_area[1]: return
        s = tuple(
            min(self.selected_area[0][i], self.selected_area[1][i])
            for i in range(2)
        )
        e = tuple(
            max(self.selected_area[0][i], self.selected_area[1][i])
            for i in range(2)
        )
        pygame.draw.rect(screen, (255, 255, 255), (s[0] - self.camera[0], s[1] - self.camera[1], e[0] - s[0], e[1] - s[1]), 1)


    def _get_selected_area_rect(self):
        if not self.selected_area or self.selected_area[0] == self.selected_area[1]: return None
        s = tuple(
            min(self.selected_area[0][i], self.selected_area[1][i])
            for i in range(2)
        )
        e = tuple(
            max(self.selected_area[0][i], self.selected_area[1][i])
            for i in range(2)
        )
        return pygame.Rect(s[0], s[1], e[0] - s[0], e[1] - s[1])

    def _add_history(self, action, pos, tile, type):
        self.history = self.history[:self.history_index]
        self.history.append(
            {
                'action': action,
                'pos': pos,
                'type': type,
                'tile': tile
            }
        )
        self.history_index += 1
        if self.history_index > HISTORY_MAX:
            self.history_index = HISTORY_MAX
            self.history = self.history[-HISTORY_MAX:]

    def _add_grid_tile(self, pos):
        if not fill_activated:
            i = int((pos[0] + self.camera[0]) // self.tile_size)
            j = int((pos[1] + self.camera[1]) // self.tile_size)
            self.tile_map[(i, j)] = {'resource': self.current_resource, 'variant': self.current_variant}
            self._add_history('add', (i, j), self.tile_map[(i, j)], 'grid')
        else:
            for i, j in self.last_filled:
                self.tile_map[(i, j)] = {'resource': self.current_resource, 'variant': self.current_variant}
            tile = {'resource': self.current_resource, 'variant': self.current_variant}
            self._add_history('add_filled', self.last_filled, tile, 'grid')


    def _add_nogrid_tile(self, pos):
        pos = ((pos[0] + self.camera[0]) / self.k, (pos[1] + self.camera[1]) / self.k)
        self.nogrid_tiles.append({'resource': self.current_resource, 'variant': self.current_variant, 'pos': pos})
        self._add_history('add', pos, self.nogrid_tiles[-1], 'nogrid')

    def _del_grid_tile(self, pos):
        i = int((pos[0] + self.camera[0]) // self.tile_size)
        j = int((pos[1] + self.camera[1]) // self.tile_size)
        if (i, j) in self.tile_map:
            tile = self.tile_map[(i, j)]
            del self.tile_map[(i, j)]
            self.history = self.history[:self.history_index]
            self._add_history('delete', (i, j), tile, 'grid')

    def _del_nogrid_tile(self, pos):
        # pos = (pos[0] + self.camera[0], pos[1] + self.camera[1])
        pos = ((pos[0] + self.camera[0]) / self.k, (pos[1] + self.camera[1]) / self.k)
        for tile in self.nogrid_tiles:
            img = self.resources[tile['resource']][tile['variant']]
            if img.get_rect(topleft=tile['pos']).collidepoint(pos):
                self.nogrid_tiles.remove(tile)
                self.history = self.history[:self.history_index]
                break

    def _remove_tiles_in_selected_area(self):
        sarect = self._get_selected_area_rect()
        if not sarect: return
        for pos, _ in self._get_tiles_in_area(sarect):
            del self.tile_map[pos]

    def _save_moved_tiles(self):
        mx, my = pygame.mouse.get_pos()
        mx += self.camera[0]
        my += self.camera[1]
        shiftx = mx - self.start_mouse_position[0]
        shifty = my - self.start_mouse_position[1]
        self._add_history('move_selected_area', (shiftx, shifty), self.moving_tiles, 'grid')
        for pos, tile in self.moving_tiles:
            xrel = pos[0] * self.tile_size + shiftx
            yrel = pos[1] * self.tile_size + shifty
            tx = xrel // self.tile_size
            ty = yrel // self.tile_size
            del self.tile_map[pos]
            self.tile_map[(tx, ty)] = tile

# This algo can be more efficient
    def _get_tiles_in_area(self, rect):
        tiles = []
        for pos, tile in self.tile_map.items():
            tilerect = pygame.Rect(pos[0] * self.tile_size, pos[1] * self.tile_size, self.tile_size, self.tile_size)
            if tilerect.colliderect(rect):
                tiles.append((pos, tile))
        return tiles
    

    def _is_start_moving_selected_area(self):
        sarect = self._get_selected_area_rect()
        mpos = pygame.mouse.get_pos()
        return self.pressed[0] and sarect and sarect.collidepoint(mpos[0] + self.camera[0], mpos[1] + self.camera[1])

    def update(self):
        self.camera[0] += self.move[0]
        self.camera[1] += self.move[1]

        if self.moving_selected_area:
            mx, my = pygame.mouse.get_pos()
            mx += self.camera[0]
            my += self.camera[1]
            shiftx = mx - self.start_mouse_position[0]
            shifty = my - self.start_mouse_position[1]
            for i in range(2):
                self.selected_area[i][0] = self.start_selected_area[i][0] + shiftx
                self.selected_area[i][1] = self.start_selected_area[i][1] + shifty
             
        if not ctrl_pressed:
            sarect = self._get_selected_area_rect()
            mpos = pygame.mouse.get_pos()
            if self._is_start_moving_selected_area():
               if not self.moving_selected_area:
                    self.start_selected_area = copy.deepcopy(self.selected_area)
                    self.moving_tiles = self._get_tiles_in_area(sarect)
                    self.start_mouse_position = (mpos[0] + self.camera[0], mpos[1] + self.camera[1])
               self.moving_selected_area = True

            if self.moving_selected_area:
                pass
            elif self.clicked[0] or (self.pressed[0] and self.shift):
                pos = pygame.mouse.get_pos()
                if self.grid: self._add_grid_tile(pos)
                else: self._add_nogrid_tile(pos)
            elif self.clicked[2] or (self.pressed[2] and self.shift):
                pos = pygame.mouse.get_pos()
                if self.grid: self._del_grid_tile(pos)
                else: self._del_nogrid_tile(pos)
        self.clicked = [False, False, False]

    def save(self):
        with open('map.json', 'w') as f:
            json.dump(
                {
                    'tile_map': {str(k): v for k, v in self.tile_map.items()},
                    'nogrid_tiles': self.nogrid_tiles,
                    'tile_size': self.tile_size,
                    'camera_x': self.camera[0],
                    'camera_y': self.camera[1],
                },
                f
            )

    def load(self):
        try:
            with open('map.json', 'r') as f:
                data = json.load(f)
                self.tile_map = {tuple(map(int, [x.replace('(', '').replace(')', '') for x in k.split(',')])): v for k, v in data['tile_map'].items()}
                self.nogrid_tiles = data['nogrid_tiles']
                self.tile_size = data['tile_size']
                self.camera = [data['camera_x'], data['camera_y']]
                self.k = self.tile_size // 16
                self._resize_resources()
        except FileNotFoundError:
            pass    

if __name__ == "__main__":
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.NOFRAME)
    clock = pygame.time.Clock()

    editor = Editor()

    ctrl_pressed = False
    shift_pressed = False
    alt_pressed = False
    z_pressed = False
    fill_activated = False

    def undo():
        while True:
            if editor.history_index == 0: return
            editor.history_index -= 1
            action = editor.history[editor.history_index]
            if action['action'] == 'add':
                if action['type'] == 'grid':
                    if action['pos'] in editor.tile_map:
                        del editor.tile_map[action['pos']]
                    else: continue
                else:
                    editor.nogrid_tiles.remove(action['tile'])
            elif action['action'] == 'del':
                if action['type'] == 'grid':
                    editor.tile_map[action['pos']] = action['tile']
                else:
                    editor.nogrid_tiles.append(action['tile'])
            elif action['action'] == 'add_filled':
                for i, j in action['pos']:
                    if (i, j) in editor.tile_map:
                        del editor.tile_map[(i, j)]
            elif action['action'] == 'move_selected_area':
                shiftx, shifty = action['pos']
                for pos, tile in action['tile']:
                    newx = pos[0] * editor.tile_size + shiftx
                    newy = pos[1] * editor.tile_size + shifty
                    x = newx // editor.tile_size
                    y = newy // editor.tile_size
                    if (x, y) in editor.tile_map:
                        del editor.tile_map[(x, y)]
                    editor.tile_map[pos] = tile
            break

    def redo():
        while True:
            if editor.history_index == len(editor.history): return
            action = editor.history[editor.history_index]
            editor.history_index += 1
            if action['action'] == 'add':
                if action['type'] == 'grid':
                    editor.tile_map[action['pos']] = action['tile']
                else:
                    editor.nogrid_tiles.append(action['tile'])
            elif action['action'] == 'del':
                if action['type'] == 'grid':
                    if action['pos'] in editor.tile_map:
                        del editor.tile_map[action['pos']]
                    else: continue
                else:
                    editor.nogrid_tiles.remove(action['tile'])
            elif action['action'] == 'add_filled':
                for i, j in action['pos']:
                    editor.tile_map[(i, j)] = action['tile']
            elif action['action'] == 'move_selected_area':
                shiftx, shifty = action['pos']
                for pos, tile in action['tile']:
                    newx = pos[0] * editor.tile_size + shiftx
                    newy = pos[1] * editor.tile_size + shifty
                    x = newx // editor.tile_size
                    y = newy // editor.tile_size
                    if pos in editor.tile_map:
                        del editor.tile_map[pos]
                    editor.tile_map[(x, y)] = tile
            break

    while True:
        clock.tick(60)
        screen.fill((0, 0, 0))
        editor.update()
        editor.render(screen)

        if z_pressed and ctrl_pressed and alt_pressed:
            if shift_pressed:
                redo()
            else:
                undo()

        if ctrl_pressed and editor.selected_area:
            mx, my = pygame.mouse.get_pos()
            mx += editor.camera[0]
            my+= editor.camera[1]
            editor.selected_area[-1] = [mx, my]

        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LSHIFT:
                    editor.shift = True
                    shift_pressed = True
                elif event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    exit()
                elif event.key == pygame.K_EQUALS:
                    editor.tile_size += 16
                    editor.camera[0] /= editor.k
                    editor.camera[1] /= editor.k
                    editor.k += 1
                    editor.camera[0] *= editor.k
                    editor.camera[1] *= editor.k
                    editor._resize_resources()
                elif event.key == pygame.K_MINUS:
                    if editor.tile_size > 16:
                        editor.tile_size -= 16
                        editor.camera[0] /= editor.k
                        editor.camera[1] /= editor.k
                        editor.k -= 1
                        editor.camera[0] *= editor.k
                        editor.camera[1] *= editor.k
                        editor._resize_resources()
                elif event.key == pygame.K_RIGHT:
                    editor.move[0] = 5
                elif event.key == pygame.K_LEFT:
                    editor.move[0] = -5
                elif event.key == pygame.K_DOWN:
                    editor.move[1] = 5
                elif event.key == pygame.K_UP:
                    editor.move[1] = -5
                if event.key == pygame.K_g:
                    editor.grid = not editor.grid
                elif (event.key == pygame.K_SPACE and ctrl_pressed) or event.key == pygame.K_b:
                    editor.current_variant -= 1
                    if editor.current_variant < 0:
                        editor.current_variant = len(editor.resources[editor.current_resource]) - 1
                elif event.key == pygame.K_SPACE:
                    editor.current_variant = (editor.current_variant + 1) % len(editor.resources[editor.current_resource])
                elif event.key == pygame.K_e:
                    editor.current_resource = editor.resource_names[(editor.resource_names.index(editor.current_resource) + 1) % len(editor.resource_names)]
                    editor.current_variant = 0
                elif event.key == pygame.K_q:
                    editor.current_resource = editor.resource_names[(editor.resource_names.index(editor.current_resource) - 1) % len(editor.resource_names)]
                    editor.current_variant = 0
                elif event.key == pygame.K_LCTRL:
                    ctrl_pressed = True
                elif event.key == pygame.K_z:
                    z_pressed = True
                    if shift_pressed:
                        redo()
                    else:
                        undo()
                elif event.key == pygame.K_s:
                    editor.save()
                elif event.key == pygame.K_t:
                    editor.transform()
                elif event.key == pygame.K_f:
                    fill_activated = not fill_activated
                elif event.key == pygame.K_LALT:
                    alt_pressed = True
                elif event.key == pygame.K_BACKSPACE and editor.selected_area:
                    editor._remove_tiles_in_selected_area()

            if event.type == pygame.KEYUP:
                if event.key == pygame.K_LSHIFT:
                    editor.shift = False
                    shift_pressed = False
                elif event.key == pygame.K_RIGHT:
                    editor.move[0] = 0
                elif event.key == pygame.K_LEFT:
                    editor.move[0] = 0
                elif event.key == pygame.K_DOWN:
                    editor.move[1] = 0
                elif event.key == pygame.K_UP:
                    editor.move[1] = 0
                elif event.key == pygame.K_LCTRL:
                    ctrl_pressed = False
                elif event.key == pygame.K_z:
                    z_pressed = False
                elif event.key == pygame.K_LALT:
                    alt_pressed = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    editor.clicked[0] = True
                    editor.pressed[0] = True
                    # selecting area
                    if ctrl_pressed:
                        mx, my = pygame.mouse.get_pos()
                        mx += editor.camera[0]
                        my+= editor.camera[1]
                        editor.selected_area = [[mx, my]] * 2
                    elif not editor._is_start_moving_selected_area():
                        if editor.selected_area:
                            editor.clicked[0] = False
                            editor.pressed[0] = False
                        editor.selected_area = []
                elif event.button == 3:
                    editor.clicked[2] = True
                    editor.pressed[2] = True
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    editor.pressed[0] = False
                    if editor.moving_selected_area:
                        editor._save_moved_tiles()
                    editor.moving_selected_area = False
                elif event.button == 3:
                    editor.pressed[2] = False

        pygame.display.flip()
