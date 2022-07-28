"""
Author    :    Shubhodeep Mitra
Describe  :    Buildind a AI based flappy bird bot that plays the flappy bird game
Reference :    Following Tech with Tim youtube channel to make this project

"""

import pygame
import neat
import time
import os
import random

pygame.font.init()

##Constants for the game
WIN_HEIGHT = 800
WIN_WIDTH  = 600

## Load the images
BIRD_IMGS = [pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "bird1.png"))), pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "bird2.png"))), pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "bird3.png")))]
BG_IMG    = pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "bg.png")))
PIPE_IMG  = pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "pipe.png")))
BASE_IMG  = pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "base.png")))

## Font for the score
STAT_FONT = pygame.font.SysFont("comicsans", 50)


class Bird:
    IMGS           = BIRD_IMGS
    # rotation is the angle the bird is going to make while moving upwards 
    # so that it looks like it is moving up, and similar downfacing logic for moving down
    MAX_ROTATION   = 25 
    ROT_VEL        = 20 # how much the bird image rotates in one frame
    ANIMATION_TIME = 5
    
    def __init__(self, x, y):
        """
        Initialize the object
        :param x: starting x pos (int)
        :param y: starting y pos (int)
        :return: None
        """
        self.x = x
        self.y = y
        self.tilt = 0  # degrees to tilt
        self.tick_count = 0 #counts the number of time bird moved since last jumps made: initializing it to be zero
        self.vel = 0
        self.height = self.y
        self.img_count = 0
        self.img = self.IMGS[0]

    def jump(self):
        """
        make the bird jump
        :return: None
        """
        self.vel = -10.5 #negative beacuse moving up the y-axis, +ve when moving down the y axis 
        self.tick_count = 0 
        self.height = self.y
    
    def move(self):
        self.tick_count += 1 #how many times the bird moved before a jump
        
        ## how many pixels we move, simalar to the physics equation s = ut +0.5 at2
        d = self.vel * self.tick_count + 1.5*self.tick_count**2       
        
        ## we don't want velocity to go way too up or way too down
        if d >= 16:
            d=16
        
        ##if it is going up then let it go slowly up
        if d < 0:
            d -= 2
        
        self.y += d 
        
        ## if we are moving upwards then tilt the bird upwards
        if d < 0 or (d < (self.height + 50)):
            if self.tilt < self.MAX_ROTATION:
                self.tilt = self.MAX_ROTATION
        ## else if we are moving down then tilt the birds downwrds
        else:
            if self.tilt > -90:
                self.tilt -= self.ROT_VEL
    
    def draw(self, win):
        self.img_count += 1
        
        if self.img_count < self.ANIMATION_TIME:
            self.img = self.IMGS[0]
        elif self.img_count < self.ANIMATION_TIME*2:
            self.img = self.IMGS[1]
        elif self.img_count < self.ANIMATION_TIME*3:
            self.img = self.IMGS[2]
        elif self.img_count < self.ANIMATION_TIME*4:
            self.img = self.IMGS[1]
        elif self.img_count < (self.ANIMATION_TIME*4 + 1):
            self.img = self.IMGS[0]
            self.img_count = 0
        
        if self.tilt <= -80:
            self.img = self.IMGS[1]
        
        """ 
            rotate the image aroung the center as per the tilt 
        """
        rotated_img = pygame.transform.rotate(self.img, self.tilt)
        ##following line is to tilt it around its center
        new_rect = rotated_img.get_rect(center = self.img.get_rect(topleft = (self.x, self.y)).center)
        
        """ Draw the image in the window
            blit: it draws whatever is passed as the first parameter, 
            on the position which is passed in the second parameter
        """
        win.blit(rotated_img, new_rect.topleft)
        
    """
        To tackle collisions
        NOTE:   Any image of an object we take is basically in the shape of a rectangle,
                which contains an object (here it's a bird), and surrounding is empty
                or blank space.
                What mask does is basically form a 2D array where the outline pixels
                of the objext will have certain values and the blank space around the
                object will have different values, hence we can check collision by
                comparing MASK values of two different objects
    """
    def get_mask(self):
        return pygame.mask.from_surface(self.img) 


class Pipe:
    ##GAP is the space between the top and bottom pipe
    GAP = 200
    VEL = 5 
    
    def __init__(self, x):
        self.x      = x
        self.height = 0
        
        self.top    = 0
        self.bottom = 0
        
        ## this will be inverted image of pipe that will be hanging from top
        self.PIPE_TOP    = pygame.transform.flip(PIPE_IMG, False, True)
        self.PIPE_BOTTOM = PIPE_IMG
        
        ## This variable says whether the bird has passed the pipe or collided
        self.passed = False
        self.set_height()
    
    def set_height(self):
        ## randmonly getting the height in the range
        self.height = random.randrange(50, 450)
        
        """
            So if the height of the image is more than ( self.height - top(y=0)),
            i.e the pipe image won't fit within the window,
            then we will start the image from negative top position
            i.e outside the top boundary
        """
        self.top = self.height - self.PIPE_TOP.get_height()
        ## the bottom image will start from the position of height with the gap added for the bird
        self.bottom = self.height + self.GAP
    
    """
        This function casues the pipe to move backwards,
        so to give illusion that the bird is moving forward
    """
    def move(self):
        self.x -= self.VEL
    
    def draw(self, win):
        ## draw the pipe position from x and top
        win.blit(self.PIPE_TOP,  (self.x, self.top))
        ## draw the pipe position from x and botttom
        win.blit(self.PIPE_BOTTOM, (self.x, self.bottom))
    
    """
        This function is responsible to find whether there is collision between
        the bird and the pipe
    """
    def collide(self, bird):
        bird_mask     = bird.get_mask()
        top_pipe_mask = pygame.mask.from_surface(self.PIPE_TOP)
        bottom_pipe_mask = pygame.mask.from_surface(self.PIPE_BOTTOM) 
        
        # distance between bird and top pipe
        top_offset = (self.x - bird.x, self.top - round(bird.y)) 
        # distance between bird and bottom pipe
        bottom_offset = (self.x - bird.x, self.bottom - round(bird.y))
        
        """
            Checks for overlap between the pipe and the bird, with 
            offset distance between them
            Returns: None if there is no collision
        """
        b_point = bird_mask.overlap(bottom_pipe_mask, bottom_offset)
        t_point = bird_mask.overlap(top_pipe_mask, top_offset)
        
        """
            if t_point or b_point are not None, i.e collision happens
            return True: if not None
            else False
        """
        if t_point or b_point:
            return True
        else:
            return False


"""
    Base image class
"""
class Base:
    VEL   = 5
    WIDTH = BASE_IMG.get_width()
    
    def __init__(self, y):
        self.y = y #start at height y
        """
            The base image must move towards left, so when the image goes left,
            it must stitch itself towards the right of the image end
            x1: position of the image1
            x2: posiiton of the image2
            Using two background image we are able to cycle around
        """
        self.x1 = 0
        self.x2 = self.WIDTH
    
    def move(self):
        self.x1 -= self.VEL
        self.x2 -= self.VEL
        
        if(self.x1 + self.WIDTH)< 0:
            self.x1 = self.x2 + self.WIDTH
        elif (self.x2 + self.WIDTH) < 0:
            self.x2 = self.x1 + self.WIDTH     
     
    def draw(self, win):
        ## drawing the first image
        win.blit(BASE_IMG, (self.x1, self.y))
        ## drawing the second image
        win.blit(BASE_IMG, (self.x2, self.y))
        
        

"""
    Draws the window on the screen
"""
def draw_window(win, bird, pipes, base, score):
    win.blit(BG_IMG, (0,0)) #drawing background at the topleft of the screen
        
    for pipe in pipes:
        pipe.draw(win)
    
    score_text = STAT_FONT.render("Score: " + str(score),1 , (255,255,255) )
    ## print on the top right corner of the screen
    win.blit(score_text, (WIN_WIDTH - 10 - score_text.get_width(), 10))
    
    base.draw(win)
    bird.draw(win)
     
    ##   the below method uodates the display and refreshes it
    pygame.display.update()
    

"""
    Runs the main loop of the game
"""
def main():
    bird  = Bird(200, 200) ##give a intitial starting position
    base  = Base(730)  ##value of y where the base imag will start
    pipes = [Pipe(600)]  ##value of starting  x co-ordinate
    
    win = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT))
    
    run      = True    
    ## score for the game
    score = 0
    
    while run:
        ## handle all type of event that can be caused by clicking of mouse/user input
        for event in pygame.event.get():
            ##if the user clicks the top red cross button then end the loop
            if event.type == pygame.constants.QUIT:
                run = False
        
        
        #rem_pipe = []
        add_pipe = False
        for pipe in pipes:
            if pipe.collide(bird):
                pass
            
            ## Check if the top pipe out of the screen (moved out of the left part of the screen)
            if pipe.x + pipe.PIPE_TOP.get_width() < 0:
                #rem_pipe.append(pipe)
                pipes.remove(pipe)
            
            ## Similarl check for the Bottom pipe for out of the screen is not needed since the pipe
            ## object holds both the top and bottom pipe image and shares the same 'x' co-ordinates
            ## hence if the top goes out the bottom also goes out since they are members of the same object
            
            """
                If the bird x co-ordinate is more than the pipe x co-ordinate 
                then the bird has passed the pipe
                and so if the is_passed is not True then update the variable
            """
            if not pipe.passed  and pipe.x < bird.x - bird.img.get_width(): ##leftmost part of the bird crosses the pipe
                pipe.passed = True
                add_pipe = True
            
            pipe.move()
            
        if add_pipe:
            score += 1
            pipes.append(Pipe(600))
        
        ##remove pipe in the rem list:
        """for r in rem_pipe:
            pipes.remove(r)"""
        
        
        ## Functionality to end game when bird hits the base
        if bird.y + bird.img.get_height() > 730: ##730 is the height of the base image
            pass
            
        base.move()
        draw_window(win, bird, pipes, base, score)
    
    """
        ERROR FIX:
        got the below solution from stackoverflow because of lint in VS
        https://stackoverflow.com/questions/53012461/imports-failing-in-vscode-for-pylint-when-importing-pygame
    """
    # pylint: disable=no-member
    pygame.quit()
    # pylint: enable=no-member
    quit() #quit program
    
main()

def run(config_path):
    pass

if __name__ == "__main__":
    local_dir = os.path.dirname(__file__)
    config_file = os.path.join(local_dir,"config-feedforward.txt")
    run(config_file)