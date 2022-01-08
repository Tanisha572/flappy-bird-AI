import pygame
import neat
import time
import os
import random

pygame.font.init()

# Defining the display window
WIN_WIDTH, WIN_HEIGHT = 500, 800
win = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT))
pygame.display.set_caption("Flappy Bird")


# Getting and defining all surfaces (texts/images) as constants
BIRD_IMGS = [
    pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "bird1.png"))), 
    pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "bird2.png"))),
    pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "bird3.png")))
]
PIPE_IMG = pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "pipe.png")))
BASE_IMG = pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "base.png")))
BG_IMG = pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "bg.png")))
STAT_FONT = pygame.font.SysFont("comicsans", 50)

#frame rate for the game i.e. the #times the display will be refreshed in one second
FPS = 30


# Making classes to represent each entity and define their behaviour in the game
class Bird:
    IMGS = BIRD_IMGS
    MAX_ROTATION = 25       #range upto which the player can tilt the bird
    ROT_VEL = 20            #rotation allowed per frame/move
    ANIMATION_TIME = 5      #time for which each animation will hold i.e. the rate at which the bird all flap its wings


    def __init__(self, x, y):
        #starting coordinates for the bird
        self.x = x
        self.y = y
        #starting orientation of the bird
        self.tilt = 0               #the bird looks straight towards the right
        self.tick_count = 0         #tracks the no. of seconds elapsed since the last move. 
                                    #will be used for physics calc for the bird
        self.vel = 0                #bird is stationary
        self.height = self.y
        self.img_count = 0          #image currently being rendered
        self.img = self.IMGS[0]     

    def jump(self):
        self.vel = -10.5            #pygame takes the upper-left corner of the diaplay as (0,0)
                                    #going left increases x, while going down increases y
                                    #therefore, to go up, negative value is required
        
        self.tick_count = 0         #keeps track of when the last jump occured
        self.height = self.y        #height from which the jump was made


    #method to define the movement of the bird.
    #flappy bird only moves up and down
    def move(self):
        self.tick_count += 1        #tracks the no. of moves made since the last jump

        #formula defining the arc for the bird when it jumps
        #displacement disp is in pixels
        disp = self.vel*self.tick_count + 1.5*self.tick_count**2

        #setting a limit to the velocity when going downwards and upwards
        if disp > 16:
            disp = 16
        if disp < 0:
            disp -= 2

        self.y = self.y+disp

        if disp < 0 or self.y < self.height + 50:
            if self.tilt < self.MAX_ROTATION:
                self.tilt = self.MAX_ROTATION   #while the bird is going up, we don't want it to climb up 90 deg
        else:
            if self.tilt > -90:                 #but while going down, it may look like nose-diving
                self.tilt -= self.ROT_VEL

    def draw(self, win):
        self.img_count += 1

        #decides on which image to show based on the image_count 
        if self.img_count < self.ANIMATION_TIME:
            self.img = self.IMGS[0]       
        elif self.img_count < self.ANIMATION_TIME*2:
            self.img = self.IMGS[1]
        elif self.img_count < self.ANIMATION_TIME*3:
            self.img = self.IMGS[2]
        elif self.img_count < self.ANIMATION_TIME*4:
            self.img = self.IMGS[1]
        elif self.img_count < self.ANIMATION_TIME*4 + 1:
            self.img = self.IMGS[0]
            self.img_count = 0

        if self.tilt <= -80:
            self.img = self.IMGS[1]
            self.img_count = self.ANIMATION_TIME*2


        #to rotate the image around its center
        rotated_image = pygame.transform.rotate(self.img, self.tilt)
        new_rect = rotated_image.get_rect(center=self.img.get_rect(topleft=(self.x,self.y)).center)
        win.blit(rotated_image, new_rect.topleft)


    #function handling collisions with objects
    def get_mask(self):
        return pygame.mask.from_surface(self.img)

        

class Pipe:
    GAP = 200   #pixels in between two pipes
    VEL = 5

    def __init__(self, x):
        self.x = x
        self.height = 0
        

        self.top = 0
        self.bottom = 0
        self.PIPE_TOP = pygame.transform.flip(PIPE_IMG, False, True)
        self.PIPE_BOTTOM = PIPE_IMG

        self.passed = False
        self.set_height()

    #sets the height for the pipe
    def set_height(self):
        self.height = random.randrange(50,450)
        self.top = self.height-self.PIPE_TOP.get_height()   #to get the x-coordinate from the height, as per the pygame coordinate
        self.bottom =self.height + self.GAP

    #method to define the movement of the pipes accross the screen
    #the pipes move only from right to left so as to make an illusion of the bird moving forward
    def  move(self):
        self.x -= self.VEL

    def draw(self, win):
        win.blit(self.PIPE_TOP, (self.x, self.top))
        win.blit(self.PIPE_BOTTOM, (self.x, self.bottom))
    
    #masks, in pygame, are used to detect pixel perfect collision
    #masks basically monitors the position of the pixels against a transparent background
    #each object on screen will be enclosed in a square and mask on that square will distinguish the 
    #object pixels against the background pixels. 
    #Overlapping of masks of two different objects will indicate the collision of the objects, rather
    #than that of the squares. therefore, making the collision perfect in the user's prespective as well.

    def collide(self, bird):
        bird_mask = bird.get_mask()
        top_mask = pygame.mask.from_surface(self.PIPE_TOP)
        bottom_mask = pygame.mask.from_surface(self.PIPE_BOTTOM)

        #offset of the bird from the top pipe and bottom pipe
        top_offset = (self.x - bird.x, self.top - round(bird.y))
        bottom_offset = (self.x - bird.x, self.bottom - round(bird.y))

        #finding the point of overlap between bird mask and bottom mask using the bottom_offset
        b_point = bird_mask.overlap(bottom_mask, bottom_offset)
        #finding the point of overlap between bird mask and top mask using the top_offset
        t_point = bird_mask.overlap(top_mask, top_offset)

        #if no overlap, overlap() returns none
        if t_point or b_point :
            #some collision occured
            return True
        #no collision occured
        return False


class Base:
    VEL = 5     #defining same velocity as pipe so that they seem to move at the same pace
    WIDTH = BASE_IMG.get_width()
    IMG = BASE_IMG

    def __init__(self, y):
        self.y = y
        self.x1 = 0
        self.x2 = self.WIDTH

    def move(self):
        self.x1 -= self.VEL
        self.x2 -= self.VEL

        #cycling back the images as and when they go off window, giving an isllusion of endless base
        #moving to the left
        if self.x1 + self.WIDTH < 0:
            self.x1 = self.x2 + self.WIDTH

        if self.x2 + self.WIDTH < 0:
            self.x2 = self.x1 + self.WIDTH

    #menthod to draw the base onto the display window
    def draw(self, win):
        win.blit(self.IMG, (self.x1, self.y))
        win.blit(self.IMG, (self.x2, self.y))


# Function to redraw the window for every iteration of the game loop

#function to render the display window
def draw_window(win, bird, pipes, base, score):
    win.blit(BG_IMG, (0,0))     #blit() just renders the provided surface onto the display
    
    for pipe in pipes:
        pipe.draw(win)
    
    text = STAT_FONT.render("Score: " + str(score), 1, (255,255,255))
    win.blit(text, (WIN_WIDTH - 10 - text.get_width(), 10))

    base.draw(win)

    bird.draw(win)
    pygame.display.update()


def main():
    bird = Bird(230, 350)
    base = Base(730)
    pipes = [Pipe(700)]
    #use clock object to set the tick rate i.e no. of frames per sec
    #prevents the game from using the system's speed and use this measure of time instead
    clock = pygame.time.Clock()

    score = 0

    run = True
    #the game loop for the pygame
    while run:
        clock.tick(FPS)      
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
        
        # bird.move()
        add_pipe = False
        rem = []
        for pipe in pipes:
            if pipe.collide(bird):
                pass

            if pipe.x + pipe.PIPE_TOP.get_width() < 0:
                rem.append(pipe)

            if not pipe.passed and pipe.x < bird.x:
                pipe.passed = True
                add_pipe = True
            
            pipe.move()

        if add_pipe:
            score += 1
            pipes.append(Pipe(700))

        for r in rem:
            pipes.remove(r)

        # bird has hit ground
        if bird.y + bird.img.get_height() > 730:
            pass

        base.move()
        draw_window(win, bird, pipes, base, score)

    pygame.quit()
    quit()



if __name__ == "__main__":
    main()

