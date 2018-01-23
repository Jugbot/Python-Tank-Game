import math
import random
import sys

import numpy
import pyglet
from pyglet.window import key
from pyqtree import Index

config = pyglet.gl.Config(sample_buffers=1, samples=4)
window = pyglet.window.Window(config=config, fullscreen=True)
batch = pyglet.graphics.Batch()
playingfield=(10, 10, window.width-20, window.height-20)
qtree = Index(bbox=playingfield)
fps = pyglet.clock.ClockDisplay()

@window.event
def on_draw():
    window.clear()
    batch.draw()
    fps.draw()

@window.event
def on_mouse_drag(x, y, dx, dy, buttons, modifiers):
    pyglet.graphics.draw(4, pyglet.gl.GL_QUADS, ('v2f', [x, y, x-dx, y, x-dx, y-dy, x, y-dy]))

class Level:

    def __init__(self):
        pass
    #subdivision method
    def generate_new(self,bbox,x,y): #bbox is the bounds of the draw
        cells = [[[False] * 2 for _ in range(y)] for _ in range(x)]
        for coord in self.recr_subdivide(0, x-1, 0, y-1, True):
            if coord[2]: #if Floor
                cells[coord[0]][coord[1]][0] = True #(Floor,Wall) of cell
            else:
                cells[coord[0]][coord[1]][1] = True
        '''
        for ydim in range(y):
            for xdim in range(x):
                try:
                    if cells[xdim][ydim][0]:
                        print('_', end='')
                    else:
                        print(' ', end='')
                    if cells[xdim][ydim][1]:
                        print('|', end='')
                    else:
                        print(' ', end='')
                except IndexError:
                    pass
            print()
        '''
        cellsize = min(bbox[3]/y, bbox[2]/x) #if y subdivisions dimension should be used to scale level (to fit bbox)
        wt = 7 #Wall Thickness
        offsetx = bbox[0] + (bbox[2] - x*cellsize)/2
        offsety = bbox[1] + (bbox[3] - y*cellsize)/2
        Wall(offsetx, offsety, cellsize*x+wt, wt)
        Wall(offsetx, offsety, wt, cellsize*y+wt)
        Wall(cellsize*x + offsetx, offsety, wt, cellsize*y+wt)
        Wall(offsetx, offsety + cellsize*y, cellsize*x+wt, wt)
        for wx in range(len(cells)):
            for wy in range(len(cells[0])):
                if cells[wx][wy][0]:
                    Wall(offsetx+wx*cellsize, offsety+(wy+1)*cellsize, cellsize + wt, wt)
                if cells[wx][wy][1]:
                    Wall(offsetx + (wx+1)*cellsize, offsety + wy*cellsize, wt, cellsize + wt)

    def recr_subdivide(self, x1, x2, y1, y2, is_floor):

        if x1 == x2 == y1 == y2:
            return

        if is_floor and y1 != y2: #True == widthwise
            ymid = random.randint(y1, y2-1) #ignore last wall
            yield from self.recr_subdivide(x1,x2,y1,ymid,False)
            yield from self.recr_subdivide(x1,x2,ymid+1,y2,False)

            hole = random.randint(x1, x2)
            for xstep in range(x1, x2+1):
                if xstep != hole:
                    yield (xstep, ymid, is_floor)

        elif not is_floor and x1 != x2:
            xmid = random.randint(x1, x2-1) #somehow gives x2??
            yield from self.recr_subdivide(xmid+1,x2,y1,y2,True)
            yield from self.recr_subdivide(x1,xmid,y1,y2,True)

            hole = random.randint(y1, y2)
            for ystep in range(y1, y2+1):
                if ystep != hole:
                    yield (xmid, ystep, is_floor)



'''
-----------------------------------------
Entities
-----------------------------------------
'''
class Entity(object):

    def __init__(self, x, y , w, h, rot = 0):
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.rot = rot

    def draw(self):
        pass

def minmax(mi, ma):
    return (mi, ma) if (ma - mi) > 0 else (ma, mi)

#https://www.gamedev.net/articles/programming/general-and-gameplay-programming/swept-aabb-collision-detection-and-response-r3084/
def sweptAABB(box1, box2, dt):
    xInvEntry = yInvEntry = xInvExit = yInvExit = None
    if box1.vx > 0:
        xInvEntry = box2.x - (box1.x + box1.size)
        xInvExit = (box2.x + box2.w) - box1.x
    else:
        xInvEntry = (box2.x + box2.w) - box1.x
        xInvExit = box2.x - (box1.x + box1.size)
    if box1.vy > 0:
        yInvEntry = box2.y - (box1.y + box1.size)
        yInvExit = (box2.y + box2.h) - box1.y
    else:
        yInvEntry = (box2.y + box2.h) - box1.y
        yInvExit = box2.y - (box1.y + box1.size)
    xEntry = xExit = yEntry = yExit = None
    if box1.vx == 0:
        xEntry = -sys.maxsize - 1
        xExit = sys.maxsize
    else:
        xEntry = xInvEntry / (box1.vx * dt) #divide pixel coordinates by velocity to get relative before-after distance?
        xExit = xInvExit / (box1.vx * dt)
    if box1.vy == 0:
        yEntry = -sys.maxsize - 1
        yExit = sys.maxsize
    else:
        yEntry = yInvEntry / (box1.vy * dt)
        yExit = yInvExit / (box1.vy * dt)

    entryTime = max(xEntry, yEntry)
    exitTime = min(xExit, yExit)
    if entryTime > exitTime or xEntry < 0 and yEntry < 0 or xEntry > 1 or yEntry > 1:
        # no collision
        return
    else:
        normal = None
        if xEntry > yEntry:
            if xInvEntry < 0.0:
                normal = (1, 0)
            else:
                normal = (-1, 0)
        else:
            if yInvEntry < 0.0:
                normal = (0, 1)
            else:
                normal = (0, -1)

        return entryTime, normal


class Projectile(Entity):

    def __init__(self, x, y, vx, vy, size=1):
        Entity.__init__(self, x-size/2, y-size/2, size, size)
        self.size = size
        self.vx = vx
        self.vy = vy
        self.bbox = (x, y, x+self.size, y+self.size)
        vrts = (x, y, x + self.size, y, x + self.size, y + self.size, x, y + self.size)
        self.vertex_list = batch.add(4, pyglet.gl.GL_QUADS, None, ('v2f', vrts))
        self.compromised = False

    def move(self, x, y):
        self.x = x
        self.y = y
        self.bbox = (self.x, self.y, self.x+self.size, self.y+self.size)
        vrts = (self.x, self.y, self.x + self.size, self.y, self.x + self.size, self.y + self.size, self.x, self.y + self.size)
        #easy translation func?
        self.vertex_list.vertices = vrts

    def out_of_bounds(self):
        return self.x > window.width or \
            self.y > window.height or \
            self.x + self.w < 0 or \
            self.y + self.h < 0

    def update(self, dt):
        #collision pre-check for a multiple collision update using simple "push" method
        #possibility for phasing through thin objects :(
        if self.out_of_bounds() and not self.compromised:
            print("uh-oh")
            self.compromised = True
            #self.vertex_list.delete()
            #somehow get it out of the list
        '''for hit in qtree.intersect(self.bbox):
            print("adjust")
            left = hit.x - self.x + self.w
            right = self.x - hit.x + hit.w
            up = hit.y - self.y + self.h
            down = self.y - hit.y + hit.h
            mi = min(left,right,up,down)
            if left == mi:
                self.move(self.x - left, self.y)
                self.vx *= -1.
            elif right == mi:
                self.move(self.x + right, self.y)
                self.vx *= -1.
            elif up == mi:
                self.move(self.x, self.y-up)
                self.vy *= -1.
            elif down == mi:
                self.move(self.x,self.y+down)
                self.vy *= -1.
        '''
        newx = self.x + self.vx * dt
        newy = self.y + self.vy * dt
        mmx = minmax(self.x, newx)
        mmy = minmax(self.y, newy)
        broadphase = ( mmx[0], mmy[0], mmx[1] + self.size, mmy[1] + self.size )
        possible_collision = qtree.intersect(broadphase)
        for other in possible_collision:
            if other in qtree.intersect(self.bbox):
                continue
            result = sweptAABB(self, other, dt) #(time, direction)
            if result is None: #no collision
                continue
            time, norm = result
            newx = self.x + dt * self.vx * time
            newy = self.y + dt * self.vy * time
            self.move(newx, newy)
            remainingtime = (1.0-time)
            if norm[0] != 0:
                self.vx *= -1.0
            else:
                self.vy *= -1.0
            self.update(remainingtime*dt)
            break
        else:
            self.move(newx, newy)


class Wall(Entity):

    def __init__(self, x, y, w, h, rot=0):
        Entity.__init__(self, x, y, w, h, rot)
        vrts = (x, y, x + w, y, x + w, y + h, x, y + h)
        bbox = (x, y, x + w, y + h)
        #ignore rot
        self.vertex_list = batch.add(4, pyglet.gl.GL_QUADS, None, ('v2f', vrts))
        qtree.insert(self, bbox)

PLAYER_SPIN_SPEED = 3
PLAYER_MAX_SPEED = 200
class Player(Entity, key.KeyStateHandler):
    WIDTH = 50
    HEIGHT = 70
    CANNON_LENGTH = 60
    def __init__(self, x ,y, rot, id): #positions center-based
        Entity.__init__(self,x-Player.WIDTH/2,y-Player.HEIGHT/2,Player.WIDTH,Player.HEIGHT)
        self.vx = self.vy = 0
        body = (x, y, x + self.w, y, x + self.w, y + self.h, x, y + self.h)
        cannon = (x,y,x,y+Player.CANNON_LENGTH)
        self.vertex_list = batch.add(4, pyglet.gl.GL_QUADS, None, ('v2f', body))
        self.vertex_list2 = batch.add(2, pyglet.gl.GL_LINES, None, ('v2f', cannon))

    def move(self, x, y, rot):
        self.x = x
        self.y = y

        rotMatrix = numpy.array([[math.cos(rot), -math.sin(rot)],
                                [math.sin(rot), math.cos(rot)]])
        hw = self.w/2
        hh = self.h/2
        coords = [[-hw, -hh],
             [hw, -hh],
             [hw, hh],
             [-hw, hh]]
        result = []
        for v in coords:
            result += (numpy.dot(rotMatrix, v) + [self.x, self.y]).tolist()

        self.vertex_list.vertices = result

        result2 = [self.x, self.y]
        result2 += (numpy.dot(rotMatrix, [0,Player.CANNON_LENGTH]) + [self.x, self.y]).tolist()
        self.vertex_list2.vertices = result2


    def update(self, dt):
        if self[key.LEFT] and not self[key.RIGHT]:
            self.rot += PLAYER_SPIN_SPEED * dt
        elif self[key.RIGHT] and not self[key.LEFT]:
            self.rot -= PLAYER_SPIN_SPEED * dt
        if self[key.SPACE]:
            projectiles.append(Projectile(self.x-math.sin(self.rot)*Player.CANNON_LENGTH,self.y+math.cos(self.rot)*Player.CANNON_LENGTH, -math.sin(self.rot)*PLAYER_MAX_SPEED, math.cos(self.rot)*PLAYER_MAX_SPEED, 4))
        if self[key.UP] and not self[key.DOWN]:
            self.vx = -math.sin(self.rot) * PLAYER_MAX_SPEED
            self.vy = math.cos(self.rot) * PLAYER_MAX_SPEED
        elif self[key.DOWN] and not self[key.UP]:
            self.vx = math.sin(self.rot) * PLAYER_MAX_SPEED
            self.vy = -math.cos(self.rot) * PLAYER_MAX_SPEED
        else:
            self.vx = self.vy = 0

        self.x += self.vx * dt
        self.y += self.vy * dt
        self.move(self.x, self.y, self.rot)


projectiles = []
player1 = Player(window.width/2, window.height/2, 0,0)
window.push_handlers(player1)
pyglet.gl.glLineWidth(10)
def global_update(dt):
    player1.update(dt)
    for p in projectiles:
        p.update(dt)
pyglet.clock.schedule_interval(global_update, 1/120.)

if __name__ == "__main__":
    level = Level()
    level.generate_new(playingfield,70,200)
    pyglet.app.run()

