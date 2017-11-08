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
        'quantity': False,
        'kind': False,
        'block': 0
        }

LEFT = 1
RIGHT = 3

PIECERANGE = 3 * range(1,5)
MAXPIECERANGE = 4
KINDLIST = ['This', 'That', 'Other', 'This', 'That', 'Other', 'This', 'That', 'Other', 'This', 'That', 'Other']
RANDOMCOUNT_VAR = -1
COUNTDOWN_VAR = 3
RANDOM_PIECE_LENGTH_VAR = 6
FILLED_COUNT_AT_START = 5
seeds = {}
randomlist = []
randomkindlist = []
SCORE_BASE = 2
# MAXCYCLE = 10
"""
FIBONACCI = [10, 20]
for n in range(1, 19):
    FIBONACCI.append(FIBONACCI[n] + FIBONACCI[n -1])
"""

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
        global randomkindlist
        global seeds

        seeds = {}

        #randomlist is a list of 4 time the piece range randomised, this prevents
        #strings random numbers which feel to unlikely, allows the player to
        #try and predict what is coming
        randomlist = random.sample(4 * PIECERANGE, len(4 * PIECERANGE))
        randomkindlist = random.sample(4 * KINDLIST, len(4 * PIECERANGE))

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
        if len(randomlist) < 4:
            randomlist = random.sample(4 * PIECERANGE, len(4 * PIECERANGE))
            randomkindlist = random.sample(4 * KINDLIST, len(4 * PIECERANGE))
        self.currentPiece  = CurrentPiece(self.board_surface, self.board.board, randomlist.pop(0), randomkindlist.pop(0), self.random_pieces)
        self.nextPieceOne = {'quantity':(randomlist.pop()), 'kind': (randomkindlist.pop())}
        self.nextPieceTwo = {'quantity':(randomlist.pop()), 'kind': (randomkindlist.pop())}

        self.status = Status(self.board_surface, 0)
        DISPLAYSURF.blit(BGIMAGE, BGRECT)
        for x in range(BOARDWIDTH):
            for y in range(BOARDHEIGHT):
                self.drawBox(x, y, self.board.board[x][y])
        first = True
        for random_dict in self.random_pieces:
            self.drawRandomPiece(random_dict['coords'], random_dict['quantity'], random_dict['kind'], random_dict['seed'])
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
            """
            # check if should draw current piece
            if self.currentPiece.onboard == True and self.currentPiece.onblock == False:
                self.currentPiece.renderTile()
            """
            self.Overlay.updateOverlay(1)
            self.Overlay.drawOverlays()
            pygame.display.flip()

    def update(self):
        pass

    def handle_events(self, events):
        global randomlist
        global randomkindlist

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
                            randomkindlist.extend(random.sample(4 * KINDLIST, len(4 * PIECERANGE)))
                        self.currentPiece.new_current_piece(randomlist.pop(), randomkindlist.pop())
                        self.nextPieceOne = {'quantity':(randomlist.pop()), 'kind': (randomkindlist.pop())}
                        self.nextPieceTwo = {'quantity':(randomlist.pop()), 'kind': (randomkindlist.pop())}
                    elif self.countdown == 2:
                        self.currentPiece.new_current_piece(copy.copy(self.nextPieceOne['quantity']), copy.copy(self.nextPieceOne['kind']))
                        self.nextPieceOne = copy.copy(self.nextPieceTwo)
                        self.nextPieceTwo = False
                    else:
                        self.currentPiece.new_current_piece(copy.copy(self.nextPieceOne['quantity']), copy.copy(self.nextPieceOne['kind']))
                        self.nextPieceOne = False
                        self.nextPieceTwo = False
                    if self.countdown == 3:
                        self.drawCurrentPiece()
                        for random_dict in self.random_pieces:
                            if random_dict == False or random_dict == 'blocked':
                                continue
                            self.drawRandomPiece(random_dict['coords'], random_dict['quantity'], random_dict['kind'], random_dict['seed'])
                        self.drawRandomToPlace()
                        self.status.sets_render()
                        DISPLAYSURF.blit(self.board_surface, self.board_rect)
                        pygame.display.flip()

    def addToBoard(self):
        global seeds
        global randomlist
        global randomkindlist
        # fill in the board based on piece's location, quantity, and rotation
        self.added_pieces = []
        self.score_chain_bonus = 1
        self.countdown -= 1
        self.update_countdown = True
        x = self.currentPiece.x
        y = self.currentPiece.y
        self.to_investigate = [(x,y)]
        if self.board.board[x][y]['blank'] is True:
            self.getAddedPieces(1, self.currentPiece.quantity, False, self.currentPiece.kind)
            self.board.board[x][y] = {
                'blank':False,
                'quantity':self.currentPiece.quantity,
                'kind':self.currentPiece.kind,
                'block': 0
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
            kind = self.currentPiece.kind
            """
            if self.currentPiece.quantity > MAXPIECERANGE:
                new_quantity = (quantity + self.currentPiece.quantity - MAXPIECERANGE) % MAXPIECERANGE
            else:
            """
            new_quantity = (quantity + self.currentPiece.quantity) % MAXPIECERANGE
            if self.board.board[x][y]['kind'] != kind:
                self.board.board[x][y]['kind'] = kind
            if new_quantity == 0:
                if quantity == MAXPIECERANGE:
                    self.board.board[x][y]['quantity'] = MAXPIECERANGE
                    self.getAddedPieces(quantity, quantity, True, kind)
                else:
                    # it has added to the max value for the tile
                    self.board.board[x][y]['quantity'] =  MAXPIECERANGE
                    self.getAddedPieces(quantity, MAXPIECERANGE, False, kind)
            elif new_quantity == quantity:
                # it has cycled around in a complete cycle and now has the same value
                self.board.board[x][y]['quantity'] = new_quantity
                self.getAddedPieces(quantity, quantity, True, kind)
            elif new_quantity < quantity:
                # it has cycled around but not made it completely back to quantity
                self.board.board[x][y]['quantity'] = new_quantity
                self.getAddedPieces(quantity, new_quantity, True, kind)
            else:
                # it hasn't cycled just added onto
                self.board.board[x][y]['quantity'] = new_quantity
                self.getAddedPieces(quantity, new_quantity, False, kind)
        # update the currentpiece so it is clear
        self.clearCurrentPiece()
        # draw each dot which is added
        for n in range(0, len(self.added_pieces)):
            added_piece = self.added_pieces[n]
            x = self.currentPiece.x
            y = self.currentPiece.y
            quantity = added_piece['quantity']
            kind = added_piece['kind']
            pixelx, pixely = self.convertToPixelCoords(x, y)
            boxImage, boxRect = GETPIECEIMAGEVARIABLE['{}_{}'.format(quantity, kind)]
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
                # return as can't add falses around current piece
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
                    if len(randomlist) <= 4:
                        randomlist.extend(random.sample(4 * PIECERANGE, len(4 * PIECERANGE)))
                        randomkindlist.extend(random.sample(4 * KINDLIST, len(4 * PIECERANGE)))
                    quantity = randomlist.pop(0)
                    kind = randomkindlist.pop(0)
                    self.random_pieces[index] = {
                                                'coords': (c_x, c_y),
                                                'quantity': quantity,
                                                'kind': kind,
                                                'block': 0,
                                                'seed': (x,y)
                                              }
                    self.drawRandomPiece((c_x, c_y), quantity, kind, (x,y))
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
                    kind = random_piece['kind']
                    block = random_piece['block']
                    self.board.board[x][y] = {
                        'blank':False,
                        'quantity': quantity,
                        'kind': kind, 'block': block
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
            seeds = {}
            for x in range(0,BOARDWIDTH):
                for y in range(0,BOARDHEIGHT):
                    if self.board.board[x][y]['blank'] is True:
                        self.board.getHighestSeed((x,y))
            self.getRandom(RANDOM_PIECE_LENGTH_VAR)

    def appendCrossToInvestigate(self, (x,y)):
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
        return

    def checkCross(self, (x,y)):
        if self.board.board[x][y]['block'] > 0:
            return False
        count = 0
        quantity = self.board.board[x][y]['quantity']
        kind = self.board.board[x][y]['kind']

        if x-1 in range(0,BOARDWIDTH):
            if self.board.board[x-1][y]['blank'] is False:
                if self.board.board[x - 1][y]['kind'] == kind:
                    count += 1
        if x+1 in range(0,BOARDWIDTH):
            if self.board.board[x+1][y]['blank'] is False:
                if self.board.board[x + 1][y]['kind'] == kind:
                    count += 1
        if y-1 in range(0,BOARDHEIGHT):
            if self.board.board[x][y-1]['blank'] is False:
                if self.board.board[x][y - 1]['kind'] == kind:
                    count += 1
        if y+1 in range(0,BOARDHEIGHT):
            if self.board.board[x][y+1]['blank'] is False:
                if self.board.board[x][y + 1]['kind'] == kind:
                    count += 1

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
                # DISPLAYSURF.blit(self.board_surface, (pixelx, pixely), (pixelx, pixely, BOXSIZE, BOXSIZE))
                # draw background
                DISPLAYSURF.blit(BGIMAGE, (pixelx, pixely), (pixelx, pixely, BOXSIZE, BOXSIZE))
                for random_piece in self.random_pieces:
                    if random_piece in ('blocked', False):
                        continue
                    if random_piece['coords'] == (self.currentPiece.x, self.currentPiece.y):
                        seed = random_piece['seed']
                        # draw random box back ontop
                        if seed == False:
                            RANDOMBLOCKRECT.topleft = pixelx, pixely
                            DISPLAYSURF.blit(RANDOMBLOCKIMAGE, RANDOMBLOCKRECT)
                        if seed == (self.currentPiece.x-1,self.currentPiece.y):
                            # w
                            RANDOMBLOCKWRECT.topleft = pixelx, pixely
                            DISPLAYSURF.blit(RANDOMBLOCKWIMAGE, RANDOMBLOCKWRECT)
                        elif seed == (self.currentPiece.x+1,self.currentPiece.y):
                            # E
                            RANDOMBLOCKERECT.topleft = pixelx, pixely
                            DISPLAYSURF.blit(RANDOMBLOCKEIMAGE, RANDOMBLOCKERECT)
                        elif seed == (self.currentPiece.x,self.currentPiece.y-1):
                            # N
                            RANDOMBLOCKNRECT.topleft = pixelx, pixely
                            DISPLAYSURF.blit(RANDOMBLOCKNIMAGE, RANDOMBLOCKNRECT)
                        elif seed == (self.currentPiece.x,self.currentPiece.y+1):
                            # S
                            RANDOMBLOCKSRECT.topleft = pixelx, pixely
                            DISPLAYSURF.blit(RANDOMBLOCKSIMAGE, RANDOMBLOCKSRECT)
                        break
                quantity = self.currentPiece.getQuantity(self.currentPiece.quantity, self.board.board[self.currentPiece.x][self.currentPiece.y]['quantity'], self.currentPiece.x, self.currentPiece.y)
                kind = self.currentPiece.kind
                boxImage, boxRect = GETCURRENTPIECEIMAGEVARIABLE['{}_{}'.format(quantity, kind)]
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
        # max_removed = []
        while checking is True:
            to_remove = []
            for (x,y) in self.to_investigate:
                check = self.checkCross((x,y))
                if check:
                    to_remove.append((x,y))
            """
            if max_removed != []:
                 for x in range(0,BOARDWIDTH):
                    for y in range(0,BOARDHEIGHT):
                        if self.board.board[x][y]['quantity'] in max_removed:
                            if (x,y) not in to_remove:
                                to_remove.append((x,y))
            """
            if to_remove == []:
                checking = False
            else:
                removed = True
                # max_removed = []
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
                self.to_investigate = []
                for (x,y) in to_remove:
                    quantity = self.board.board[x][y]['quantity']
                    """
                    if cycle == MAXCYCLE:
                        if cycle not in max_removed:
                            max_removed.append(quantity)
                    """
                    self.board.board[x][y] = BLANK
                    score_increase = 4 ** self.score_chain_bonus
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
        boxImage, boxRect = GETPIECEIMAGEVARIABLE['{}_{}'.format(self.currentPiece.quantity, self.currentPiece.kind)]
        boxRect.topleft = 100, 391
        self.board_surface.blit(boxImage, boxRect)

        self.board_surface.blit(BGIMAGE, (175, 391), (175, 391, BOXSIZE, BOXSIZE))
        boxImage, boxRect = GETPIECEIMAGEVARIABLE['{}_{}'.format(self.nextPieceOne['quantity'], self.nextPieceOne['kind'])]
        boxRect.topleft = 175, 391
        self.board_surface.blit(boxImage, boxRect)

        self.board_surface.blit(BGIMAGE, (250, 391), (250, 391, BOXSIZE, BOXSIZE))
        boxImage, boxRect = GETPIECEIMAGEVARIABLE['{}_{}'.format(self.nextPieceTwo['quantity'], self.nextPieceTwo['kind'])]
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
            boxImage, boxRect = GETPIECEIMAGEVARIABLE['{}_{}'.format(values['quantity'], values['kind'])]
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


    def drawRandomPiece(self, (x,y), quantity, kind, seed):
        pixelx, pixely = self.convertToPixelCoords(x, y)
        # background with out the black circle
        self.board_surface.blit(BGIMAGE, (pixelx, pixely), (pixelx, pixely, BOXSIZE, BOXSIZE))
        boxImage, boxRect = GETRANDOMPIECEIMAGEVARIABLE['{}_{}'.format(quantity, kind)]
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
            # not drawing blocks as nicer that they just disappear
            TOPLACEBLOCKEDRECT.topleft = from_x_margin, 507
            self.board_surface.blit(TOPLACEBLOCKEDIMAGE, TOPLACEBLOCKEDRECT)


    def getAddedPieces(self, quantity, new_quantity, cycled, kind):
        if cycled:
            for n in range(quantity, MAXPIECERANGE + 1 ):
                self.added_pieces.append({'quantity':n, 'kind':kind})
            for n in range(1, new_quantity + 1):
                self.added_pieces.append({'quantity':n, 'kind':kind})
        else:
            for n in range(quantity, new_quantity + 1):
                self.added_pieces.append({'quantity':n, 'kind':kind})


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
        global seeds
        global randomlist
        global randomkindlist
        self.false_random_count = 0

        self.random_pieces = []

        self.draw_random_position = True
        if seeds == {}:
            if self.board.board[0][0]['blank'] is True:
                self.board.createBoard()

        if len(randomlist) < randomlength:
            sets_needed = int(math.ceil(randomlength / 4.0))
            if sets_needed < 4:
                sets_needed = 4
            randomlist.extend(random.sample(sets_needed * PIECERANGE, len(sets_needed * PIECERANGE)))
            randomkindlist.extend(random.sample(sets_needed * KINDLIST, len(sets_needed * PIECERANGE)))
        # get a list of new random coordinates, add one for piece if player places
        # on a random piece
        seeds_keys = seeds.keys()
        seeds_keys.sort()
        if seeds_keys == []:
            # if there are no pieces on the board
            if (self.random_pieces == []
                    and self.board.board[1][1]['blank'] is True):
                # if no seeds found, there are no current random pieces and the board
                # is blank, i.e.: don't overwrite randompieces if the board isn't blank
                self.random_pieces = [{'coords': BOARDCENTRE, 'quantity': randomlist.pop(0), 'kind': randomkindlist.pop(0), 'block': 0, 'seed':False}]
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
            seeds_list = seeds[seeds_keys[key]]
            length_seeds_list = len(seeds_list)
            for n in range(0, length_seeds_list):
                # check not in random_pieces
                coord = seeds_list[n][0]
                if coord in current_random_coords:
                    continue
                seed = seeds_list[n][1]
                (x, y) = coord
                quantity = randomlist.pop(0)
                kind  = randomkindlist.pop(0)
                self.random_pieces.insert(0, {
                                            'coords': coord,
                                            'quantity': quantity,
                                            'kind':kind,
                                            'block': 0,
                                            'seed': seed
                                          })
                length_required -= 1
                if length_required == 0:
                    break
            key += 1
            if key >= len(seeds_keys):
                for n in range(0, length_required):
                    self.random_pieces.insert(0, False)
                    self.false_random_count += 1
                    length_required -= 1
                    if length_required == 0:
                        break

    def updateFalseRandoms(self, to_remove):
        global seeds
        global randomlist
        global randomkindlist

        new_randoms = []

        seeds = {}

        for x in range(0,BOARDWIDTH):
            for y in range(0,BOARDHEIGHT):
                if self.board.board[x][y]['blank'] is True:
                    self.board.getHighestSeed((x,y))

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
            randomkindlist.extend(random.sample(sets_needed * KINDLIST, len(sets_needed * PIECERANGE)))
        seeds_keys = seeds.keys()
        seeds_keys.sort()
        key = 0
        updating_false_randoms = True
        # will break if not enough to fill random_pieces
        while updating_false_randoms is True:
            seeds_list = seeds[seeds_keys[key]]
            length_seeds_list = len(seeds_list)
            for n in range(0, length_seeds_list):
                (x,y) = seeds_list[n][0]
                # check not already in random_pieces
                if (x,y) in current_random_coords:
                    continue
                seed = seeds_list[n][1]
                quantity = randomlist.pop(0)
                kind = randomkindlist.pop(0)
                index = false_randoms_index.pop(0)
                self.random_pieces[index] = {
                                            'coords': (x,y),
                                            'quantity': quantity,
                                            'kind': kind,
                                            'block': 0,
                                            'seed': seed
                                          }
                new_randoms.append({'coords':(x,y), 'quantity':quantity, 'kind':kind, 'seed':seed})
                self.drawRandomPiece((x,y), quantity, kind, seed)
                # why investigating?
                self.appendCrossToInvestigate((x,y))
                self.false_random_count -= 1
                if self.false_random_count == 0:
                    updating_false_randoms = False
                    break
            key += 1
            if key >= len(seeds_keys):
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
        global seeds

        self.createSpawnRank()

        self.possible_random_spaces = possible_random_spaces

        self.board = []

        # self.create_random_list = [0,1,2,3]
        self.create_random_list = [0,0,0,0]
        self.random_block_list =[]

        #create board
        for i in range(BOARDWIDTH):
            self.board.append([BLANK] * BOARDHEIGHT)
        self.createBoard()

    def createBoard(self):
        global seeds
        global randomlist
        global randomkindlist
        filled_count = copy.copy(FILLED_COUNT_AT_START)

        self.random_block_list = random.sample(FILLED_COUNT_AT_START * self.create_random_list, len(FILLED_COUNT_AT_START * self.create_random_list))
        # kind_list_length = len(self.random_block_list)
        # self.random_kind_list = random.sample((kind_list_length/ len(KINDLIST)) * KINDLIST, kind_list_length)
        if len(randomlist) < FILLED_COUNT_AT_START:
            randomlist.extend(random.sample(FILLED_COUNT_AT_START * PIECERANGE, len(FILLED_COUNT_AT_START * PIECERANGE)))
            randomkindlist.extend(random.sample(FILLED_COUNT_AT_START * KINDLIST, len(FILLED_COUNT_AT_START * PIECERANGE)))
        # fill the middle
        x = BOARDCENTRE[0]
        y = BOARDCENTRE[1]
        self.board[x][y] = {'blank':False, 'quantity':1, 'kind':randomkindlist.pop(), 'block': self.random_block_list.pop(0)}
        filled_tiles = [(x,y)]
        filled_count -= 1

        """
        if len(randomlist) < FILLED_COUNT_AT_START - 1:
            randomlist.extend(random.sample(FILLED_COUNT_AT_START * PIECERANGE, len(FILLED_COUNT_AT_START * PIECERANGE)))
        """
        self.possible_seeds = []
        self.extendPossibleSeeds((x,y))

        while filled_count > 0:
            (x,y) = self.possible_seeds.pop(0)
            self.board[x][y] = {'blank':False, 'quantity':1, 'kind':randomkindlist.pop(), 'block': self.random_block_list.pop(0)}
            self.extendPossibleSeeds((x,y))
            filled_tiles.append((x,y))
            filled_count -= 1

        for (x,y) in filled_tiles:
            tile_values = self.getTileValue((x, y))
            kind = self.board[x][y]['kind']
            non_quantity = tile_values['{}_count'.format(kind)]
            quantity = randomlist[0]
            if self.board[x][y]['block'] == 0:
                if quantity != non_quantity:
                    randomlist.pop(0)
                else:
                    n = 0
                    while quantity == non_quantity:
                        n += 1
                        if len(randomlist) < (n - 1):
                            randomlist.extend(random.sample(4 * PIECERANGE, len(4 * PIECERANGE)))
                            randomkindlist.extend(random.sample(4 * KINDLIST, len(4 * PIECERANGE)))
                        check_quantity = randomlist[n]
                        if check_quantity != non_quantity:
                            randomlist.pop(n)
                            quantity = check_quantity
            else:
                randomlist.pop(0)
            self.board[x][y]['quantity'] = quantity

        # reset cycles  blanks for creating randoms
        # self.getCycles()
        self.getSeeds()

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

    def createSpawnRank(self):
        self.seed_ranks = {}
        centre = (3,3)
        rank = 1
        rank_count = 0
        self.investigated = []
        self.to_rank = [centre]
        while rank_count <(BOARDWIDTH*BOARDHEIGHT):
            # self.spawn_ranks[rank] = []
            self.highest_rank = rank
            for (x,y) in self.to_rank:
                # self.spawn_ranks[rank].append((x,y))
                self.seed_ranks['{}_{}'.format(x,y)] = rank
                self.investigated.append((x,y))
                rank_count += 1
            self.ranked = copy.copy(self.to_rank)
            self.to_rank = []
            self.getNextRank()
            rank += 1



    def getNextRank(self):
        for (x,y) in self.ranked:
            for nx in (x-1, x, x+1):
                if x in range(0,BOARDWIDTH):
                    for yx in (y-1, y, y+1):
                        if yx in range(0,BOARDHEIGHT):
                            if (nx, yx) != (x,y):
                                if (nx, yx) not in self.investigated:
                                    if (nx, yx) not in self.to_rank:
                                        self.to_rank.append((nx, yx))

    """
    def getCycles(self):
        global cycles
        cycles = {}

        for x in range(0,BOARDWIDTH):
            for y in range(0,BOARDHEIGHT):
                if self.board[x][y]['blank'] is True:
                    self.getHighestCycle((x,y))
    """
    def getSeeds(self):
        global seeds
        seeds = {}

        for n in range(1, self.highest_rank + 1):
            seeds[n] = []
        for x in range(0,BOARDWIDTH):
            for y in range(0,BOARDHEIGHT):
                if self.board[x][y]['blank'] is True:
                    self.getHighestSeed((x,y))

    def getHighestSeed(self, (x,y)):
        global seeds

        seeds_found = []
        if (x-1 in range(0,BOARDWIDTH) and self.board[x-1][y]['blank'] is False):
            rank = self.seed_ranks['{}_{}'.format(x-1,y)]
            seeds_found.append((rank, (x-1,y)))
        if (x+1 in range(0,BOARDWIDTH) and self.board[x+1][y]['blank'] is False):
            rank = self.seed_ranks['{}_{}'.format(x+1,y)]
            seeds_found.append((rank, (x+1,y)))
        if (y-1 in range(0,BOARDHEIGHT) and self.board[x][y-1]['blank'] is False):
            rank = self.seed_ranks['{}_{}'.format(x,y-1)]
            seeds_found.append((rank, (x,y-1)))
        if (y+1 in range(0,BOARDHEIGHT) and self.board[x][y+1]['blank'] is False):
            rank = self.seed_ranks['{}_{}'.format(x,y+1)]
            seeds_found.append((rank,  (x,y+1)))
        if seeds_found == []:
            return False

        # sort by rank
        seeds_found.sort()
        highest_found_rank = seeds_found[0][0]
        seed_list = [seeds_found[0][1]]
        if len(seeds_found) > 1:
            for n in range(1, len(seeds_found)):
                if seeds_found[n][0] == highest_found_rank:
                    seed_list.append(seeds_found[n][1])

        seed = random.choice(seed_list)

        #then if seeds has key append, otherwise add
        if seeds.has_key('{}'.format(highest_found_rank)):
            seeds['{}'.format(highest_found_rank)].append([(x,y), seed])
            shuffle(seeds['{}'.format(highest_found_rank)])
        else:
            seeds['{}'.format(highest_found_rank)] = [[(x,y), seed]]

        self.board[x][y]['seed'] = highest_found_rank


    """
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
        """


    def getTileValue(self, (x, y)):
        This_count = 0
        That_count = 0
        Other_count = 0
        if x + 1 in range(0,BOARDWIDTH):
            if self.board[x + 1][y]['blank'] is False:
                if self.board[x + 1][y]['kind'] == 'This':
                    This_count += 1
                elif self.board[x + 1][y]['kind'] == 'That':
                    That_count += 1
                else:
                    Other_count += 1
        if x - 1 in range(0,BOARDWIDTH):
            if self.board[x - 1][y]['blank'] is False:
                if self.board[x - 1][y]['kind'] == 'This':
                    This_count += 1
                elif self.board[x - 1][y]['kind'] == 'That':
                    That_count += 1
                else:
                    Other_count += 1
        if y + 1 in range(0,BOARDHEIGHT):
            if self.board[x][y + 1]['blank'] is False:
               if self.board[x][y + 1]['kind'] == 'This':
                    This_count += 1
               elif self.board[x][y + 1]['kind'] == 'That':
                    That_count += 1
               else:
                    Other_count += 1
        if y - 1 in range(0,BOARDHEIGHT):
            if self.board[x][y - 1]['blank'] is False:
                if self.board[x][y - 1]['kind'] == 'This':
                    This_count += 1
                elif self.board[x][y - 1]['kind'] == 'That':
                    That_count += 1
                else:
                    Other_count += 1
        return {'This_count':This_count, 'That_count':That_count, 'Other_count':Other_count}


class CurrentPiece(object):
    #individual classes for story the next pieces
    def __init__(self, board_surface, board, quantity_val, kind_val, random_pieces):
        self.quantity = quantity_val
        self.kind = kind_val
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
        self.random_pieces = random_pieces

    def convertMouseToGrid(self, mouseX, mouseY):
        #use closest grid position from mouse position unless it is outside the border

        self.x = ((mouseX - XMARGIN) - ((mouseX - XMARGIN)%BOXSIZE))/BOXSIZE
        if self.x not in range(0,BOARDWIDTH):
            self.x = -1 * BOXSIZE
        self.y = ((mouseY - TOPMARGIN) - ((mouseY - TOPMARGIN)%BOXSIZE))/BOXSIZE
        if self.y not in range(0,BOARDHEIGHT):
            self.y = -1 * BOXSIZE

    def getQuantity(self, quantity, board_quantity, x, y):

        new_quantity = (quantity + board_quantity) % MAXPIECERANGE
        if new_quantity == 0:
            return MAXPIECERANGE
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

    def new_current_piece(self, quantity, kind):
        self.quantity = quantity
        self.kind = kind
        self.x = -1 * BOXSIZE
        self.y = -1 * BOXSIZE
        self.onboard = False
        self.onblock = False

    def renderTile(self):
        pixelx = (XMARGIN + (self.x * BOXSIZE))
        pixely = (TOPMARGIN + (self.y * BOXSIZE))
        #draw background
        DISPLAYSURF.blit(BGIMAGE, (pixelx, pixely), (pixelx, pixely, BOXSIZE, BOXSIZE))
        for random_piece in self.random_pieces:
            if random_piece == 'blocked':
                continue
            if random_piece['coords'] == (self.x, self.y):
                seed = random_piece['seed']
                # draw random box back ontop
                if seed == False:
                    RANDOMBLOCKRECT.topleft = pixelx, pixely
                    DISPLAYSURF.blit(RANDOMBLOCKIMAGE, RANDOMBLOCKRECT)
                if seed == (self.x-1,self.y):
                    # w
                    RANDOMBLOCKWRECT.topleft = pixelx, pixely
                    DISPLAYSURF.blit(RANDOMBLOCKWIMAGE, RANDOMBLOCKWRECT)
                elif seed == (self.x+1,self.y):
                    # E
                    RANDOMBLOCKERECT.topleft = pixelx, pixely
                    DISPLAYSURF.blit(RANDOMBLOCKEIMAGE, RANDOMBLOCKERECT)
                elif seed == (self.x,self.y-1):
                    # N
                    RANDOMBLOCKNRECT.topleft = pixelx, pixely
                    DISPLAYSURF.blit(RANDOMBLOCKNIMAGE, RANDOMBLOCKNRECT)
                elif seed == (self.x,self.y+1):
                    # S
                    RANDOMBLOCKSRECT.topleft = pixelx, pixely
                    DISPLAYSURF.blit(RANDOMBLOCKSIMAGE, RANDOMBLOCKSRECT)
                break

        quantity = self.getQuantity(self.quantity, self.board[self.x][self.y]['quantity'], self.x, self.y)
        boxImage, boxRect = GETCURRENTPIECEIMAGEVARIABLE['{}_{}'.format(quantity, self.kind)]
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
    ONETHISIMAGE, ONETHISRECT, TWOTHISIMAGE, TWOTHISRECT,\
    THREETHISIMAGE, THREETHISRECT, FOURTHISIMAGE, FOURTHISRECT,\
    ONETHATIMAGE, ONETHATRECT, TWOTHATIMAGE, TWOTHATRECT,\
    THREETHATIMAGE, THREETHATRECT, FOURTHATIMAGE, FOURTHATRECT,\
    ONEOTHERIMAGE, ONEOTHERRECT, TWOOTHERIMAGE, TWOOTHERRECT,\
    THREEOTHERIMAGE, THREEOTHERRECT, FOUROTHERIMAGE, FOUROTHERRECT,\
    CURRENTONETHISIMAGE, CURRENTONETHISRECT, CURRENTTWOTHISIMAGE, CURRENTTWOTHISRECT,\
    CURRENTTHREETHISIMAGE, CURRENTTHREETHISRECT, CURRENTFOURTHISIMAGE, CURRENTFOURTHISRECT,\
    CURRENTONETHATIMAGE, CURRENTONETHATRECT, CURRENTTWOTHATIMAGE, CURRENTTWOTHATRECT,\
    CURRENTTHREETHATIMAGE, CURRENTTHREETHATRECT, CURRENTFOURTHATIMAGE, CURRENTFOURTHATRECT,\
    CURRENTONEOTHERIMAGE, CURRENTONEOTHERRECT, CURRENTTWOOTHERIMAGE, CURRENTTWOOTHERRECT,\
    CURRENTTHREEOTHERIMAGE, CURRENTTHREEOTHERRECT, CURRENTFOUROTHERIMAGE, CURRENTFOUROTHERRECT,\
    RANDOMONETHISIMAGE, RANDOMONETHISRECT, RANDOMTWOTHISIMAGE, RANDOMTWOTHISRECT,\
    RANDOMTHREETHISIMAGE, RANDOMTHREETHISRECT, RANDOMFOURTHISIMAGE, RANDOMFOURTHISRECT,\
    RANDOMONETHATIMAGE, RANDOMONETHATRECT, RANDOMTWOTHATIMAGE, RANDOMTWOTHATRECT,\
    RANDOMTHREETHATIMAGE, RANDOMTHREETHATRECT, RANDOMFOURTHATIMAGE, RANDOMFOURTHATRECT,\
    RANDOMONEOTHERIMAGE, RANDOMONEOTHERRECT, RANDOMTWOOTHERIMAGE, RANDOMTWOOTHERRECT,\
    RANDOMTHREEOTHERIMAGE, RANDOMTHREEOTHERRECT, RANDOMFOUROTHERIMAGE, RANDOMFOUROTHERRECT,\
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
    ONETHISIMAGE, ONETHISRECT = load_png('1_This.png')
    TWOTHISIMAGE, TWOTHISRECT = load_png('2_This.png')
    THREETHISIMAGE, THREETHISRECT = load_png('3_This.png')
    FOURTHISIMAGE, FOURTHISRECT = load_png('4_This.png')
    ONETHATIMAGE, ONETHATRECT = load_png('1_That.png')
    TWOTHATIMAGE, TWOTHATRECT = load_png('2_That.png')
    THREETHATIMAGE, THREETHATRECT = load_png('3_That.png')
    FOURTHATIMAGE, FOURTHATRECT = load_png('4_That.png')
    ONEOTHERIMAGE, ONEOTHERRECT = load_png('1_Other.png')
    TWOOTHERIMAGE, TWOOTHERRECT = load_png('2_Other.png')
    THREEOTHERIMAGE, THREEOTHERRECT = load_png('3_Other.png')
    FOUROTHERIMAGE, FOUROTHERRECT = load_png('4_Other.png')
    CURRENTONETHISIMAGE, CURRENTONETHISRECT = load_png('current_one_This.png')
    CURRENTTWOTHISIMAGE, CURRENTTWOTHISRECT = load_png('current_two_This.png')
    CURRENTTHREETHISIMAGE, CURRENTTHREETHISRECT = load_png('current_three_This.png')
    CURRENTFOURTHISIMAGE, CURRENTFOURTHISRECT = load_png('current_four_This.png')
    CURRENTONETHATIMAGE, CURRENTONETHATRECT = load_png('current_one_That.png')
    CURRENTTWOTHATIMAGE, CURRENTTWOTHATRECT = load_png('current_two_That.png')
    CURRENTTHREETHATIMAGE, CURRENTTHREETHATRECT = load_png('current_three_That.png')
    CURRENTFOURTHATIMAGE, CURRENTFOURTHATRECT = load_png('current_four_That.png')
    CURRENTONEOTHERIMAGE, CURRENTONEOTHERRECT = load_png('current_one_Other.png')
    CURRENTTWOOTHERIMAGE, CURRENTTWOOTHERRECT = load_png('current_two_Other.png')
    CURRENTTHREEOTHERIMAGE, CURRENTTHREEOTHERRECT = load_png('current_three_Other.png')
    CURRENTFOUROTHERIMAGE, CURRENTFOUROTHERRECT = load_png('current_four_Other.png')
    RANDOMONETHISIMAGE, RANDOMONETHISRECT = load_png('random_one_This.png')
    RANDOMTWOTHISIMAGE, RANDOMTWOTHISRECT = load_png('random_two_This.png')
    RANDOMTHREETHISIMAGE, RANDOMTHREETHISRECT = load_png('random_three_This.png')
    RANDOMFOURTHISIMAGE, RANDOMFOURTHISRECT = load_png('random_four_This.png')
    RANDOMONETHATIMAGE, RANDOMONETHATRECT = load_png('random_one_That.png')
    RANDOMTWOTHATIMAGE, RANDOMTWOTHATRECT = load_png('random_two_That.png')
    RANDOMTHREETHATIMAGE, RANDOMTHREETHATRECT = load_png('random_three_That.png')
    RANDOMFOURTHATIMAGE, RANDOMFOURTHATRECT = load_png('random_four_That.png')
    RANDOMONEOTHERIMAGE, RANDOMONEOTHERRECT = load_png('random_one_Other.png')
    RANDOMTWOOTHERIMAGE, RANDOMTWOOTHERRECT = load_png('random_two_Other.png')
    RANDOMTHREEOTHERIMAGE, RANDOMTHREEOTHERRECT = load_png('random_three_Other.png')
    RANDOMFOUROTHERIMAGE, RANDOMFOUROTHERRECT = load_png('random_four_Other.png')
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
                                '1_This':(CURRENTONETHISIMAGE, CURRENTONETHISRECT),
                                '2_This':(CURRENTTWOTHISIMAGE, CURRENTTWOTHISRECT),
                                '3_This':(CURRENTTHREETHISIMAGE, CURRENTTHREETHISRECT),
                                '4_This':(CURRENTFOURTHISIMAGE, CURRENTFOURTHISRECT),
                                '1_That':(CURRENTONETHATIMAGE, CURRENTONETHATRECT),
                                '2_That':(CURRENTTWOTHATIMAGE, CURRENTTWOTHATRECT),
                                '3_That':(CURRENTTHREETHATIMAGE, CURRENTTHREETHATRECT),
                                '4_That':(CURRENTFOURTHATIMAGE, CURRENTFOURTHATRECT),
                                '1_Other':(CURRENTONEOTHERIMAGE, CURRENTONEOTHERRECT),
                                '2_Other':(CURRENTTWOOTHERIMAGE, CURRENTTWOOTHERRECT),
                                '3_Other':(CURRENTTHREEOTHERIMAGE, CURRENTTHREEOTHERRECT),
                                '4_Other':(CURRENTFOUROTHERIMAGE, CURRENTFOUROTHERRECT)
                                }

    GETPIECEIMAGEVARIABLE = {
                            '1_This':(ONETHISIMAGE, ONETHISRECT),
                            '2_This':(TWOTHISIMAGE, TWOTHISRECT),
                            '3_This':(THREETHISIMAGE, THREETHISRECT),
                            '4_This':(FOURTHISIMAGE, FOURTHISRECT),
                            '1_That':(ONETHATIMAGE, ONETHATRECT),
                            '2_That':(TWOTHATIMAGE, TWOTHATRECT),
                            '3_That':(THREETHATIMAGE, THREETHATRECT),
                            '4_That':(FOURTHATIMAGE, FOURTHATRECT),
                            '1_Other':(ONEOTHERIMAGE, ONEOTHERRECT),
                            '2_Other':(TWOOTHERIMAGE, TWOOTHERRECT),
                            '3_Other':(THREEOTHERIMAGE, THREEOTHERRECT),
                            '4_Other':(FOUROTHERIMAGE, FOUROTHERRECT)
                            }

    GETRANDOMPIECEIMAGEVARIABLE = {
                                '1_This':(RANDOMONETHISIMAGE, RANDOMONETHISRECT),
                                '2_This':(RANDOMTWOTHISIMAGE, RANDOMTWOTHISRECT),
                                '3_This':(RANDOMTHREETHISIMAGE, RANDOMTHREETHISRECT),
                                '4_This':(RANDOMFOURTHISIMAGE, RANDOMFOURTHISRECT),
                                '1_That':(RANDOMONETHATIMAGE, RANDOMONETHATRECT),
                                '2_That':(RANDOMTWOTHATIMAGE, RANDOMTWOTHATRECT),
                                '3_That':(RANDOMTHREETHATIMAGE, RANDOMTHREETHATRECT),
                                '4_That':(RANDOMFOURTHATIMAGE, RANDOMFOURTHATRECT),
                                '1_Other':(RANDOMONEOTHERIMAGE, RANDOMONEOTHERRECT),
                                '2_Other':(RANDOMTWOOTHERIMAGE, RANDOMTWOOTHERRECT),
                                '3_Other':(RANDOMTHREEOTHERIMAGE, RANDOMTHREEOTHERRECT),
                                '4_Other':(RANDOMFOUROTHERIMAGE, RANDOMFOUROTHERRECT)
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
