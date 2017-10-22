#-------------------------------------------------------------------------------
# Name:        cyclic
# Purpose:     cyclic game using oop
#
# Author:      PandP
#
# Created:     14/04/2017
# Copyright:   (c) PandP 2017
# Licence:     <your licence>
#-------------------------------------------------------------------------------

import random, time, pygame, sys
import math
import os
import copy
from pygame.locals import *
from random import randint, sample, shuffle
import operator

FPS = 25

WINDOWWIDTH = 400
WINDOWHEIGHT = 600
BOXSIZE = 50
BOARDWIDTH = 5
BOARDHEIGHT = 5
BOARDCENTRE = (int(math.ceil(BOARDWIDTH/2.0) -1), int(math.ceil(BOARDHEIGHT/2.0) -1))
BLANK = {
        'blank': True,
        'seed_cycle': False,
        'quantity': False,
        'cycle': False,
        'block': 0
        }

LEFT = 1
RIGHT = 3

PIECERANGE = range(1,9)
RANDOMCOUNT_VAR = -1
COUNTDOWN_VAR = 3
RANDOM_PIECE_LENGTH_VAR = 6
FILLED_COUNT_AT_START = 5
cycles = {}
randomlist = []
SCORE_BASE = 2
MAXCYCLE = 10
FIBONACCI = [10, 20]
for n in range(1, 19):
    FIBONACCI.append(FIBONACCI[n] + FIBONACCI[n -1])

XMARGIN = (WINDOWWIDTH - (BOARDWIDTH * BOXSIZE))/2
RANDOM_COUNT_MARGIN = (WINDOWWIDTH - ((RANDOM_PIECE_LENGTH_VAR + RANDOM_PIECE_LENGTH_VAR - 1) * 12))/2
TOPMARGIN = 25

#               R    G    B
BLACK       = (  0,   0,   0)
DARKGREY    = (139, 139, 139)
LIGHTGREY   = (220, 220, 220)

TEXTCOLOR = DARKGREY

class Scene(object):
    def __init__(self):
        pass

    def render(self, screen):
        raise NotImplementedError

    def update(self):
        raise NotImplementedError

    def handle_events(self, events):
        raise NotImplementedError

class SceneMananger(object):
    def __init__(self):
        self.go_to(TitleScene())

    def go_to(self, scene):
        self.scene = scene
        self.scene.manager = self

class TitleScene(object):
    def __init__(self):
        super(TitleScene, self).__init__()
        #display title screen
        TITLERECT.topleft = 0,0
        DISPLAYSURF.blit(TITLE, TITLERECT)
        pygame.display.flip()

    def render(self, DISPLAYSURF):
        pass

    def update(self):
        pass

    def handle_events(self, events):
        for e in events:
            if e.type == KEYDOWN:
                self.manager.go_to(GameScene())

class GameScene(Scene):
    def __init__(self):
        super(GameScene, self).__init__()
        global randomlist
        global cycles

        cycles = {}

        #randomlist is a list of 4 time the piece range randomised, this prevents
        #strings random numbers which feel to unlikely, allows the player to
        #try and predict what is coming
        randomlist = random.sample(4 * PIECERANGE, len(4 * PIECERANGE))

        self.game_over = False
        self.possible_random_spaces= []
        self.random_pieces = []
        self.board = Board(self.possible_random_spaces)
        self.board_surface = pygame.Surface((WINDOWWIDTH, WINDOWHEIGHT), pygame.SRCALPHA)
        self.board_surface.blit(BGIMAGE, (XMARGIN, TOPMARGIN), (XMARGIN, TOPMARGIN, BOXSIZE * BOARDWIDTH, BOXSIZE * BOARDHEIGHT))
        self.board_rect = self.board_surface.get_rect()
        self.Overlay = Overlay(self.board_surface)
        self.countdown = COUNTDOWN_VAR
        self.false_random_count = 0
        self.update_countdown = False
        self.draw_current_piece = False
        self.random_count = -1
        self.getRandom(RANDOM_PIECE_LENGTH_VAR)
        if len(randomlist) < 3:
            randomlist = random.sample(4 * PIECERANGE, len(4 * PIECERANGE))
        self.currentPiece  = CurrentPiece(self.board_surface, self.board.board, randomlist.pop(0))
        self.nextPieceOne = {'quantity':(randomlist.pop()), 'cycle': 1}
        self.nextPieceTwo = {'quantity':(randomlist.pop()), 'cycle': 1}

        self.status = Status(self.board_surface, 0)
        DISPLAYSURF.blit(BGIMAGE, BGRECT)
        for x in range(BOARDWIDTH):
            for y in range(BOARDHEIGHT):
                self.drawBox(x, y, self.board.board[x][y])
        first = True
        for random_dict in self.random_pieces:
            self.drawRandomPiece(random_dict['coords'], random_dict['quantity'], random_dict['seed'])
        self.status.score_render()
        self.status.sets_render()
        self.drawCurrentPiece()
        self.drawRandomToPlace()
        DISPLAYSURF.blit(self.board_surface, self.board_rect)
        pygame.display.flip()

    def render(self, DISPLAYSURF):
        if self.Overlay.score_overlays != []:
            # update the score overlays, don't display those which have timed out
            DISPLAYSURF.blit(self.board_surface, self.board_rect)
            # check if should draw current piece
            if self.currentPiece.onboard == True and self.currentPiece.onblock == False:
                self.currentPiece.renderTile()
            self.Overlay.updateOverlay(1)
            self.Overlay.drawOverlays()
            pygame.display.flip()

    def update(self):
        pass

    def handle_events(self, events):

        global randomlist
        for event in events: # event handling loop
            if event.type == MOUSEMOTION:
                mouseX, mouseY = event.pos
                self.currentPiece.convertMouseToGrid(mouseX, mouseY)
                self.currentPiece.isValidPosition()
                self.checkCurrentPiece()
            elif event.type == pygame.MOUSEBUTTONUP and event.button == LEFT:
                if self.currentPiece.onboard == True and self.currentPiece.onblock == False:
                    self.addToBoard()
                    if self.game_over:
                        return
                    # check if full before doing any more work
                    if self.board.fullBoard():
                        self.manager.go_to(GameOverScene())
                        return
                    self.currentPiece.oldonblock = True
                    self.currentPiece.onblock =True
                    if self.countdown == 3:
                        if len(randomlist) <= 3:
                            randomlist.extend(random.sample(4 * PIECERANGE, len(4 * PIECERANGE)))
                        self.currentPiece.new_current_piece(randomlist.pop(), 1)
                        self.nextPieceOne = {'quantity':(randomlist.pop()), 'cycle': 1}
                        self.nextPieceTwo = {'quantity':(randomlist.pop()), 'cycle': 1}
                    elif self.countdown == 2:
                        self.currentPiece.new_current_piece(copy.copy(self.nextPieceOne['quantity']), copy.copy(self.nextPieceOne['cycle']))
                        self.nextPieceOne = copy.copy(self.nextPieceTwo)
                        self.nextPieceTwo = False
                    else:
                        self.currentPiece.new_current_piece(copy.copy(self.nextPieceOne['quantity']), copy.copy(self.nextPieceOne['cycle']))
                        self.nextPieceOne = False
                        self.nextPieceTwo = False
                    if self.countdown == 3:
                        self.drawCurrentPiece()
                        for random_dict in self.random_pieces:
                            if random_dict == False or random_dict == 'blocked':
                                continue
                            self.drawRandomPiece(random_dict['coords'], random_dict['quantity'], random_dict['seed'])
                        self.drawRandomToPlace()
                        self.status.sets_render()
                        DISPLAYSURF.blit(self.board_surface, self.board_rect)
                        pygame.display.flip()

    def addCycle(self, (x,y), cycles_to_add):
        global cycles

        block = self.board.board[x][y]['block']
        cycle = self.board.board[x][y]['cycle']
        while cycles_to_add > 0:
            if self.board.board[x][y]['block'] > 0:
                self.board.board[x][y]['block'] -= 1
                cycles_to_add -= 1
            elif self.board.board[x][y]['cycle'] == MAXCYCLE:
                cycles_to_add = 0
            else:
                self.board.board[x][y]['cycle'] += 1
                cycles_to_add -= 1

    def addToBoard(self):
        global cycles
        # fill in the board based on piece's location, quantity, and rotation
        self.added_pieces = []
        self.score_chain_bonus = 0
        self.countdown -= 1
        self.update_countdown = True
        x = self.currentPiece.x
        y = self.currentPiece.y
        self.to_investigate = [(x,y)]
        if self.board.board[x][y]['blank'] is True:
            if x == 0 or x == BOARDWIDTH - 1:
                if y == 0 or y == BOARDHEIGHT - 1:
                    tile_max = 3
                else:
                    tile_max = 5
            elif y == 0 or y == BOARDHEIGHT - 1:
                    tile_max = 5
            else:
                tile_max = 8 # or max(PIECERANGE)
            cycle = self.currentPiece.cycle
            cycles_to_add = 0
            if self.currentPiece.quantity > tile_max:
                new_quantity = self.currentPiece.quantity
                while new_quantity > tile_max:
                    new_quantity = new_quantity - tile_max
                    cycles_to_add += 1
                self.getAddedPieces(1, new_quantity, tile_max, cycle, cycles_to_add)
                #cycle += 1
            else:
                new_quantity = self.currentPiece.quantity
                self.getAddedPieces(1, new_quantity, tile_max, cycle, 0)
            self.board.board[x][y] = {
                'blank':False, 'seed_cycle':False,
                'quantity':new_quantity,
                'cycle':cycle, 'block': 0
            }
            self.appendCrossToInvestigate((x,y))
            for n in range(0, len(self.random_pieces)):
                random_piece = self.random_pieces[n]
                if random_piece is False or random_piece == 'blocked':
                    continue
                elif (x,y) == random_piece['coords']:
                    self.random_pieces[n] = 'blocked'
                    self.drawRandomToPlace()
        else:
            self.board.board[x][y]['block'] = 0
            quantity = self.board.board[x][y]['quantity']
            underneath_quantity = quantity
            cycle = self.board.board[x][y]['cycle']
            if x == 0 or x == BOARDWIDTH - 1:
                if y == 0 or y == BOARDHEIGHT - 1:
                    tile_max = 3
                else:
                    tile_max = 5
            elif y == 0 or y == BOARDHEIGHT - 1:
                    tile_max = 5
            else:
                tile_max = 8 # or max(PIECERANGE)
            cycles_to_add = 0
            new_quantity = quantity + self.currentPiece.quantity
            if new_quantity > tile_max:
                while new_quantity > tile_max:
                    cycles_to_add += 1
                    new_quantity -= tile_max
            """
            if self.currentPiece.quantity > tile_max:
                while self.currentPiece.quantity > tile_max:
                    cycles_to_add += 1
                    new_quantity = (quantity + self.currentPiece.quantity - tile_max) % tile_max
            else:
                new_quantity = (quantity + self.currentPiece.quantity) % tile_max
            """
            if cycles_to_add > 0:
                """
                if cycle + cycles_to_add >= MAXCYCLE:
                    cycle = MAXCYCLE
                """
                self.board.board[x][y]['quantity'] = new_quantity
                self.getAddedPieces(quantity, new_quantity, tile_max, cycle, cycles_to_add)
                self.addCycle((x,y), cycles_to_add)
            else:
                # it hasn't cycled just added onto
                self.board.board[x][y]['quantity'] = new_quantity
                self.getAddedPieces(quantity, new_quantity, tile_max, cycle, 0)
            """
            if new_quantity == 0:
                if quantity == tile_max:
                    # it has cycled to the max value for the tile
                    if cycle == MAXCYCLE:
                        self.board.board[x][y]['quantity'] = tile_max
                        self.getAddedPieces(quantity, quantity, tile_max, cycle, True, True)
                    else:
                        self.board.board[x][y]['quantity'] = tile_max
                        self.getAddedPieces(quantity, quantity, tile_max, cycle, True, False)
                        self.addCycle((x,y), cycles_to_add)
                else:
                    # it has added to the max value for the tile
                    self.board.board[x][y]['quantity'] = tile_max
                    self.getAddedPieces(quantity, tile_max, tile_max, cycle, False, False)
            elif new_quantity == quantity:
                # it has cycled around in a complete cycle and now has the same value
                if cycle == MAXCYCLE:
                    self.board.board[x][y]['quantity'] = new_quantity
                    self.getAddedPieces(quantity, quantity, tile_max, cycle, True, True)
                else:
                    self.board.board[x][y]['quantity'] = new_quantity
                    self.getAddedPieces(quantity, quantity, tile_max, cycle, True, False)
                    self.addCycle((x,y))
            elif new_quantity < quantity:
                # it has cycled around but not made it completely back to quantity
                if cycle == MAXCYCLE:
                    self.board.board[x][y]['quantity'] = new_quantity
                    self.getAddedPieces(quantity, new_quantity, tile_max, cycle, True, True)
                else:
                    self.board.board[x][y]['quantity'] = new_quantity
                    self.getAddedPieces(quantity, new_quantity, tile_max, cycle, True, False)
                    self.addCycle((x,y))
            else:
                # it hasn't cycled just added onto
                self.board.board[x][y]['quantity'] = new_quantity
                self.getAddedPieces(quantity, new_quantity, tile_max, cycle, False, False)
            """
        # update the currentpiece so it is clear
        self.clearCurrentPiece()
        # draw each dot which is added
        for n in range(0, len(self.added_pieces)):
            added_piece = self.added_pieces[n]
            x = self.currentPiece.x
            y = self.currentPiece.y
            quantity = added_piece['quantity']
            cycle = added_piece['cycle']
            pixelx, pixely = self.convertToPixelCoords(x, y)
            boxImage, boxRect = GETPIECEIMAGEVARIABLE['{}_{}'.format(quantity, cycle)]
            boxRect.topleft = pixelx, pixely
            if n == len(self.added_pieces) - 1:
                self.board_surface.blit(BGIMAGE, (pixelx, pixely), (pixelx, pixely, BOXSIZE, BOXSIZE))
                self.board_surface.blit(boxImage, boxRect)
                DISPLAYSURF.blit(self.board_surface, self.board_rect)
            else:
                DISPLAYSURF.blit(BGIMAGE, (pixelx, pixely), (pixelx, pixely, BOXSIZE, BOXSIZE))
                DISPLAYSURF.blit(boxImage, boxRect)
            self.Overlay.drawOverlays()
            pygame.display.flip()
            pygame.time.delay(250)
            # a quater of second turned into a quarter of my 20fps is 5
            self.Overlay.updateOverlay(5)
        self.checkRemove()
        if self.countdown != 0:
            if False in self.random_pieces:
                if self.board.board[x][y]['blank'] is True:
                    return
                #check surrounding tiles
                false_randoms_index = []
                current_random_coords = []
                for n in range(RANDOM_PIECE_LENGTH_VAR):
                    random_piece = self.random_pieces[n]
                    if random_piece is False:
                        false_randoms_index.append(n)
                    elif random_piece != 'blocked':
                        current_random_coords.append(random_piece['coords'])
                new_random = False
                for (c_x, c_y) in self.getAdjacentTiles((x,y)):
                    if self.board.board[c_x][c_y]['blank'] is False:
                        continue
                    if (c_x, c_y) in current_random_coords:
                        continue
                    index = false_randoms_index.pop(0)
                    new_random = True
                    if c_x == 0 or c_x == BOARDWIDTH - 1:
                        if c_y == 0 or c_y == BOARDHEIGHT - 1:
                            tile_max = 3
                        else:
                            tile_max = 5
                    elif c_y == 0 or c_y == BOARDHEIGHT - 1:
                            tile_max = 5
                    else:
                        tile_max = 8 # or max(PIECERANGE)
                    if len(randomlist) <= 4:
                        randomlist.extend(random.sample(4 * PIECERANGE, len(4 * PIECERANGE)))
                    quantity = randomlist.pop(0)
                    if quantity > tile_max:
                        while quantity > tile_max:
                            quantity = quantity - tile_max
                    self.random_pieces[index] = {
                                                'coords': (c_x, c_y),
                                                'quantity': quantity,
                                                'cycle':1,
                                                'block': 0,
                                                'seed': (x,y)
                                              }
                    self.drawRandomPiece((c_x, c_y), quantity, (x,y))
                    self.false_random_count -= 1
                    if len(false_randoms_index) == 0:
                        break
                if new_random:
                    DISPLAYSURF.blit(self.board_surface, self.board_rect)
                    self.Overlay.drawOverlays()
                    pygame.display.flip()
                    # don't worry about delay is now players turn to olace

        else:
            self.status.sets_completed += 1
            placing_randoms = True
            while placing_randoms is True:
                false_random = 0
                placed_seed_coords = []
                removed = False
                for n in range(0, RANDOM_PIECE_LENGTH_VAR):
                    random_piece = self.random_pieces[n]
                    if random_piece is False:
                        false_random +=1
                        continue
                    elif random_piece == 'blocked':
                        continue
                    (x,y) = random_piece['coords']
                    (s_x,s_y) = random_piece['seed']
                    quantity = random_piece['quantity']
                    cycle = random_piece['cycle']
                    block = random_piece['block']
                    self.board.board[x][y] = {
                        'blank':False, 'seed_cycle':False,
                        'quantity': quantity,
                        'cycle': cycle, 'block': block
                    }
                    if (x,y) not in self.to_investigate:
                        self.to_investigate.append((x,y))
                    self.appendCrossToInvestigate((x,y))
                    placed_seed_coords.extend([(x,y), (s_x,s_y)])
                    self.random_pieces[n] = 'blocked'
                if placed_seed_coords != []:
                    self.drawRandomToPlace()
                    self.draw_placed(placed_seed_coords)
                    self.Overlay.drawOverlays()
                    pygame.display.flip()
                    pygame.time.delay(500)
                    self.Overlay.updateOverlay(10)
                removed = self.checkRemove()
                if removed is False and placed_seed_coords == []:
                    placing_randoms = False
            for random_piece in self.random_pieces:
                if random_piece is False:
                    self.game_over = True
                    self.manager.go_to(GameOverScene())
                    return
            self.countdown = COUNTDOWN_VAR
            #create new randoms
            cycles = {}
            for x in range(0,BOARDWIDTH):
                for y in range(0,BOARDHEIGHT):
                    if self.board.board[x][y]['blank'] is True:
                        self.board.getHighestCycle((x,y))
            self.getRandom(RANDOM_PIECE_LENGTH_VAR)

    def appendCrossToInvestigate(self, (x,y)):
        for xn in (x-1, x, x+1):
            if xn  not in range(0,BOARDWIDTH):
                continue
            for yn in (y-1, y, y+1):
                if yn  not in range(0,BOARDHEIGHT):
                    continue
                if (xn, yn) == (x,y):
                    continue
                elif self.board.board[xn][yn]['blank'] is False:
                    if self.board.board[xn][yn]['block'] == 0:
                        if (xn, yn) not in self.to_investigate:
                            self.to_investigate.append((xn,yn))
        """
        if x-1 in range(0,BOARDWIDTH):
            if self.board.board[x-1][y]['blank'] is False:
                if self.board.board[x-1][y]['block'] == 0:
                    if (x-1, y) not in self.to_investigate:
                        self.to_investigate.append((x-1,y))
        if x+1 in range(0,BOARDWIDTH):
            if self.board.board[x+1][y]['blank'] is False:
                if self.board.board[x+1][y]['block'] == 0:
                    if (x+1, y) not in self.to_investigate:
                        self.to_investigate.append((x+1,y))
        if y-1 in range(0,BOARDHEIGHT):
            if self.board.board[x][y-1]['blank'] is False:
                if self.board.board[x][y-1]['block'] == 0:
                    if (x, y-1) not in self.to_investigate:
                        self.to_investigate.append((x,y-1))
        if y+1 in range(0,BOARDHEIGHT):
            if self.board.board[x][y+1]['blank'] is False:
                if self.board.board[x][y+1]['block'] == 0:
                    if (x, y+1) not in self.to_investigate:
                        self.to_investigate.append((x,y+1))
        """
        return

    def checkCross(self, (x,y)):
        if self.board.board[x][y]['block'] > 0:
            return False
        count = 0
        quantity = self.board.board[x][y]['quantity']
        for xn in (x-1, x, x+1):
            if xn  not in range(0,BOARDWIDTH):
                continue
            for yn in (y-1, y, y+1):
                if yn not in range(0,BOARDHEIGHT):
                    continue
                if (xn, yn) == (x,y):
                    continue
                elif self.board.board[xn][yn]['blank'] is False:
                    count += 1
        """
        if x-1 in range(0,BOARDWIDTH):
            if self.board.board[x-1][y]['blank'] is False:
                count += 1
        if x+1 in range(0,BOARDWIDTH):
            if self.board.board[x+1][y]['blank'] is False:
                count += 1
        if y-1 in range(0,BOARDHEIGHT):
            if self.board.board[x][y-1]['blank'] is False:
                count += 1
        if y+1 in range(0,BOARDHEIGHT):
            if self.board.board[x][y+1]['blank'] is False:
                count += 1
        """
        if count == quantity:
            return True
        else:
            return False

    def checkCurrentPiece(self):
        if self.currentPiece.oldgrid != (self.currentPiece.x, self.currentPiece.y):
            flipdisplay = False
            if self.currentPiece.x in range(0,BOARDWIDTH) and self.currentPiece.y in range(0,BOARDHEIGHT) and self.currentPiece.onblock == False:
                # draw the new position of the current piece
                pixelx = (XMARGIN + (self.currentPiece.x * BOXSIZE))
                pixely = (TOPMARGIN + (self.currentPiece.y * BOXSIZE))
                DISPLAYSURF.blit(self.board_surface, (pixelx, pixely), (pixelx, pixely, BOXSIZE, BOXSIZE))
                quantity = self.currentPiece.getQuantity(self.currentPiece.quantity, self.board.board[self.currentPiece.x][self.currentPiece.y]['quantity'], self.currentPiece.x, self.currentPiece.y)
                boxImage, boxRect = GETCURRENTPIECEIMAGEVARIABLE['{}'.format(quantity)]
                boxRect.topleft = pixelx, pixely
                DISPLAYSURF.blit(boxImage, boxRect)
                flipdisplay = True
            if self.currentPiece.oldgrid[0] in range(0,BOARDWIDTH) and self.currentPiece.oldgrid[1] in range(0,BOARDHEIGHT) and self.currentPiece.oldonblock == False:
                pixelx, pixely = self.convertToPixelCoords(self.currentPiece.oldgrid[0], self.currentPiece.oldgrid[1])
                DISPLAYSURF.blit(self.board_surface, (pixelx, pixely), (pixelx, pixely, BOXSIZE, BOXSIZE))
                flipdisplay = True
            self.currentPiece.oldgrid = (self.currentPiece.x, self.currentPiece.y)
            if flipdisplay:
                pygame.display.flip()


    def checkRemove(self):

        checking = True
        removed = False
        max_removed = []
        while checking is True:
            to_remove = []
            for (x,y) in self.to_investigate:
                check = self.checkCross((x,y))
                if check:
                    to_remove.append((x,y))
            if max_removed != []:
                 for x in range(0,BOARDWIDTH):
                    for y in range(0,BOARDHEIGHT):
                        if self.board.board[x][y]['quantity'] in max_removed:
                            if (x,y) not in to_remove:
                                to_remove.append((x,y))
            if to_remove == []:
                checking = False
            else:
                removed = True
                max_removed = []
                blocked = False
                for n in range (0, RANDOM_PIECE_LENGTH_VAR):
                    random_piece = self.random_pieces[n]
                    if random_piece is False or random_piece == 'blocked':
                        continue
                    else:
                        for (x,y) in to_remove:
                            if (x,y) == random_piece['seed']:
                                blocked = True
                                (ran_x,ran_y) = random_piece['coords']
                                pixelx, pixely = self.convertToPixelCoords(ran_x,ran_y)
                                self.board_surface.blit(BGIMAGE, (pixelx, pixely), (pixelx, pixely, BOXSIZE, BOXSIZE))
                                self.drawBox(ran_x, ran_y, self.board.board[ran_x][ran_y])
                                self.random_pieces[n] = 'blocked'
                for (x,y) in to_remove:
                    # for all the pieces around it add 1 to cycles
                    for xn in (x-1, x, x+1):
                        if xn  not in range(0,BOARDWIDTH):
                            continue
                        for yn in (y-1, y, y+1):
                            if yn not in range(0,BOARDHEIGHT):
                                continue
                            if (xn, yn) == (x,y):
                                continue
                            elif self.board.board[xn][yn]['blank'] is False:
                                self.addCycle((xn, yn), 1)
                                if (xn,yn) not in to_remove:
                                    pixelx, pixely = self.convertToPixelCoords(xn, yn)
                                    self.board_surface.blit(BGIMAGE, (pixelx, pixely), (pixelx, pixely, BOXSIZE, BOXSIZE))
                                    self.drawBox(xn , yn, self.board.board[xn][yn])
                    """
                    if x-1 in range(0,BOARDWIDTH):
                        if self.board.board[x-1][y]['blank'] is False:
                            self.addCycle((x-1, y))
                            if (x-1,y) not in to_remove:
                                pixelx, pixely = self.convertToPixelCoords(x-1, y)
                                self.board_surface.blit(BGIMAGE, (pixelx, pixely), (pixelx, pixely, BOXSIZE, BOXSIZE))
                                self.drawBox(x-1 , y, self.board.board[x-1][y])
                    if x+1 in range(0,BOARDWIDTH):
                        if self.board.board[x+1][y]['blank'] is False:
                            self.addCycle((x+1, y))
                            if (x+1,y) not in to_remove:
                                pixelx, pixely = self.convertToPixelCoords(x+1, y)
                                self.board_surface.blit(BGIMAGE, (pixelx, pixely), (pixelx, pixely, BOXSIZE, BOXSIZE))
                                self.drawBox(x+1 , y, self.board.board[x+1][y])
                    if y-1 in range(0,BOARDHEIGHT):
                        if self.board.board[x][y-1]['blank'] is False:
                            self.addCycle((x, y-1))
                            if (x,y-1) not in to_remove:
                                pixelx, pixely = self.convertToPixelCoords(x, y-1)
                                self.board_surface.blit(BGIMAGE, (pixelx, pixely), (pixelx, pixely, BOXSIZE, BOXSIZE))
                                self.drawBox(x, y-1, self.board.board[x][y-1])
                    if y+1 in range(0,BOARDHEIGHT):
                        if self.board.board[x][y+1]['blank'] is False:
                            self.addCycle((x, y+1))
                            if (x,y+1) not in to_remove:
                                pixelx, pixely = self.convertToPixelCoords(x, y+1)
                                self.board_surface.blit(BGIMAGE, (pixelx, pixely), (pixelx, pixely, BOXSIZE, BOXSIZE))
                                self.drawBox(x, y+1, self.board.board[x][y+1])
                    """
                self.to_investigate = []
                for (x,y) in to_remove:
                    cycle = self.board.board[x][y]['cycle']
                    quantity = self.board.board[x][y]['quantity']
                    if cycle == MAXCYCLE:
                        if cycle not in max_removed:
                            max_removed.append(quantity)
                    self.board.board[x][y] = BLANK
                    score_increase = (self.score_chain_bonus + cycle) * 10
                    self.status.score += score_increase
                    pixelx, pixely = self.convertToPixelCoords(x, y)
                    exponent_score_surf = COUNTFONT.render('{}'.format(str((score_increase))), True, TEXTCOLOR)
                    exponent_score_rect = exponent_score_surf.get_rect()
                    exponent_score_rect.center = (pixelx+(BOXSIZE/2), pixely+(BOXSIZE/2))
                    min_x = exponent_score_rect.left
                    min_y = exponent_score_rect.top
                    width  = exponent_score_rect.width
                    height = exponent_score_rect.height
                    self.Overlay.score_overlays.append({
                        'countdown':1 * FPS, 'rectangle':exponent_score_rect,
                        'surface': exponent_score_surf})
                    self.board_surface.blit(BGIMAGE, (pixelx, pixely), (pixelx, pixely, BOXSIZE, BOXSIZE))
                    self.drawBox(x, y, self.board.board[x][y])
                self.score_chain_bonus += 1
                for (x,y) in to_remove:
                    self.appendCrossToInvestigate((x,y))
                if blocked is True:
                    self.drawRandomToPlace()
                self.status.score_render()
                DISPLAYSURF.blit(self.board_surface, self.board_rect)
                self.Overlay.drawOverlays()
                pygame.display.flip()
                pygame.time.delay(500)
                self.Overlay.updateOverlay(10)
                if self.false_random_count > 0:
                    new_randoms = self.updateFalseRandoms(to_remove)
                    if new_randoms != []:
                        self.drawRandomToPlace()
                    DISPLAYSURF.blit(self.board_surface, self.board_rect)
                    self.Overlay.drawOverlays()
                    pygame.display.flip()
                    pygame.time.delay(500)
                    self.Overlay.updateOverlay(10)
        return removed


    def clearCurrentPiece(self):
        if self.countdown == 2:
            #clear first
            self.board_surface.blit(BGIMAGE, (100, 391), (100, 391, BOXSIZE, BOXSIZE))
        elif self.countdown == 1:
            # clear second
            self.board_surface.blit(BGIMAGE, (175, 391), (175, 391, BOXSIZE, BOXSIZE))
        elif self.countdown == 0:
            # clear last piece
            self.board_surface.blit(BGIMAGE, (250, 391), (250, 391, BOXSIZE, BOXSIZE))


    def convertToPixelCoords(self, boxx, boxy):
        # Convert the given xy coordinates of the board to xy
        # coordinates of the location on the screen.
        return (XMARGIN + (boxx * BOXSIZE)), (TOPMARGIN + (boxy * BOXSIZE))


    def drawCurrentPiece(self):
        # draw the "next" piece
        self.board_surface.blit(BGIMAGE, (100, 391), (100, 391, BOXSIZE, BOXSIZE))
        boxImage, boxRect = GETPIECEIMAGEVARIABLE['{}_{}'.format(self.currentPiece.quantity, self.currentPiece.cycle)]
        boxRect.topleft = 100, 391
        self.board_surface.blit(boxImage, boxRect)

        self.board_surface.blit(BGIMAGE, (175, 391), (175, 391, BOXSIZE, BOXSIZE))
        boxImage, boxRect = GETPIECEIMAGEVARIABLE['{}_{}'.format(self.nextPieceOne['quantity'], self.nextPieceOne['cycle'])]
        boxRect.topleft = 175, 391
        self.board_surface.blit(boxImage, boxRect)

        self.board_surface.blit(BGIMAGE, (250, 391), (250, 391, BOXSIZE, BOXSIZE))
        boxImage, boxRect = GETPIECEIMAGEVARIABLE['{}_{}'.format(self.nextPieceTwo['quantity'], self.nextPieceTwo['cycle'])]
        boxRect.topleft = 250, 391
        self.board_surface.blit(boxImage, boxRect)

    def drawBox(self, boxx, boxy, values):
        # draw a single box
        # at xy coordinates on the board.

        pixelx, pixely = self.convertToPixelCoords(boxx, boxy)

        if values['blank'] is True:
            boxImage = BLANKIMAGE
            boxRect = BLANKRECT
        else:
            boxImage, boxRect = GETPIECEIMAGEVARIABLE['{}_{}'.format(values['quantity'], values['cycle'])]
        boxRect.topleft = pixelx, pixely
        self.board_surface.blit(boxImage, boxRect)
        if values['block'] > 0:
            blockImage, blockRect = GETBLOCKIMAGEVARIABLE['{}'.format(values['block'])]
            blockRect.topleft = pixelx, pixely
            self.board_surface.blit(blockImage, blockRect)

    def draw_placed(self, placed_coords):
        for (x,y) in placed_coords:
            pixelx, pixely = self.convertToPixelCoords(x, y)
            self.board_surface.blit(BGIMAGE, (pixelx, pixely), (pixelx, pixely, BOXSIZE, BOXSIZE))
            self.drawBox(x, y, self.board.board[x][y])
        DISPLAYSURF.blit(self.board_surface, self.board_rect)


    def drawRandomPiece(self, (x,y), quantity, seed):
        pixelx, pixely = self.convertToPixelCoords(x, y)
        boxImage, boxRect = GETRANDOMPIECEIMAGEVARIABLE['{}'.format(quantity)]
        boxRect.topleft = pixelx, pixely
        self.board_surface.blit(boxImage, boxRect)
        if seed == False:
            RANDOMBLOCKRECT.topleft = pixelx, pixely
            self.board_surface.blit(RANDOMBLOCKIMAGE, RANDOMBLOCKRECT)
        if seed == (x-1,y):
            # w
            RANDOMBLOCKWRECT.topleft = pixelx, pixely
            self.board_surface.blit(RANDOMBLOCKWIMAGE, RANDOMBLOCKWRECT)
        elif seed == (x+1,y):
            # E
            RANDOMBLOCKERECT.topleft = pixelx, pixely
            self.board_surface.blit(RANDOMBLOCKEIMAGE, RANDOMBLOCKERECT)
        elif seed == (x,y-1):
            # N
            RANDOMBLOCKNRECT.topleft = pixelx, pixely
            self.board_surface.blit(RANDOMBLOCKNIMAGE, RANDOMBLOCKNRECT)
        elif seed == (x,y+1):
            # S
            RANDOMBLOCKSRECT.topleft = pixelx, pixely
            self.board_surface.blit(RANDOMBLOCKSIMAGE, RANDOMBLOCKSRECT)

    def drawRandomToPlace(self):

        random_count = copy.copy(RANDOM_PIECE_LENGTH_VAR)
        blocked_count = 0
        false_count = 0
        for n in range(0, RANDOM_PIECE_LENGTH_VAR):
            if self.random_pieces[n] == 'blocked':
                random_count -= 1
                blocked_count += 1
            elif self.random_pieces[n] is False:
                random_count -= 1
                false_count += 1

        for n in range(false_count):
            from_x_margin = RANDOM_COUNT_MARGIN + (n * 24)
            self.board_surface.blit(BGIMAGE, (from_x_margin, 507), (from_x_margin, 507, 12, 12))
            TOPLACERECT.topleft = from_x_margin, 507
            self.board_surface.blit(TOPLACEIMAGE, TOPLACERECT)
        for n in range(random_count):
            from_x_margin = RANDOM_COUNT_MARGIN + ((n + false_count) * 24)
            self.board_surface.blit(BGIMAGE, (from_x_margin, 507), (from_x_margin, 507, 12, 12))
            TOPLACERANDOMRECT.topleft = from_x_margin, 507
            self.board_surface.blit(TOPLACERANDOMIMAGE, TOPLACERANDOMRECT)
        for n in range(blocked_count):
            from_x_margin = RANDOM_COUNT_MARGIN + ((n + false_count + random_count) * 24)
            self.board_surface.blit(BGIMAGE, (from_x_margin, 507), (from_x_margin, 507, 12, 12))
            continue
            TOPLACEBLOCKEDRECT.topleft = from_x_margin, 507
            self.board_surface.blit(TOPLACEBLOCKEDIMAGE, TOPLACEBLOCKEDRECT)

    def getAddedPieces(self, quantity, new_quantity, tile_max, cycle, cycled):
        if cycled == 1:
            for n in range(quantity, tile_max + 1):
                self.added_pieces.append({'quantity':n, 'cycle':cycle})
            if cycle < MAXCYCLE:
                cycle += 1
            for n in range(1, new_quantity + 1):
                self.added_pieces.append({'quantity':n, 'cycle':cycle})
        elif cycled == 2:
            for n in range(quantity, tile_max + 1):
                self.added_pieces.append({'quantity':n, 'cycle':cycle})
            if cycle <MAXCYCLE:
                cycle += 1
            for n in range(1, tile_max + 1):
                self.added_pieces.append({'quantity':n, 'cycle':cycle})
            if cycle < MAXCYCLE:
                cycle += 1
            for n in range(1, new_quantity + 1):
                self.added_pieces.append({'quantity':n, 'cycle':cycle})
        else:
            for n in range(quantity, new_quantity + 1):
                self.added_pieces.append({'quantity':n, 'cycle':cycle})
    """
    def getAddedPieces(self, quantity, new_quantity, tile_max, cycle, cycled, max_var):
        if cycled:
            for n in range(quantity, tile_max + 1):
                self.added_pieces.append({'quantity':n, 'cycle':cycle})
            if max_var is False:
                cycle += 1
            for n in range(1, new_quantity + 1):
                self.added_pieces.append({'quantity':n, 'cycle':cycle})
        else:
            for n in range(quantity, new_quantity + 1):
                self.added_pieces.append({'quantity':n, 'cycle':cycle})
    """


    def getAdjacentTiles(self, (x,y)):
        """
        Returns coords of tiles adjacent which are on the board
        """
        adjacent_tiles = []
        if x-1 in range(0,BOARDWIDTH):
            adjacent_tiles.append((x-1, y))
        if x+1 in range(0,BOARDWIDTH):
            adjacent_tiles.append((x+1, y))
        if y-1 in range(0,BOARDHEIGHT):
            adjacent_tiles.append((x,y-1))
        if y+1 in range(0,BOARDHEIGHT):
            adjacent_tiles.append((x,y+1))
        return adjacent_tiles


    def getRandom(self, randomlength):
        global cycles
        global randomlist
        self.false_random_count = 0

        self.random_pieces = []

        self.draw_random_position = True
        if cycles == {}:
            if self.board.board[0][0]['blank'] is True:
                self.board.createBoard()

        if len(randomlist) < randomlength:
            sets_needed = int(math.ceil(randomlength / 4.0))
            if sets_needed < 4:
                sets_needed = 4
            randomlist.extend(random.sample(sets_needed * PIECERANGE, len(sets_needed * PIECERANGE)))
        # get a list of new random coordinates, add one for piece if player places
        # on a random piece
        cycles_keys = cycles.keys()
        cycles_keys.sort(reverse = True)
        if cycles_keys == []:
            # if there are no pieces on the board
            if (self.random_pieces == []
                    and self.board.board[1][1]['blank'] is True):
                # if no cycles found, there are no current random pieces and the board
                # is blank, i.e.: don't overwrite randompieces if the board isn't blank
                self.random_pieces = [{'coords': BOARDCENTRE, 'quantity': randomlist.pop(0), 'cycle':1, 'block': 0, 'seed':False}]
                for n in range(0, randomlength - 1):
                    self.random_pieces.insert(0, False)
                    self.false_random_count += 1
            else:
                # there is pieces in the randomlist but no more random options to add
                for n in range(0, randomlength):
                    self.random_pieces.insert(0, False)
                    self.false_random_count += 1
            return

        current_random_coords = []
        for random_piece in self.random_pieces:
            current_random_coords.append(random_piece['coords'])

        length_required = randomlength
        key = 0
        while length_required > 0:
            cycles_list = cycles[cycles_keys[key]]
            length_cycles_list = len(cycles_list)
            for n in range(0, length_cycles_list):
                # check not in random_pieces
                coord = cycles_list[n][0]
                if coord in current_random_coords:
                    continue
                seed = cycles_list[n][1]
                (x, y) = coord
                if x == 0 or x == BOARDWIDTH - 1:
                    if y == 0 or y == BOARDHEIGHT - 1:
                        tile_max = 3
                    else:
                        tile_max = 5
                elif y == 0 or y == BOARDHEIGHT - 1:
                        tile_max = 5
                else:
                    tile_max = 8 # or max(PIECERANGE)
                quantity = randomlist.pop(0)
                if quantity > tile_max:
                    while quantity > tile_max:
                        quantity = quantity - tile_max
                self.random_pieces.insert(0, {
                                            'coords': coord,
                                            'quantity': quantity,
                                            'cycle':1,
                                            'block': 0,
                                            'seed': seed
                                          })
                length_required -= 1
                if length_required == 0:
                    break
            key += 1
            if key >= len(cycles_keys):
                for n in range(0, length_required):
                    self.random_pieces.insert(0, False)
                    self.false_random_count += 1
                    length_required -= 1
                    if length_required == 0:
                        break

    def updateFalseRandoms(self, to_remove):
        global cycles
        global randomlist

        new_randoms = []

        cycles = {}

        for x in range(0,BOARDWIDTH):
            for y in range(0,BOARDHEIGHT):
                if self.board.board[x][y]['blank'] is True:
                    self.board.getHighestCycle((x,y))

        false_randoms_index = []
        current_random_coords = []
        for n in range(0, RANDOM_PIECE_LENGTH_VAR):
            random_piece = self.random_pieces[n]
            if random_piece is False:
                false_randoms_index.append(n)
            elif random_piece != 'blocked':
                current_random_coords.append(random_piece['coords'])

        if len(randomlist) < self.false_random_count:
            sets_needed = int(math.ceil(self.false_random_count / 4.0))
            if sets_needed < 4:
                sets_needed = 4
            randomlist.extend(random.sample(sets_needed * PIECERANGE, len(sets_needed * PIECERANGE)))
        cycles_keys = cycles.keys()
        cycles_keys.sort(reverse = True)
        key = 0
        updating_false_randoms = True
        # will break if not enough to fill random_pieces
        while updating_false_randoms is True:
            cycles_list = cycles[cycles_keys[key]]
            length_cycles_list = len(cycles_list)
            for n in range(0, length_cycles_list):
                (x,y) = cycles_list[n][0]
                # check not already in random_pieces
                if (x,y) in current_random_coords:
                    continue
                seed = cycles_list[n][1]
                if x == 0 or x == BOARDWIDTH - 1:
                    if y == 0 or y == BOARDHEIGHT - 1:
                        tile_max = 3
                    else:
                        tile_max = 5
                elif y == 0 or y == BOARDHEIGHT - 1:
                        tile_max = 5
                else:
                    tile_max = 8 # or max(PIECERANGE)
                quantity = randomlist.pop(0)
                if quantity > tile_max:
                    while quantity > tile_max:
                        quantity = quantity - tile_max
                index = false_randoms_index.pop(0)
                self.random_pieces[index] = {
                                            'coords': (x,y),
                                            'quantity': quantity,
                                            'cycle':1,
                                            'block': 0,
                                            'seed': seed
                                          }
                new_randoms.append({'coords':(x,y), 'quantity':quantity, 'seed':seed})
                self.drawRandomPiece((x,y), quantity, seed)
                self.appendCrossToInvestigate((x,y))
                self.false_random_count -= 1
                if self.false_random_count == 0:
                    updating_false_randoms = False
                    break
            key += 1
            if key >= len(cycles_keys):
                updating_false_randoms = False
                break

        return new_randoms


class GameOverScene(object):
    def __init__(self):
        super(GameOverScene, self).__init__()
        #display game over text
        s = pygame.Surface((WINDOWWIDTH, WINDOWHEIGHT))
        s.set_alpha(128)               # alpha level 128
        s.fill(BLACK)           # this fills the entire surface
        DISPLAYSURF.blit(s, (0,0))    # (0,0) are the top-left coordinates

        # Draw the text
        titleSurf, titleRect = makeTextObjs("Game over", BIGFONT, LIGHTGREY)
        titleRect.center = (int(WINDOWWIDTH / 2) - 3, int(WINDOWHEIGHT / 2) - 3)
        DISPLAYSURF.blit(titleSurf, titleRect)

        # Draw the additional "Press a key to play." text.
        pressKeySurf, pressKeyRect = makeTextObjs('Press a key to play.', PRESSFONT, LIGHTGREY)
        pressKeyRect.center = (int(WINDOWWIDTH / 2), int(WINDOWHEIGHT / 2) + 100)
        DISPLAYSURF.blit(pressKeySurf, pressKeyRect)
        pygame.display.flip()

    def render(self, DISPLAYSURF):
        pass

    def update(self):
        pass

    def handle_events(self, events):
        for e in events:
            if e.type == KEYDOWN:
                self.manager.go_to(GameScene())

class Board(object):
    """represents Archipelago the board

    The Game board is as follows:

    x_0_y_0| x_1_y_0| x_2_y_0| x_3_y_0| x_4_y_0
    x_0_y_1| x_1_y_1| x_2_y_1| x_3_y_1| x_4_y_1
    x_0_y_2| x_1_y_2| x_2_y_2| x_3_y_2| x_4_y_2
    x_0_y_3| x_1_y_3| x_2_y_3| x_3_y_3| x_4_y_3
    x_0_y_4| x_1_y_4| x_2_y_4| x_3_y_4| x_4_y_4

    may change depending on the BOARDWIDTH and BOARDHEIGHT
    """
    def __init__(self, possible_random_spaces):
        global cycles

        self.possible_random_spaces = possible_random_spaces

        self.board = []

        # self.create_random_list = [0,1,2,3]
        self.create_random_list = [0]
        self.random_block_list =[]

        #create board
        for i in range(BOARDWIDTH):
            self.board.append([BLANK] * BOARDHEIGHT)
        self.createBoard()

    def createBoard(self):
        global cycles
        global randomlist
        filled_count = copy.copy(FILLED_COUNT_AT_START)

        self.random_block_list = random.sample(FILLED_COUNT_AT_START * self.create_random_list, len(FILLED_COUNT_AT_START * self.create_random_list))
        # fill the middle
        x = BOARDCENTRE[0]
        y = BOARDCENTRE[1]
        self.board[x][y] = {'blank':False, 'seed_cycle':False, 'quantity':1, 'cycle':1, 'block': self.random_block_list.pop(0)}
        filled_tiles = [(x,y)]
        filled_count -= 1

        if len(randomlist) < FILLED_COUNT_AT_START - 1:
            randomlist.extend(random.sample(FILLED_COUNT_AT_START * PIECERANGE, len(FILLED_COUNT_AT_START * PIECERANGE)))
        self.possible_seeds = []
        self.extendPossibleSeeds((x,y))

        while filled_count > 0:
            (x,y) = self.possible_seeds.pop(0)
            self.board[x][y] = {'blank':False, 'seed_cycle':False, 'quantity':1, 'cycle':1, 'block': self.random_block_list.pop(0)}
            self.extendPossibleSeeds((x,y))
            filled_tiles.append((x,y))
            filled_count -= 1

        for (x,y) in filled_tiles:
            non_quantity = self.getTileValue((x, y))
            quantity = randomlist[0]
            if x == 0 or x == BOARDWIDTH - 1:
                if y == 0 or y == BOARDHEIGHT - 1:
                    tile_max = 3
                else:
                    tile_max = 5
            elif y == 0 or y == BOARDHEIGHT - 1:
                    tile_max = 5
            else:
                tile_max = 8 # or max(PIECERANGE)
            if quantity > tile_max:
                while quantity > tile_max:
                    quantity = quantity - tile_max
            if self.board[x][y]['block'] == 0:
                if quantity != non_quantity:
                    randomlist.pop(0)
                else:
                    n = 0
                    while quantity == non_quantity:
                        n += 1
                        if len(randomlist) < (n - 1):
                            randomlist.extend(random.sample(4 * PIECERANGE, len(4 * PIECERANGE)))
                        check_quantity = randomlist[n]
                        if check_quantity > tile_max:
                            while check_quantity > tile_max:
                                check_quantity = check_quantity - tile_max
                        if check_quantity != non_quantity:
                            randomlist.pop(n)
                            quantity = check_quantity
            else:
                randomlist.pop(0)
            self.board[x][y]['quantity'] = quantity

        # reset cycles  blanks for creating randoms
        self.getCycles()

    def extendPossibleSeeds(self, (x,y)):
        if (x-1 in range(0,BOARDWIDTH) and self.board[x-1][y]['blank'] is True):
            if (x-1, y) not in self.possible_seeds:
                self.possible_seeds.append((x-1, y))
        if (x+1 in range(0,BOARDWIDTH) and self.board[x+1][y]['blank'] is True):
            if (x+1, y) not in self.possible_seeds:
                self.possible_seeds.append((x+1, y))
        if (y-1 in range(0,BOARDHEIGHT) and self.board[x][y-1]['blank'] is True):
            if (x, y-1) not in self.possible_seeds:
                self.possible_seeds.append((x, y-1))
        if (y+1 in range(0,BOARDHEIGHT) and self.board[x][y+1]['blank'] is True):
            if (x, y+1) not in self.possible_seeds:
                self.possible_seeds.append((x, y+1))
        shuffle(self.possible_seeds)


    def fullBoard(self):
        for x in range(0,BOARDWIDTH):
            for y in range(0,BOARDHEIGHT):
                if self.board[x][y]['blank'] is True:
                    return False
                elif self.board[x][y]['block'] == 0:
                    return False
        return True

    def getCycles(self):
        global cycles
        cycles = {}

        for x in range(0,BOARDWIDTH):
            for y in range(0,BOARDHEIGHT):
                if self.board[x][y]['blank'] is True:
                    self.getHighestCycle((x,y))


    def getHighestCycle(self, (x,y)):
        global cycles

        cycles_found = []
        if (x-1 in range(0,BOARDWIDTH) and self.board[x-1][y]['blank'] is False):
            cycle = self.board[x-1][y]['cycle']
            cycles_found.append((cycle, (x-1,y)))
        if (x+1 in range(0,BOARDWIDTH) and self.board[x+1][y]['blank'] is False):
            cycle = self.board[x+1][y]['cycle']
            cycles_found.append((cycle, (x+1,y)))
        if (y-1 in range(0,BOARDHEIGHT) and self.board[x][y-1]['blank'] is False):
            cycle = self.board[x][y-1]['cycle']
            cycles_found.append((cycle, (x,y-1)))
        if (y+1 in range(0,BOARDHEIGHT) and self.board[x][y+1]['blank'] is False):
            cycle = self.board[x][y+1]['cycle']
            cycles_found.append((cycle,  (x,y+1)))

        if cycles_found == []:
            return

        # sort by cycle
        cycles_found.sort(reverse=True)
        highest_cycle = cycles_found[0][0]
        seed_list = [cycles_found[0][1]]
        if len(cycles_found) > 1:
            for n in range(1, len(cycles_found)):
                if cycles_found[n][0] == highest_cycle:
                    seed_list.append(cycles_found[n][1])

        seed = random.choice(seed_list)

        #then if cycles has key append, otherwise add
        if cycles.has_key('{}'.format(highest_cycle)):
            cycles['{}'.format(highest_cycle)].append([(x,y), seed])
            shuffle(cycles['{}'.format(highest_cycle)])
        else:
            cycles['{}'.format(highest_cycle)] = [[(x,y), seed]]

        self.board[x][y]['seed'] = highest_cycle


    def getTileValue(self, (x, y)):
        count = 0
        for xn in (x-1, x, x+1):
            if xn  not in range(0,BOARDWIDTH):
                continue
            for yn in (y-1, y, y+1):
                if yn  not in range(0,BOARDHEIGHT):
                    continue
                if (xn, yn) == (x,y):
                    continue
                if self.board[xn][yn]['blank'] is False:
                    count += 1
        """
        if x + 1 in range(0,BOARDWIDTH):
            if self.board[x + 1][y]['blank'] is False:
                count += 1
        if x - 1 in range(0,BOARDWIDTH):
            if self.board[x - 1][y]['blank'] is False:
                count += 1
        if y + 1 in range(0,BOARDHEIGHT):
            if self.board[x][y + 1]['blank'] is False:
                count += 1
        if y - 1 in range(0,BOARDHEIGHT):
            if self.board[x][y - 1]['blank'] is False:
                count += 1
        """
        return count


class CurrentPiece(object):
    #individual classes for story the next pieces
    def __init__(self, board_surface, board, quantity_val):
        self.quantity = quantity_val
        self.cycle = 1
        self.x = -1 * BOXSIZE
        self.y = -1 * BOXSIZE
        self.onboard = False
        self.onblock = False
        self.oldgrid = (-1 * BOXSIZE, -1 * BOXSIZE)
        self.oldonblock = False
        self.draw_current_piece = False
        #self.draw_old_current_piece will used for removing additonal marks around current piece
        self.draw_old_current_piece = []
        self.board_surface = board_surface
        self.board = board

    def convertMouseToGrid(self, mouseX, mouseY):
        #use closest grid position from mouse position unless it is outside the border

        self.x = ((mouseX - XMARGIN) - ((mouseX - XMARGIN)%BOXSIZE))/BOXSIZE
        if self.x not in range(0,BOARDWIDTH):
            self.x = -1 * BOXSIZE
        self.y = ((mouseY - TOPMARGIN) - ((mouseY - TOPMARGIN)%BOXSIZE))/BOXSIZE
        if self.y not in range(0,BOARDHEIGHT):
            self.y = -1 * BOXSIZE

    def getQuantity(self, quantity, board_quantity, x, y):
        if x == 0 or x == BOARDWIDTH - 1:
            if y == 0 or y == BOARDHEIGHT - 1:
                tile_max = 3
            else:
                tile_max = 5
        elif y == 0 or y == BOARDHEIGHT - 1:
                tile_max = 5
        else:
            tile_max = 8 # or max(PIECERANGE)
        if quantity > tile_max:
            new_quantity = (quantity + board_quantity - tile_max) % tile_max
        else:
            new_quantity = (quantity + board_quantity) % tile_max
        if new_quantity == 0:
            return tile_max
        else:
            return new_quantity

    def isValidPosition(self):
        # Checks if the currentPiece is within the board and not ontop of another piece

        if  self.x >= 0 and self.x < BOARDWIDTH and self.y >= 0 and self.y < BOARDHEIGHT:
            self.onboard = True
            if self.board[self.x][self.y]['block'] > 0:
                self.oldonblock = self.onblock
                self.onblock = self.board[self.x][self.y]
            else:
                self.oldonblock = self.onblock
                self.onblock = False
        else:
            self.oldonblock = self.onblock
            self.onboard = False
            self.onblock = False

    def new_current_piece(self, quantity, cycle):
        self.quantity = quantity
        self.cycle = cycle
        self.x = -1 * BOXSIZE
        self.y = -1 * BOXSIZE
        self.onboard = False
        self.onblock = False

    def renderTile(self):
        pixelx = (XMARGIN + (self.x * BOXSIZE))
        pixely = (TOPMARGIN + (self.y * BOXSIZE))
        quantity = self.getQuantity(self.quantity, self.board[self.x][self.y]['quantity'], self.x, self.y)
        boxImage, boxRect = GETCURRENTPIECEIMAGEVARIABLE['{}'.format(quantity)]
        boxRect.topleft = pixelx, pixely
        DISPLAYSURF.blit(boxImage, boxRect)

class Overlay(object):
    #class for recording and rendering scores, piece animations and other overlays
    def __init__(self, board_surface):
        self.piece_animations = []
        self.board_surface = board_surface
        self.score_overlays = []

    def drawOverlays(self):
        for score_overlay in self.score_overlays:
            DISPLAYSURF.blit(score_overlay['surface'], score_overlay['rectangle'])


    def updateOverlay(self, time_reduction):
        remove = []
        for n in range(len(self.score_overlays)):
            if self.score_overlays[n]['countdown'] - time_reduction <= 0:
                overlay_rect = self.score_overlays[n]['rectangle']
                DISPLAYSURF.blit(self.board_surface, overlay_rect, overlay_rect)
                remove.append(n)
            else:
                self.score_overlays[n]['countdown'] = self.score_overlays[n]['countdown'] - time_reduction
        remove.sort(reverse = True)
        for n in remove:
            del self.score_overlays[n]


class Status(object):
    #class for displaying score and matches
    def __init__(self, board_surface, score=0):
        self.board_surface = board_surface
        self.score = score
        self.sets_completed = 0
        scoreSurf = COUNTFONT.render('%s' % self.score, True, TEXTCOLOR)
        scoreRect = scoreSurf.get_rect()
        scoreRect.center = ((WINDOWWIDTH/2), 555)
        self.oldScoreRect = scoreRect
        setsSurf = COUNTFONT.render('%s' % self.sets_completed, True, TEXTCOLOR)
        setsRect = setsSurf.get_rect()
        setsRect.center = ((WINDOWWIDTH/2), 357)
        self.oldSetsRect = scoreRect

    def score_render(self):
        #Displays the current score and matches on the screen
        scoreSurf = COUNTFONT.render('%s' % self.score, True, TEXTCOLOR)
        scoreRect = scoreSurf.get_rect()
        scoreRect.center = ((WINDOWWIDTH/2), 555)
        unionRect = scoreRect.union(self.oldScoreRect)
        self.board_surface.blit(BGIMAGE, unionRect, unionRect)
        self.board_surface.blit(scoreSurf, scoreRect)
        self.oldScoreRect = scoreRect

    def sets_render(self):
        #Displays the current sets completed on the screen
        setsSurf = COUNTFONT.render('%s' % self.sets_completed, True, TEXTCOLOR)
        setsRect = setsSurf.get_rect()
        setsRect.center = ((WINDOWWIDTH/2), 357)
        unionRect = setsRect.union(self.oldSetsRect)
        self.board_surface.blit(BGIMAGE, unionRect, unionRect)
        self.board_surface.blit(setsSurf, setsRect)
        self.oldSetsRect = setsRect

def checkForQuit():
    for event in pygame.event.get(QUIT): # get all the QUIT events
        terminate() # terminate if any QUIT events are present
    for event in pygame.event.get(KEYUP): # get all the KEYUP events
        if event.key == K_ESCAPE:
            terminate() # terminate if the KEYUP event was for the Esc key
        pygame.event.post(event) # put the other KEYUP event objects back

def load_png(name):
    """ Load image and return image object"""
    fullname = os.path.join('texture', name)
    try:
            image = pygame.image.load(fullname)
            if image.get_alpha is None:
                image = image.convert()
            else:
                image = image.convert_alpha()
    except pygame.error, message:
            print 'Cannot load image:', fullname
            raise SystemExit, message
    return image, image.get_rect()

def makeTextObjs(text, font, color):
    surf = font.render(text, True, color)
    return surf, surf.get_rect()

def terminate():
    pygame.quit()
    sys.exit()

def main():
    global FPSCLOCK, DISPLAYSURF, BIGFONT, PRESSFONT, COUNTFONT, MATCHFONT,\
    BGIMAGE, BGRECT, TITLE, TITLERECT,\
    BLANKIMAGE, BLANKRECT,\
    ONEONEIMAGE, ONEONERECT, TWOONEIMAGE, TWOONERECT,\
    THREEONEIMAGE, THREEONERECT, FOURONEIMAGE, FOURONERECT,\
    ONETWOIMAGE, ONETWORECT, TWOTWOIMAGE, TWOTWORECT,\
    THREETWOIMAGE, THREETWORECT, FOURTWOIMAGE, FOURTWORECT,\
    ONETHREEIMAGE, ONETHREERECT, TWOTHREEIMAGE, TWOTHREERECT,\
    THREETHREEIMAGE, THREETHREERECT, FOURTHREEIMAGE, FOURTHREERECT,\
    ONEFOURIMAGE, ONEFOURRECT, TWOFOURIMAGE, TWOFOURRECT,\
    THREEFOURIMAGE, THREEFOURRECT, FOURFOURIMAGE, FOURFOURRECT,\
    ONEFIVEIMAGE, ONEFIVERECT, TWOFIVEIMAGE, TWOFIVERECT,\
    THREEFIVEIMAGE, THREEFIVERECT, FOURFIVEIMAGE, FOURFIVERECT,\
    ONESIXIMAGE, ONESIXRECT, TWOSIXIMAGE, TWOSIXRECT,\
    THREESIXIMAGE, THREESIXRECT, FOURSIXIMAGE, FOURSIXRECT,\
    ONESEVENIMAGE, ONESEVENRECT, TWOSEVENIMAGE, TWOSEVENRECT,\
    THREESEVENIMAGE, THREESEVENRECT, FOURSEVENIMAGE, FOURSEVENRECT,\
    ONEEIGHTIMAGE, ONEEIGHTRECT, TWOEIGHTIMAGE, TWOEIGHTRECT,\
    THREEEIGHTIMAGE, THREEEIGHTRECT, FOUREIGHTIMAGE, FOUREIGHTRECT,\
    ONENINEIMAGE, ONENINERECT, TWONINEIMAGE, TWONINERECT,\
    THREENINEIMAGE, THREENINERECT, FOURNINEIMAGE, FOURNINERECT,\
    ONETENIMAGE, ONETENRECT, TWOTENIMAGE, TWOTENRECT,\
    THREETENIMAGE, THREETENRECT, FOURTENIMAGE, FOURTENRECT,\
    FIVEONEIMAGE, FIVEONERECT, SIXONEIMAGE, SIXONERECT,\
    SEVENONEIMAGE, SEVENONERECT, EIGHTONEIMAGE, EIGHTONERECT,\
    FIVETWOIMAGE, FIVETWORECT, SIXTWOIMAGE, SIXTWORECT,\
    SEVENTWOIMAGE, SEVENTWORECT, EIGHTTWOIMAGE, EIGHTTWORECT,\
    FIVETHREEIMAGE, FIVETHREERECT, SIXTHREEIMAGE, SIXTHREERECT,\
    SEVENTHREEIMAGE, SEVENTHREERECT, EIGHTTHREEIMAGE, EIGHTTHREERECT,\
    FIVEFOURIMAGE, FIVEFOURRECT, SIXFOURIMAGE, SIXFOURRECT,\
    SEVENFOURIMAGE, SEVENFOURRECT, EIGHTFOURIMAGE, EIGHTFOURRECT,\
    FIVEFIVEIMAGE, FIVEFIVERECT, SIXFIVEIMAGE, SIXFIVERECT,\
    SEVENFIVEIMAGE, SEVENFIVERECT, EIGHTFIVEIMAGE, EIGHTFIVERECT,\
    FIVESIXIMAGE, FIVESIXRECT, SIXSIXIMAGE, SIXSIXRECT,\
    SEVENSIXIMAGE, SEVENSIXRECT, EIGHTSIXIMAGE, EIGHTSIXRECT,\
    FIVESEVENIMAGE, FIVESEVENRECT, SIXSEVENIMAGE, SIXSEVENRECT,\
    SEVENSEVENIMAGE, SEVENSEVENRECT, EIGHTSEVENIMAGE, EIGHTSEVENRECT,\
    FIVEEIGHTIMAGE, FIVEEIGHTRECT, SIXEIGHTIMAGE, SIXEIGHTRECT,\
    SEVENEIGHTIMAGE, SEVENEIGHTRECT, EIGHTEIGHTIMAGE, EIGHTEIGHTRECT,\
    FIVENINEIMAGE, FIVENINERECT, SIXNINEIMAGE, SIXNINERECT,\
    SEVENNINEIMAGE, SEVENNINERECT, EIGHTNINEIMAGE, EIGHTNINERECT,\
    FIVETENIMAGE, FIVETENRECT, SIXTENIMAGE, SIXTENRECT,\
    SEVENTENIMAGE, SEVENTENRECT, EIGHTTENIMAGE, EIGHTTENRECT,\
    CURRENTONEIMAGE, CURRENTONERECT, CURRENTTWOIMAGE, CURRENTTWORECT,\
    CURRENTTHREEIMAGE, CURRENTTHREERECT, CURRENTFOURIMAGE, CURRENTFOURRECT,\
    CURRENTFIVEIMAGE, CURRENTFIVERECT, CURRENTSIXIMAGE, CURRENTSIXRECT,\
    CURRENTSEVENIMAGE, CURRENTSEVENRECT, CURRENTEIGHTIMAGE, CURRENTEIGHTRECT,\
    RANDOMONEIMAGE, RANDOMONERECT, RANDOMTWOIMAGE, RANDOMTWORECT,\
    RANDOMTHREEIMAGE, RANDOMTHREERECT, RANDOMFOURIMAGE, RANDOMFOURRECT,\
    RANDOMFIVEIMAGE, RANDOMFIVERECT, RANDOMSIXIMAGE, RANDOMSIXRECT, \
    RANDOMSEVENIMAGE, RANDOMSEVENRECT, RANDOMEIGHTIMAGE, RANDOMEIGHTRECT, \
    RANDOMBLOCKIMAGE, RANDOMBLOCKRECT,\
    RANDOMBLOCKEIMAGE, RANDOMBLOCKERECT, RANDOMBLOCKNIMAGE, RANDOMBLOCKNRECT,\
    RANDOMBLOCKWIMAGE, RANDOMBLOCKWRECT, RANDOMBLOCKSIMAGE, RANDOMBLOCKSRECT,\
    BARIMAGE, BARRECT,\
    BLOCKONEIMAGE, BLOCKONERECT, BLOCKTWOIMAGE, BLOCKTWORECT, \
    BLOCKTHREEIMAGE, BLOCKTHREERECT, \
    GETBLOCKIMAGEVARIABLE, GETCURRENTPIECEIMAGEVARIABLE,\
    GETPIECEIMAGEVARIABLE, GETRANDOMPIECEIMAGEVARIABLE,\
    TOPLACEIMAGE, TOPLACERECT,\
    TOPLACERANDOMIMAGE, TOPLACERANDOMRECT,\
    TOPLACEBLOCKEDIMAGE, TOPLACEBLOCKEDRECT
    pygame.init()
    FPSCLOCK = pygame.time.Clock()
    DISPLAYSURF = pygame.display.set_mode((WINDOWWIDTH, WINDOWHEIGHT))
    PRESSFONT = pygame.font.Font('fonts/constan.ttf', 40)
    BIGFONT = pygame.font.Font('fonts/constan.ttf', 80)
    #COUNTFONT = pygame.font.SysFont('times', 45)
    COUNTFONT = pygame.font.Font('fonts/constan.ttf', 50)
    BGIMAGE, BGRECT = load_png('background.png')
    TITLE, TITLERECT = load_png('title.png')
    BLANKIMAGE, BLANKRECT = load_png('blank.png')
    ONEONEIMAGE, ONEONERECT = load_png('1_1.png')
    TWOONEIMAGE, TWOONERECT = load_png('2_1.png')
    THREEONEIMAGE, THREEONERECT = load_png('3_1.png')
    FOURONEIMAGE, FOURONERECT = load_png('4_1.png')
    ONETWOIMAGE, ONETWORECT = load_png('1_2.png')
    TWOTWOIMAGE, TWOTWORECT = load_png('2_2.png')
    THREETWOIMAGE, THREETWORECT = load_png('3_2.png')
    FOURTWOIMAGE, FOURTWORECT = load_png('4_2.png')
    ONETHREEIMAGE, ONETHREERECT = load_png('1_3.png')
    TWOTHREEIMAGE, TWOTHREERECT = load_png('2_3.png')
    THREETHREEIMAGE, THREETHREERECT = load_png('3_3.png')
    FOURTHREEIMAGE, FOURTHREERECT = load_png('4_3.png')
    ONEFOURIMAGE, ONEFOURRECT = load_png('1_4.png')
    TWOFOURIMAGE, TWOFOURRECT = load_png('2_4.png')
    THREEFOURIMAGE, THREEFOURRECT = load_png('3_4.png')
    FOURFOURIMAGE, FOURFOURRECT = load_png('4_4.png')
    ONEFIVEIMAGE, ONEFIVERECT = load_png('1_5.png')
    TWOFIVEIMAGE, TWOFIVERECT = load_png('2_5.png')
    THREEFIVEIMAGE, THREEFIVERECT = load_png('3_5.png')
    FOURFIVEIMAGE, FOURFIVERECT = load_png('4_5.png')
    ONESIXIMAGE, ONESIXRECT = load_png('1_6.png')
    TWOSIXIMAGE, TWOSIXRECT = load_png('2_6.png')
    THREESIXIMAGE, THREESIXRECT = load_png('3_6.png')
    FOURSIXIMAGE, FOURSIXRECT = load_png('4_6.png')
    ONESEVENIMAGE, ONESEVENRECT = load_png('1_7.png')
    TWOSEVENIMAGE, TWOSEVENRECT = load_png('2_7.png')
    THREESEVENIMAGE, THREESEVENRECT = load_png('3_7.png')
    FOURSEVENIMAGE, FOURSEVENRECT = load_png('4_7.png')
    ONEEIGHTIMAGE, ONEEIGHTRECT = load_png('1_8.png')
    TWOEIGHTIMAGE, TWOEIGHTRECT = load_png('2_8.png')
    THREEEIGHTIMAGE, THREEEIGHTRECT = load_png('3_8.png')
    FOUREIGHTIMAGE, FOUREIGHTRECT = load_png('4_8.png')
    ONENINEIMAGE, ONENINERECT = load_png('1_9.png')
    TWONINEIMAGE, TWONINERECT = load_png('2_9.png')
    THREENINEIMAGE, THREENINERECT = load_png('3_9.png')
    FOURNINEIMAGE, FOURNINERECT = load_png('4_9.png')
    ONETENIMAGE, ONETENRECT = load_png('1_10.png')
    TWOTENIMAGE, TWOTENRECT = load_png('2_10.png')
    THREETENIMAGE, THREETENRECT = load_png('3_10.png')
    FOURTENIMAGE, FOURTENRECT = load_png('4_10.png')

    FIVEONEIMAGE, FIVEONERECT = load_png('5_1.png')
    SIXONEIMAGE, SIXONERECT = load_png('6_1.png')
    SEVENONEIMAGE, SEVENONERECT = load_png('7_1.png')
    EIGHTONEIMAGE, EIGHTONERECT = load_png('8_1.png')
    FIVETWOIMAGE, FIVETWORECT = load_png('5_2.png')
    SIXTWOIMAGE, SIXTWORECT = load_png('6_2.png')
    SEVENTWOIMAGE, SEVENTWORECT = load_png('7_2.png')
    EIGHTTWOIMAGE, EIGHTTWORECT = load_png('8_2.png')
    FIVETHREEIMAGE, FIVETHREERECT = load_png('5_3.png')
    SIXTHREEIMAGE, SIXTHREERECT = load_png('6_3.png')
    SEVENTHREEIMAGE, SEVENTHREERECT = load_png('7_3.png')
    EIGHTTHREEIMAGE, EIGHTTHREERECT = load_png('8_3.png')
    FIVEFOURIMAGE, FIVEFOURRECT = load_png('5_4.png')
    SIXFOURIMAGE, SIXFOURRECT = load_png('6_4.png')
    SEVENFOURIMAGE, SEVENFOURRECT = load_png('7_4.png')
    EIGHTFOURIMAGE, EIGHTFOURRECT = load_png('8_4.png')
    FIVEFIVEIMAGE, FIVEFIVERECT = load_png('5_5.png')
    SIXFIVEIMAGE, SIXFIVERECT = load_png('6_5.png')
    SEVENFIVEIMAGE, SEVENFIVERECT = load_png('7_5.png')
    EIGHTFIVEIMAGE, EIGHTFIVERECT = load_png('8_5.png')
    FIVESIXIMAGE, FIVESIXRECT = load_png('5_6.png')
    SIXSIXIMAGE, SIXSIXRECT = load_png('6_6.png')
    SEVENSIXIMAGE, SEVENSIXRECT = load_png('7_6.png')
    EIGHTSIXIMAGE, EIGHTSIXRECT = load_png('8_6.png')
    FIVESEVENIMAGE, FIVESEVENRECT = load_png('5_7.png')
    SIXSEVENIMAGE, SIXSEVENRECT = load_png('6_7.png')
    SEVENSEVENIMAGE, SEVENSEVENRECT = load_png('7_7.png')
    EIGHTSEVENIMAGE, EIGHTSEVENRECT = load_png('8_7.png')
    FIVEEIGHTIMAGE, FIVEEIGHTRECT = load_png('5_8.png')
    SIXEIGHTIMAGE, SIXEIGHTRECT = load_png('6_8.png')
    SEVENEIGHTIMAGE, SEVENEIGHTRECT = load_png('7_8.png')
    EIGHTEIGHTIMAGE, EIGHTEIGHTRECT = load_png('8_8.png')
    FIVENINEIMAGE, FIVENINERECT = load_png('5_9.png')
    SIXNINEIMAGE, SIXNINERECT = load_png('6_9.png')
    SEVENNINEIMAGE, SEVENNINERECT = load_png('7_9.png')
    EIGHTNINEIMAGE, EIGHTNINERECT = load_png('8_9.png')
    FIVETENIMAGE, FIVETENRECT = load_png('5_10.png')
    SIXTENIMAGE, SIXTENRECT = load_png('6_10.png')
    SEVENTENIMAGE, SEVENTENRECT = load_png('7_10.png')
    EIGHTTENIMAGE, EIGHTTENRECT = load_png('8_10.png')

    CURRENTONEIMAGE, CURRENTONERECT = load_png('current_one.png')
    CURRENTTWOIMAGE, CURRENTTWORECT = load_png('current_two.png')
    CURRENTTHREEIMAGE, CURRENTTHREERECT = load_png('current_three.png')
    CURRENTFOURIMAGE, CURRENTFOURRECT = load_png('current_four.png')
    CURRENTFIVEIMAGE, CURRENTFIVERECT = load_png('current_five.png')
    CURRENTSIXIMAGE, CURRENTSIXRECT = load_png('current_six.png')
    CURRENTSEVENIMAGE, CURRENTSEVENRECT = load_png('current_seven.png')
    CURRENTEIGHTIMAGE, CURRENTEIGHTRECT = load_png('current_eight.png')
    RANDOMONEIMAGE, RANDOMONERECT = load_png('random_one.png')
    RANDOMTWOIMAGE, RANDOMTWORECT = load_png('random_two.png')
    RANDOMTHREEIMAGE, RANDOMTHREERECT = load_png('random_three.png')
    RANDOMFOURIMAGE, RANDOMFOURRECT = load_png('random_four.png')
    RANDOMFIVEIMAGE, RANDOMFIVERECT = load_png('random_five.png')
    RANDOMSIXIMAGE, RANDOMSIXRECT = load_png('random_six.png')
    RANDOMSEVENIMAGE, RANDOMSEVENRECT = load_png('random_seven.png')
    RANDOMEIGHTIMAGE, RANDOMEIGHTRECT = load_png('random_eight.png')
    RANDOMBLOCKIMAGE, RANDOMBLOCKRECT = load_png('random_block.png')
    RANDOMBLOCKEIMAGE, RANDOMBLOCKERECT = load_png('random_block_E.png')
    RANDOMBLOCKNIMAGE, RANDOMBLOCKNRECT = load_png('random_block_N.png')
    RANDOMBLOCKWIMAGE, RANDOMBLOCKWRECT = load_png('random_block_W.png')
    RANDOMBLOCKSIMAGE, RANDOMBLOCKSRECT = load_png('random_block_S.png')
    BARIMAGE, BARRECT = load_png('bar.png')
    BLOCKONEIMAGE, BLOCKONERECT = load_png('block_one.png')
    BLOCKTWOIMAGE, BLOCKTWORECT = load_png('block_two.png')
    BLOCKTHREEIMAGE, BLOCKTHREERECT = load_png('block_three.png')
    TOPLACEIMAGE, TOPLACERECT = load_png('to_place.png')
    TOPLACERANDOMIMAGE, TOPLACERANDOMRECT = load_png('to_place_random.png')
    TOPLACEBLOCKEDIMAGE, TOPLACEBLOCKEDRECT = load_png('to_place_blocked.png')

    GETBLOCKIMAGEVARIABLE = {
                            '1':(BLOCKONEIMAGE, BLOCKONERECT),
                            '2':(BLOCKTWOIMAGE, BLOCKTWORECT),
                            '3':(BLOCKTHREEIMAGE, BLOCKTHREERECT)
                            }

    GETCURRENTPIECEIMAGEVARIABLE = {
                                '1':(CURRENTONEIMAGE, CURRENTONERECT),
                                '2':(CURRENTTWOIMAGE, CURRENTTWORECT),
                                '3':(CURRENTTHREEIMAGE, CURRENTTHREERECT),
                                '4':(CURRENTFOURIMAGE, CURRENTFOURRECT),
                                '5':(CURRENTFIVEIMAGE, CURRENTFIVERECT),
                                '6':(CURRENTSIXIMAGE, CURRENTSIXRECT),
                                '7':(CURRENTSEVENIMAGE, CURRENTSEVENRECT),
                                '8':(CURRENTEIGHTIMAGE, CURRENTEIGHTRECT)
                                }

    GETPIECEIMAGEVARIABLE = {
                            '1_1':(ONEONEIMAGE, ONEONERECT),
                            '2_1':(TWOONEIMAGE, TWOONERECT),
                            '3_1':(THREEONEIMAGE, THREEONERECT),
                            '4_1':(FOURONEIMAGE, FOURONERECT),
                            '1_2':(ONETWOIMAGE, ONETWORECT),
                            '2_2':(TWOTWOIMAGE, TWOTWORECT),
                            '3_2':(THREETWOIMAGE, THREETWORECT),
                            '4_2':(FOURTWOIMAGE, FOURTWORECT),
                            '1_3':(ONETHREEIMAGE, ONETHREERECT),
                            '2_3':(TWOTHREEIMAGE, TWOTHREERECT),
                            '3_3':(THREETHREEIMAGE, THREETHREERECT),
                            '4_3':(FOURTHREEIMAGE, FOURTHREERECT),
                            '1_4':(ONEFOURIMAGE, ONEFOURRECT),
                            '2_4':(TWOFOURIMAGE, TWOFOURRECT),
                            '3_4':(THREEFOURIMAGE, THREEFOURRECT),
                            '4_4':(FOURFOURIMAGE, FOURFOURRECT),
                            '1_5':(ONEFIVEIMAGE, ONEFIVERECT),
                            '2_5':(TWOFIVEIMAGE, TWOFIVERECT),
                            '3_5':(THREEFIVEIMAGE, THREEFIVERECT),
                            '4_5':(FOURFIVEIMAGE, FOURFIVERECT),
                            '1_6':(ONESIXIMAGE, ONESIXRECT),
                            '2_6':(TWOSIXIMAGE, TWOSIXRECT),
                            '3_6':(THREESIXIMAGE, THREESIXRECT),
                            '4_6':(FOURSIXIMAGE, FOURSIXRECT),
                            '1_7':(ONESEVENIMAGE, ONESEVENRECT),
                            '2_7':(TWOSEVENIMAGE, TWOSEVENRECT),
                            '3_7':(THREESEVENIMAGE, THREESEVENRECT),
                            '4_7':(FOURSEVENIMAGE, FOURSEVENRECT),
                            '1_8':(ONEEIGHTIMAGE, ONEEIGHTRECT),
                            '2_8':(TWOEIGHTIMAGE, TWOEIGHTRECT),
                            '3_8':(THREEEIGHTIMAGE, THREEEIGHTRECT),
                            '4_8':(FOUREIGHTIMAGE, FOUREIGHTRECT),
                            '1_9':(ONENINEIMAGE, ONENINERECT),
                            '2_9':(TWONINEIMAGE, TWONINERECT),
                            '3_9':(THREENINEIMAGE, THREENINERECT),
                            '4_9':(FOURNINEIMAGE, FOURNINERECT),
                            '1_10':(ONETENIMAGE, ONETENRECT),
                            '2_10':(TWOTENIMAGE, TWOTENRECT),
                            '3_10':(THREETENIMAGE, THREETENRECT),
                            '4_10':(FOURTENIMAGE, FOURTENRECT),
                            '5_1':(FIVEONEIMAGE, FIVEONERECT),
                            '6_1':(SIXONEIMAGE, SIXONERECT),
                            '7_1':(SEVENONEIMAGE, SEVENONERECT),
                            '8_1':(EIGHTONEIMAGE, EIGHTONERECT),
                            '5_2':(FIVETWOIMAGE, FIVETWORECT),
                            '6_2':(SIXTWOIMAGE, SIXTWORECT),
                            '7_2':(SEVENTWOIMAGE, SEVENTWORECT),
                            '8_2':(EIGHTTWOIMAGE, EIGHTTWORECT),
                            '5_3':(FIVETHREEIMAGE, FIVETHREERECT),
                            '6_3':(SIXTHREEIMAGE, SIXTHREERECT),
                            '7_3':(SEVENTHREEIMAGE, SEVENTHREERECT),
                            '8_3':(EIGHTTHREEIMAGE, EIGHTTHREERECT),
                            '5_4':(FIVEFOURIMAGE, FIVEFOURRECT),
                            '6_4':(SIXFOURIMAGE, SIXFOURRECT),
                            '7_4':(SEVENFOURIMAGE, SEVENFOURRECT),
                            '8_4':(EIGHTFOURIMAGE, EIGHTFOURRECT),
                            '5_5':(FIVEFIVEIMAGE, FIVEFIVERECT),
                            '6_5':(SIXFIVEIMAGE, SIXFIVERECT),
                            '7_5':(SEVENFIVEIMAGE, SEVENFIVERECT),
                            '8_5':(EIGHTFIVEIMAGE, EIGHTFIVERECT),
                            '5_6':(FIVESIXIMAGE, FIVESIXRECT),
                            '6_6':(SIXSIXIMAGE, SIXSIXRECT),
                            '7_6':(SEVENSIXIMAGE, SEVENSIXRECT),
                            '8_6':(EIGHTSIXIMAGE, EIGHTSIXRECT),
                            '5_7':(FIVESEVENIMAGE, FIVESEVENRECT),
                            '6_7':(SIXSEVENIMAGE, SIXSEVENRECT),
                            '7_7':(SEVENSEVENIMAGE, SEVENSEVENRECT),
                            '8_7':(EIGHTSEVENIMAGE, EIGHTSEVENRECT),
                            '5_8':(FIVEEIGHTIMAGE, FIVEEIGHTRECT),
                            '6_8':(SIXEIGHTIMAGE, SIXEIGHTRECT),
                            '7_8':(SEVENEIGHTIMAGE, SEVENEIGHTRECT),
                            '8_8':(EIGHTEIGHTIMAGE, EIGHTEIGHTRECT),
                            '5_9':(FIVENINEIMAGE, FIVENINERECT),
                            '6_9':(SIXNINEIMAGE, SIXNINERECT),
                            '7_9':(SEVENNINEIMAGE, SEVENNINERECT),
                            '8_9':(EIGHTNINEIMAGE, EIGHTNINERECT),
                            '5_10':(FIVETENIMAGE, FIVETENRECT),
                            '6_10':(SIXTENIMAGE, SIXTENRECT),
                            '7_10':(SEVENTENIMAGE, SEVENTENRECT),
                            '8_10':(EIGHTTENIMAGE, EIGHTTENRECT)
                            }

    GETRANDOMPIECEIMAGEVARIABLE = {
                                '1':(RANDOMONEIMAGE, RANDOMONERECT),
                                '2':(RANDOMTWOIMAGE, RANDOMTWORECT),
                                '3':(RANDOMTHREEIMAGE, RANDOMTHREERECT),
                                '4':(RANDOMFOURIMAGE, RANDOMFOURRECT),
                                '5':(RANDOMFIVEIMAGE, RANDOMFIVERECT),
                                '6':(RANDOMSIXIMAGE, RANDOMSIXRECT),
                                '7':(RANDOMSEVENIMAGE, RANDOMSEVENRECT),
                                '8':(RANDOMEIGHTIMAGE, RANDOMEIGHTRECT)
                                }

    manager = SceneMananger()

    while True:
        checkForQuit()
        manager.scene.handle_events(pygame.event.get())
        manager.scene.update()
        manager.scene.render(DISPLAYSURF)
        FPSCLOCK.tick(FPS)

if __name__ == '__main__':
    main()
