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
# BLANK = '.'

LEFT = 1
RIGHT = 3

PIECERANGE = range(1,5)
RANDOMCOUNT_VAR = -1
RANDOMSEQUENCE = [2, 2, 3, 4]
cycles = {}
randomlist = []
MAXCYCLE = 10

XMARGIN = (WINDOWWIDTH - (BOARDWIDTH * BOXSIZE))/2
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

    def render(self, DISPLAYSURF):
        #display title screen
        TITLERECT.topleft = 0,0
        DISPLAYSURF.blit(TITLE, TITLERECT)

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

        self.altered = []
        cycles = {}

        #randomlist is a list of 4 time the piece range randomised, this prevents
        #strings random numbers which feel to unlikely, allows the player to
        #try and predict what is coming
        randomlist = random.sample(4 * PIECERANGE, len(4 * PIECERANGE))

        self.possible_random_spaces= []
        self.board = Board(self.altered, self.possible_random_spaces)
        self.board_surface = pygame.Surface((WINDOWWIDTH, WINDOWHEIGHT), pygame.SRCALPHA)
        self.board_surface.blit(BGIMAGE, (XMARGIN, TOPMARGIN), (XMARGIN, TOPMARGIN, BOXSIZE * BOARDWIDTH, BOXSIZE * BOARDHEIGHT))
        self.board_rect = self.board_surface.get_rect()
        self.Overlay = Overlay(self.board_surface)
        self.phase = 0
        self.update_countdown = False
        self.draw_current_piece = False
        self.random_pieces = []
        self.random_count = -1
        self.altered = []
        self.getRandom(RANDOMSEQUENCE[0] + 1)
        self.altered = []
        self.draw_random = False
        if len(randomlist) < 1:
            randomlist = random.sample(4 * PIECERANGE, len(4 * PIECERANGE))
        self.currentPiece  = CurrentPiece(self.board_surface, self.board.board, randomlist.pop(0))

        self.status = Status(0)
        DISPLAYSURF.blit(BGIMAGE, BGRECT)
        for x in range(BOARDWIDTH):
            for y in range(BOARDHEIGHT):
                self.drawBox(x, y, self.board.board[x][y])
        first = True
        for random_dict in self.random_pieces:
            if first is True:
                first = False
                self.drawRandomPiece(random_dict['coords'], random_dict['quantity'], True)
            # coord, quantity
            else:
                self.drawRandomPiece(random_dict['coords'], random_dict['quantity'], False)
        DISPLAYSURF.blit(self.board_surface, self.board_rect)
        self.status.render()
        self.drawCurrentPiece()
        pygame.display.flip()

    def render(self, DISPLAYSURF):
        if self.altered != []:
            #draw base and tile of each coordinate
            for coordinate in self.altered:
                pixelx, pixely = self.convertToPixelCoords(coordinate[0], coordinate[1])
                self.board_surface.blit(BGIMAGE, (pixelx, pixely), (pixelx, pixely, BOXSIZE, BOXSIZE))
                self.drawBox(coordinate[0], coordinate[1], self.board.board[coordinate[0]][coordinate[1]])
            #update display surface
            first = True
            for random_dict in self.random_pieces:
                if first is True:
                    first = False
                    if random_dict == False:
                        continue
                    self.drawRandomPiece(random_dict['coords'], random_dict['quantity'], True)
                # coord, quantity
                else:
                    if random_dict == False:
                        continue
                    self.drawRandomPiece(random_dict['coords'], random_dict['quantity'], False)
            """for block in self.blocks:
                if block[0] in self.altered:
                    self.drawNextBlock(block[0], block[1])"""
            if self.update_countdown == True:
                self.draw_countdown()
                self.update_countdown = False
            DISPLAYSURF.blit(self.board_surface, self.board_rect)
        self.Overlay.render(self.altered)
        self.currentPiece.render()
        if self.status.score_changed == True:
            #draw score, bar and to next clear
            self.status.render()
            self.status.score_changed = False
        if self.draw_current_piece == True:
            self.drawCurrentPiece()
            self.draw_current_piece = False

    def update(self):
        pass

    def handle_events(self, events):

        global randomlist
        self.altered = []
        for event in events: # event handling loop
            if event.type == MOUSEMOTION:
                mouseX, mouseY = event.pos
                self.currentPiece.convertMouseToGrid(mouseX, mouseY)
                self.currentPiece.isValidPosition()
                self.checkCurrentPiece()
            elif event.type == pygame.MOUSEBUTTONUP and event.button == LEFT:
                if self.currentPiece.onboard == True and self.currentPiece.onpiece == False:
                    self.addToBoard()
                    self.draw_current_piece = True
                    # check if full before doing any more work
                    if self.board.fullBoard():
                        self.manager.go_to(GameOverScene())
                    self.currentPiece.oldOnpiece = True
                    self.currentPiece.onpiece =True
                    if randomlist == []:
                        randomlist = random.sample(4 * PIECERANGE, len(4 * PIECERANGE))
                    self.currentPiece.new_current_piece(randomlist.pop(0), 1)

    def addCycle(self, (x,y)):
        global cycles

        block = self.board.board[x][y]['block']
        cycle = self.board.board[x][y]['cycle']

        if self.board.board[x][y]['block'] > 0:
            self.board.board[x][y]['block'] -= 1
        elif self.board.board[x][y]['cycle'] == MAXCYCLE:
            return
        else:
            self.board.board[x][y]['cycle'] += 1

    def addToBoard(self):
        global cycles
        print len(self.random_pieces)
        # fill in the board based on piece's location, quantity, and rotation
        self.exponent_base = 0
        self.scored = []
        self.update_countdown = True
        self.to_investigate = [(self.currentPiece.x,self.currentPiece.y)]
        self.board.board[self.currentPiece.x][self.currentPiece.y] = {
            'blank':False, 'seed_cycle':False,
            'quantity':self.currentPiece.quantity,
            'cycle':self.currentPiece.cycle, 'block': 0
        }
        self.altered.append((self.currentPiece.x,self.currentPiece.y))
        for x in range(self.currentPiece.x-1, self.currentPiece.x+2):
            for y in range(self.currentPiece.y-1, self.currentPiece.y+2):
                if x in range(0,BOARDWIDTH) and y in range(0,BOARDHEIGHT):
                    if (x, y) != (self.currentPiece.x, self.currentPiece.y):
                        if self.board.board[x][y]['blank'] is False:
                            self.altered.append((x,y))
                            self.to_investigate.append((x,y))
                            quantity = self.board.board[x][y]['quantity']
                            cycle = self.board.board[x][y]['cycle']
                            new_quantity = (quantity + self.currentPiece.quantity) % max(PIECERANGE)
                            if new_quantity == 0:
                                if quantity == max(PIECERANGE):
                                    if cycle == MAXCYCLE:
                                        self.board.board[x][y]['quantity'] = max(PIECERANGE)
                                    else:
                                        self.board.board[x][y]['quantity'] = max(PIECERANGE)
                                        self.addCycle((x,y))
                                else:
                                    self.board.board[x][y]['quantity'] = max(PIECERANGE)
                            elif new_quantity == quantity:
                                if cycle == MAXCYCLE:
                                    self.board.board[x][y]['quantity'] = new_quantity
                                else:
                                    self.board.board[x][y]['quantity'] = new_quantity
                                    self.addCycle((x,y))
                            elif new_quantity < quantity:
                                if cycle == MAXCYCLE:
                                    self.board.board[x][y]['quantity'] = new_quantity
                                else:
                                    self.board.board[x][y]['quantity'] = new_quantity
                                    self.addCycle((x,y))
                            else:
                                self.board.board[x][y]['quantity'] = new_quantity
        self.draw_placed([(self.currentPiece.x,self.currentPiece.y)])
        self.checkRemove()

        # add random pieces
        self.to_investigate = []
        # check if any false values in random pieces
        # if so check grid and add any additionals to random pieces
        for random_piece in self.random_pieces:
            if random_piece is False:
                self.checkForFalseRandoms()
                break
        # for each random check if can still be placed, if so add
        placed = 0
        to_place = RANDOMSEQUENCE[self.phase]
        clear_random_pieces = False
        for n in range(len(self.random_pieces) -1, -1, -1):
            random_piece = self.random_pieces[n]
            if random_piece is False:
                continue
            (x,y) = random_piece['coords']
            if (x,y) == (self.currentPiece.x,self.currentPiece.y):
                continue
            seed_list = random_piece['seed_list']
            for (s_x,s_y) in seed_list:
                if self.board.board[s_x][s_y]['blank'] is False:
                    quantity = random_piece['quantity']
                    cycle = random_piece['cycle']
                    block = random_piece['block']
                    self.board.board[x][y] = {
                        'blank':False, 'seed_cycle':False,
                        'quantity': quantity,
                        'cycle': cycle, 'block': block
                    }
                    placed += 1
                    self.appendCrossToInvestigate((x,y))
                    break
            if placed == to_place:
                if n == 0:
                    clear_random_pieces = True
                break
        placed_coords = []
        for random_piece in self.random_pieces:
            if random_piece is not False:
                if random_piece['coords'] != (self.currentPiece.x,self.currentPiece.y):
                    self.altered.append(random_piece['coords'])
                    placed_coords.append(random_piece['coords'])
        self.draw_placed(placed_coords)
        # check if current piece was placed on the bonus piece, or on a random piece
        # so bonus piece was used
        if clear_random_pieces == True:
            self.random_pieces = []
        elif self.random_pieces[0] == False:
            self.random_pieces = []
        elif self.random_pieces[0]['coords'] == (self.currentPiece.x,self.currentPiece.y):
            self.random_pieces = []
        else:
            self.random_pieces = self.random_pieces[0:1]

        # check around randoms for any removals
        self.checkRemove()

        #create new randoms
        cycles = {}
        for x in range(0,BOARDWIDTH):
            for y in range(0,BOARDHEIGHT):
                if self.board.board[x][y]['blank'] is True:
                    self.board.getHighestCycle((x,y))

        self.phase += 1
        if self.phase >= len(RANDOMSEQUENCE):
            self.phase = 0
        randomlength = RANDOMSEQUENCE[self.phase] + 1 - len(self.random_pieces)
        print "getting random len {}".format(randomlength)
        self.getRandom(randomlength)

        # work out the displaying of scoring
        # get base score by finding total number of tiles removed
        score_base = 0
        for score_level in self.scored:
            score_base += len(score_level)

        for score_level in self.scored:
            for score_item in score_level:
                (x,y) = score_item[0]
                exponent = score_item[1]
                self.status.score_changed = True
                #self.status.score += (2 ** self.exponent)
                score_increase = score_base ** exponent
                self.status.score += score_increase
                #self.status.score += (5 ** self.exponent)
                pixelx, pixely = self.convertToPixelCoords(x, y)
                #exponent_score_surf = COUNTFONT.render('{}'.format(str((2 ** self.exponent))), True, TEXTCOLOR)
                exponent_score_surf = COUNTFONT.render('{}'.format(str((score_increase))), True, TEXTCOLOR)
                exponent_score_rect = exponent_score_surf.get_rect()
                exponent_score_rect.center = (pixelx+(BOXSIZE/2), pixely+(BOXSIZE/2))
                min_x = exponent_score_rect.left
                min_y = exponent_score_rect.top
                width  = exponent_score_rect.width
                height = exponent_score_rect.height
                self.Overlay.score_overlays.append([1 * FPS, exponent_score_surf, exponent_score_rect, [min_x, min_y, width, height]])
                self.board_surface.blit(BGIMAGE, (pixelx, pixely), (pixelx, pixely, BOXSIZE, BOXSIZE))
                self.drawBox(x, y, self.board.board[x][y])
                for score_overlay in self.Overlay.score_overlays:
                    DISPLAYSURF.blit(score_overlay[1], score_overlay[2])
            pygame.display.flip()
            pygame.time.delay(500)
        for random_piece in self.random_pieces:
            if random_piece is not False:
                self.altered.append(random_piece['coords'])

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
        if count == quantity:
            return True
        else:
            return False

    def checkCurrentPiece(self):
        if self.currentPiece.oldgrid != (self.currentPiece.x, self.currentPiece.y):
            if self.currentPiece.x in range(0,BOARDWIDTH) and self.currentPiece.y in range(0,BOARDHEIGHT) and self.currentPiece.onpiece == False:
                self.currentPiece.draw_current_piece = True
            if self.currentPiece.oldgrid[0] in range(0,BOARDWIDTH) and self.currentPiece.oldgrid[1] in range(0,BOARDHEIGHT) and self.currentPiece.oldOnpiece == False:
                if (self.currentPiece.oldgrid[0], self.currentPiece.oldgrid[1]) not in self.altered:
                     pixelx, pixely = self.convertToPixelCoords(self.currentPiece.oldgrid[0], self.currentPiece.oldgrid[1])
                     self.currentPiece.draw_old_current_piece.append((pixelx, pixely))
            self.currentPiece.oldgrid = (self.currentPiece.x, self.currentPiece.y)

    def checkForFalseRandoms(self):
        """
        Fill in False entries in random_pieces with any places which have
        been removed.
        Do this by clearing cycles then search board for blanks which are
        not the coord of a random piece, if foun add to cycles then fill in
        random_pieces using getRandom
        """

        global cycles
        cycles = {}
        false_count = 0
        random_coordinates = []
        possible_blanks = []
        # {'coords': BOARDCENTRE, 'quantity': randomlist.pop(0), 'cycle':1, 'block': 2, 'seed_list':False}
        for random_piece in self.random_pieces:
            if random_piece is False:
                false_count += 1
            else:
                random_coordinates.append(random_piece['coords'])

        # remove all entries of false so can be overwritten
        self.random_pieces = [val for val in  self.random_pieces if val is not False]

        for x in range(0,BOARDWIDTH):
            for y in range(0,BOARDHEIGHT):
                if self.board.board[x][y]['blank'] is True:
                    if (x,y) in random_coordinates:
                        continue
                    else:
                        self.board.getHighestCycle((x,y))

        self.getRandom(false_count)


    def checkRemove(self):

        checking = True
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
                max_removed = []
                for (x,y) in to_remove:
                    # for all the pieces around it add 1 to cycles
                    if x-1 in range(0,BOARDWIDTH):
                        if self.board.board[x-1][y]['blank'] is False:
                            self.addCycle((x-1, y))
                    if x+1 in range(0,BOARDWIDTH):
                        if self.board.board[x+1][y]['blank'] is False:
                            self.addCycle((x+1, y))
                    if y-1 in range(0,BOARDHEIGHT):
                        if self.board.board[x][y-1]['blank'] is False:
                            self.addCycle((x, y-1))
                    if y+1 in range(0,BOARDHEIGHT):
                        if self.board.board[x][y+1]['blank'] is False:
                            self.addCycle((x, y+1))
                self.scored.append([])
                #score_increase = self.getScoreIncrease(self.exponent)
                self.to_investigate = []
                for (x,y) in to_remove:
                    self.exponent_base += 1
                    self.altered.append((x,y))
                    cycle = self.board.board[x][y]['cycle']
                    if cycle == MAXCYCLE:
                        if cycle not in max_removed:
                            max_removed.append(cycle)
                    self.scored[-1].append([(x,y), cycle])
                    self.board.board[x][y] = BLANK
                    self.status.score_changed = True
                for (x,y) in to_remove:
                    self.appendCrossToInvestigate((x,y))

    def convertToPixelCoords(self, boxx, boxy):
        # Convert the given xy coordinates of the board to xy
        # coordinates of the location on the screen.
        return (XMARGIN + (boxx * BOXSIZE)), (TOPMARGIN + (boxy * BOXSIZE))

    def draw_countdown(self):
        length = 1 - (float((1 + self.phase))/len(RANDOMSEQUENCE))
        self.board_surface.blit(BGIMAGE, (27, 506), (27, 506, 346, 5))
        self.board_surface.blit(BARIMAGE, (27, 506), (0, 0, int(length * 346), 5))

    def drawCurrentPiece(self):
        # draw the "next" piece
        DISPLAYSURF.blit(BGIMAGE, (100, 391), (100, 391, BOXSIZE, BOXSIZE))
        boxImage, boxRect = GETPIECEIMAGEVARIABLE['{}_{}'.format(self.currentPiece.quantity, self.currentPiece.cycle)]
        boxRect.topleft = 100, 391
        DISPLAYSURF.blit(boxImage, boxRect)

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
        for score_overlay in self.Overlay.score_overlays:
                DISPLAYSURF.blit(score_overlay[1], score_overlay[2])
        #pygame.display.flip()

    def drawRandomPiece(self, (x,y), quantity, extra_piece):
        pixelx, pixely = self.convertToPixelCoords(x, y)
        if self.board.board[x][y]['blank'] is True:
            boxImage, boxRect = GETRANDOMPIECEIMAGEVARIABLE['{}_{}'.format(quantity, extra_piece)]
            boxRect.topleft = pixelx, pixely
            self.board_surface.blit(boxImage, boxRect)
        if extra_piece is False:
            RANDOMBLOCKRECT.topleft = pixelx, pixely
            self.board_surface.blit(RANDOMBLOCKIMAGE, RANDOMBLOCKRECT)
        else:
            RANDOMBLOCKNEXTRECT.topleft = pixelx, pixely
            self.board_surface.blit(RANDOMBLOCKNEXTIMAGE, RANDOMBLOCKNEXTRECT)

    def getRandom(self, randomlength):
        global cycles
        global randomlist

        self.draw_random_position = True

        if len(randomlist) < randomlength:
            randomlist.extend(random.sample(4 * PIECERANGE, len(4 * PIECERANGE)))
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
                self.random_pieces = [{'coords': BOARDCENTRE, 'quantity': randomlist.pop(0), 'cycle':1, 'block': 2, 'seed_list':False}]
                #self.altered.append(BOARDCENTRE)
                for n in range(0, randomlength - 1):
                    self.random_pieces.insert(0, False)
            else:
                # there is pieces in the randomlist but no more random options to add
                for n in range(0, randomlength):
                    self.random_pieces.insert(0, False)
            return

        current_random_coords = []
        for random_piece in self.random_pieces:
            current_random_coords.append(random_piece['coords'])

        # length_required = randomlength - len(self.random_pieces)
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
                seeds = cycles_list[n][1]
                self.random_pieces.insert(0, {
                                            'coords': coord,
                                            'quantity': randomlist.pop(0),
                                            'cycle':1,
                                            'block': 2,
                                            'seed_list': seeds
                                          })
                # self.altered.append(coord)
                length_required -= 1
                if length_required == 0:
                    break
            key += 1
            if key >= len(cycles_keys):
                for n in range(0, length_required):
                    self.random_pieces.insert(0, False)
                    length_required -= 1
                    if length_required == 0:
                        break

class GameOverScene(object):
    def __init__(self):
        super(GameOverScene, self).__init__()

        #display game over text
        s = pygame.Surface((WINDOWWIDTH, WINDOWHEIGHT))
        s.set_alpha(128)                # alpha level
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
    def __init__(self, altered, possible_random_spaces):
        global cycles

        self.altered = altered
        self.possible_random_spaces = possible_random_spaces

        self.board = []

        #create board
        for i in range(BOARDWIDTH):
            self.board.append([BLANK] * BOARDHEIGHT)
        self.createBoard()

    """def appendCycles(self, (x,y)):
        if (x-1 in range(0,BOARDWIDTH) and self.board[x-1][y]['blank'] is True):
            self.getHighestCycle((x-1,y))
        if (x+1 in range(0,BOARDWIDTH) and self.board[x+1][y]['blank'] is True):
            self.getHighestCycle((x+1,y))
        if (y-1 in range(0,BOARDHEIGHT) and self.board[x][y-1]['blank'] is True):
            self.getHighestCycle((x,y-1))
        if (y+1 in range(0,BOARDHEIGHT) and self.board[x][y+1]['blank'] is True):
            self.getHighestCycle((x,y+1))
    """

    def createBoard(self):
        global cycles
        global randomlist
        fills = self.getMiddle()

        #mat.ceil is rounding up
        boardsize = BOARDWIDTH * BOARDHEIGHT
        quarter_size = math.ceil(boardsize/4.0)
        # plus 1 for middle
        if len(randomlist) < (quarter_size + 1):
            sets_needed = math.ceil((quarter_size + 1 - len(randomlist)) / 4.0)
            randomlist.extend(shuffle(sets_needed * PIECERANGE))

        quarter_size_count = math.ceil(boardsize/4.0) - 5
        while quarter_size_count > 0:
            (x,y), seeds = cycles['1'].pop(0)
            fills.append((x,y))
            # original pieces do not have blocks
            self.board[x][y] = {'blank':False, 'seed_cycle':False, 'quantity':1, 'cycle':1, 'block': 0}
            # self.appendCycles((x,y))
            # self.appendRandomSpaces((x,y), self.possible_random_spaces)
            quarter_size_count -= 1
            if len(cycles['1']) == 0:
                self.getCycles()

        for (x,y) in fills:
            non_quantity = self.getTileValue((x, y))
            quantity = randomlist[0]
            if quantity != non_quantity:
                randomlist.pop(0)
            else:
                n = 0
                while quantity == non_quantity:
                    n += 1
                    if len(randomlist) < (n - 1):
                        randomlist.extend(random.sample(4 * PIECERANGE, len(4 * PIECERANGE)))
                    if randomlist[n] != non_quantity:
                        quantity = randomlist.pop(n)
            self.board[x][y]['quantity'] = quantity

        # reset cycles  blanks for creating randoms
        self.getCycles()

    def fullBoard(self):
        for x in range(0,BOARDWIDTH):
            for y in range(0,BOARDHEIGHT):
                if self.board[x][y]['blank'] is True:
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

        """#check board to find out if in cycles, if so remove from cycles
        if self.board[x][y]['seed_cycle'] is not False:
            old_highest_cycle = self.board[x][y]['seed_cycle']
            cycle_list = cycles['{}'.format(old_highest_cycle)]
            for n in range(0, len(cycle_list)):
                if cycle_list[n][0] == (x,y):
                    cycles['{}'.format(old_highest_cycle)].pop(n)
                    break"""

        #then if cycles has key append, otherwise add
        if cycles.has_key('{}'.format(highest_cycle)):
            cycles['{}'.format(highest_cycle)].append([(x,y), seed_list])
            shuffle(cycles['{}'.format(highest_cycle)])
        else:
            cycles['{}'.format(highest_cycle)] = [[(x,y), seed_list]]

        self.board[x][y]['seed_cycle'] = highest_cycle

    def getMiddle(self):
        x = BOARDCENTRE[0]
        y = BOARDCENTRE[1]
        self.board[x][y] = {'blank':False, 'seed_cycle':False, 'quantity':1, 'cycle':1, 'block': 0}
        self.board[x-1][y] = {'blank':False, 'seed_cycle':False, 'quantity':1, 'cycle':1, 'block': 0}
        self.board[x+1][y] = {'blank':False, 'seed_cycle':False, 'quantity':1, 'cycle':1, 'block': 0}
        self.board[x][y-1] = {'blank':False, 'seed_cycle':False, 'quantity':1, 'cycle':1, 'block': 0}
        self.board[x][y+1] = {'blank':False, 'seed_cycle':False, 'quantity':1, 'cycle':1, 'block': 0}
        # self.appendCycles((x-1,y))
        # self.appendCycles((x+1,y))
        # self.appendCycles((x,y-1))
        # self.appendCycles((x,y+1))
        self.getCycles()
        return [(x,y), (x-1,y), (x+1,y), (x,y-1),(x,y+1)]


    def getTileValue(self, (x, y)):
        count = 0
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
        return count

    def removeCycle(self, (x,y), old_highest_cycle):
        #check board to find out if in cycles, if so remove from cycles
        # new
        # cycles['{}'.format(highest_cycle)].append(((x,y), seed_list))
        # shuffle(cycles['{}'.format(highest_cycle)])
        # old
        # if self.board[x][y]['seed_cycle'] is not False:
        #    old_highest_cycle = self.board[x][y]['seed_cycle']
        cycle_list = cycles['{}'.format(old_highest_cycle)]
        for n in range(0, len(cycle_list)):
            if cycle_list[n][0] == (x,y):
                cycles['{}'.format(old_highest_cycle)].pop(n)
                break

class CurrentPiece(object):
    #individual classes for story the next pieces
    def __init__(self, board_surface, board, quantity_val):
        self.quantity = quantity_val
        self.cycle = 1
        #self.quantity = random.choice(PIECERANGE)
        #self.quantity = 4
        self.x = -1 * BOXSIZE
        self.y = -1 * BOXSIZE
        self.onboard = False
        self.onpiece = False
        self.oldgrid = (-1 * BOXSIZE, -1 * BOXSIZE)
        self.oldOnpiece = False
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

    def isValidPosition(self):
        # Checks if the currentPiece is within the board and not ontop of another piece

        if  self.x >= 0 and self.x < BOARDWIDTH and self.y >= 0 and self.y < BOARDHEIGHT:
            self.onboard = True
            if self.board[self.x][self.y]['blank'] is False:
                self.oldOnpiece = self.onpiece
                self.onpiece = self.board[self.x][self.y]
            else:
                self.oldOnpiece = self.onpiece
                self.onpiece = False
        else:
            self.oldOnpiece = self.onpiece
            self.onboard = False
            self.onpiece = False

    def new_current_piece(self, quantity, cycle):
        self.quantity = quantity
        self.cycle = cycle
        self.x = -1 * BOXSIZE
        self.y = -1 * BOXSIZE
        self.onboard = False
        self.onpiece = False

    def render(self):
        if self.draw_current_piece == True:
            pixelx = (XMARGIN + (self.x * BOXSIZE))
            pixely = (TOPMARGIN + (self.y * BOXSIZE))
            DISPLAYSURF.blit(self.board_surface, (pixelx, pixely), (pixelx, pixely, BOXSIZE, BOXSIZE))
            boxImage, boxRect = GETCURRENTPIECEIMAGEVARIABLE['{}'.format(self.quantity)]
            boxRect.topleft = pixelx, pixely
            DISPLAYSURF.blit(boxImage, boxRect)
            self.draw_current_piece = False
        if self.draw_old_current_piece != []:
            for pixel_coordinates in self.draw_old_current_piece:
                DISPLAYSURF.blit(self.board_surface, (pixel_coordinates[0], pixel_coordinates[1]), (pixel_coordinates[0], pixel_coordinates[1], BOXSIZE, BOXSIZE))
            self.draw_old_current_piece = []

class Overlay(object):
    #class for recording and rendering scores, piece animations and other overlays
    def __init__(self, board_surface):
        self.piece_animations = []
        self.board_surface = board_surface
        # score overlays holds a countdown of 3 * FPS, scoreSurf, scoreRect, [pixelx, pixely, boxwidth, boxheight]
        self.score_overlays = []

    def render(self, alt_list):
        for piece_animation in self.piece_animations:
            pass
        score_ind = []
        for score_overlay in self.score_overlays:
            #first if board altered draw
            score_overlay[0] -= 1
            if score_overlay[0] <= 0:
                score_ind.append(self.score_overlays.index(score_overlay))
                DISPLAYSURF.blit(BGIMAGE, (score_overlay[3][0], score_overlay[3][1]), (score_overlay[3][0], score_overlay[3][1], score_overlay[3][2], score_overlay[3][3]))
                DISPLAYSURF.blit(self.board_surface, (score_overlay[3][0], score_overlay[3][1]), (score_overlay[3][0], score_overlay[3][1], score_overlay[3][2], score_overlay[3][3]))
            #second if board altered draw
            if alt_list != [] and score_overlay[0] > 0:
                DISPLAYSURF.blit(score_overlay[1], score_overlay[2])
        if score_ind != []:
            score_ind.sort(reverse=True)
            for index in score_ind:
                del self.score_overlays[index]

class Status(object):
    #class for displaying score and matches
    def __init__(self,score=0):
        self.score = score
        scoreSurf = COUNTFONT.render('%s' % self.score, True, TEXTCOLOR)
        scoreRect = scoreSurf.get_rect()
        scoreRect.center = ((WINDOWWIDTH/2), 555)
        self.oldScoreRect = scoreRect
        self.score_changed = True

    #Displays the current score and matches on the screen
    def render(self):
        scoreSurf = COUNTFONT.render('%s' % self.score, True, TEXTCOLOR)
        scoreRect = scoreSurf.get_rect()
        scoreRect.center = ((WINDOWWIDTH/2), 555)
        unionRect = scoreRect.union(self.oldScoreRect)
        DISPLAYSURF.blit(BGIMAGE, unionRect, unionRect)
        DISPLAYSURF.blit(scoreSurf, scoreRect)
        self.oldScoreRect = scoreRect

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
    CURRENTONEIMAGE, CURRENTONERECT, CURRENTTWOIMAGE, CURRENTTWORECT,\
    CURRENTTHREEIMAGE, CURRENTTHREERECT, CURRENTFOURIMAGE, CURRENTFOURRECT,\
    RANDOMONEIMAGE, RANDOMONERECT, RANDOMTWOIMAGE, RANDOMTWORECT,\
    RANDOMTHREEIMAGE, RANDOMTHREERECT, RANDOMFOURIMAGE, RANDOMFOURRECT,\
    RANDOMBLOCKIMAGE, RANDOMBLOCKRECT,\
    RANDOMONENEXTIMAGE, RANDOMONENEXTRECT, RANDOMTWONEXTIMAGE, RANDOMTWONEXTRECT,\
    RANDOMTHREENEXTIMAGE, RANDOMTHREENEXTRECT, RANDOMFOURNEXTIMAGE, RANDOMFOURNEXTRECT,\
    RANDOMBLOCKNEXTIMAGE, RANDOMBLOCKNEXTRECT,\
    BARIMAGE, BARRECT,\
    BLOCKONEIMAGE, BLOCKONERECT, BLOCKTWOIMAGE, BLOCKTWORECT, \
    GETBLOCKIMAGEVARIABLE, GETCURRENTPIECEIMAGEVARIABLE,\
    GETPIECEIMAGEVARIABLE, GETRANDOMPIECEIMAGEVARIABLE

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
    CURRENTONEIMAGE, CURRENTONERECT = load_png('current_one.png')
    CURRENTTWOIMAGE, CURRENTTWORECT = load_png('current_two.png')
    CURRENTTHREEIMAGE, CURRENTTHREERECT = load_png('current_three.png')
    CURRENTFOURIMAGE, CURRENTFOURRECT = load_png('current_four.png')
    RANDOMONEIMAGE, RANDOMONERECT = load_png('random_one.png')
    RANDOMTWOIMAGE, RANDOMTWORECT = load_png('random_two.png')
    RANDOMTHREEIMAGE, RANDOMTHREERECT = load_png('random_three.png')
    RANDOMFOURIMAGE, RANDOMFOURRECT = load_png('random_four.png')
    RANDOMBLOCKIMAGE, RANDOMBLOCKRECT = load_png('random_block.png')
    RANDOMONENEXTIMAGE, RANDOMONENEXTRECT = load_png('random_one_next.png')
    RANDOMTWONEXTIMAGE, RANDOMTWONEXTRECT = load_png('random_two_next.png')
    RANDOMTHREENEXTIMAGE, RANDOMTHREENEXTRECT = load_png('random_three_next.png')
    RANDOMFOURNEXTIMAGE, RANDOMFOURNEXTRECT = load_png('random_four_next.png')
    RANDOMBLOCKNEXTIMAGE, RANDOMBLOCKNEXTRECT = load_png('random_block_next.png')
    BARIMAGE, BARRECT = load_png('bar.png')
    BLOCKONEIMAGE, BLOCKONERECT = load_png('block_one.png')
    BLOCKTWOIMAGE, BLOCKTWORECT = load_png('block_two.png')

    GETBLOCKIMAGEVARIABLE = {
                            '1':(BLOCKONEIMAGE, BLOCKONERECT),
                            '2':(BLOCKTWOIMAGE, BLOCKTWORECT)
                            }

    GETCURRENTPIECEIMAGEVARIABLE = {
                                '1':(CURRENTONEIMAGE, CURRENTONERECT),
                                '2':(CURRENTTWOIMAGE, CURRENTTWORECT),
                                '3':(CURRENTTHREEIMAGE, CURRENTTHREERECT),
                                '4':(CURRENTFOURIMAGE, CURRENTFOURRECT)
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
                            '4_10':(FOURTENIMAGE, FOURTENRECT)
                            }

    GETRANDOMPIECEIMAGEVARIABLE = {
                                '1_False':(RANDOMONEIMAGE, RANDOMONERECT),
                                '2_False':(RANDOMTWOIMAGE, RANDOMTWORECT),
                                '3_False':(RANDOMTHREEIMAGE, RANDOMTHREERECT),
                                '4_False':(RANDOMFOURIMAGE, RANDOMFOURRECT),
                                '1_True':(RANDOMONENEXTIMAGE, RANDOMONENEXTRECT),
                                '2_True':(RANDOMTWONEXTIMAGE, RANDOMTWONEXTRECT),
                                '3_True':(RANDOMTHREENEXTIMAGE, RANDOMTHREENEXTRECT),
                                '4_True':(RANDOMFOURNEXTIMAGE, RANDOMFOURNEXTRECT)
                                }

    manager = SceneMananger()

    while True:
        checkForQuit()
        manager.scene.handle_events(pygame.event.get())
        manager.scene.update()
        manager.scene.render(DISPLAYSURF)
        pygame.display.flip()
        FPSCLOCK.tick(FPS)

if __name__ == '__main__':
    main()