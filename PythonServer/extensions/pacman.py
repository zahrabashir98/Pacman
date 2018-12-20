# -*- coding: utf-8 -*-

# project imports
from ks.models import Pacman, ECell
from extensions.agent import get_position, calculate_new_position, can_move
from gui_events import GuiEvent, GuiEventType


def change_direction(self, world, command):
    self.direction = command.direction


def eat_food(self, world):

     # Add score to pacman
    world.scores["Pacman"] += world.constants.food_score
    # Change Food to Empty
    world.board[self.y][self.x] = ECell.Empty
    # Decrease the number of foods
    world.num_of_foods -= 1


def eat_super_food(self, world):

    # Add score to pacman
    world.scores["Pacman"] += world.constants.super_food_score
    # Change Food to Empty
    world.board[self.y][self.x] = ECell.Empty
    # Decrease the number of super foods
    world.num_of_super_foods -= 1


def can_eat_food(self, world, position):
    return world.board[(position[1])][(position[0])] == ECell.Food


def can_eat_super_food(self, world, position):
    return world.board[(position[1])][(position[0])] == ECell.SuperFood


def move(self, world):

    gui_events = []
    new_position = world.pacman.calculate_new_position()

    if world.pacman.can_move(world, new_position):
        world.pacman.x = new_position[0]
        world.pacman.y = new_position[1]
        gui_events.append(GuiEvent(GuiEventType.MovePacman, new_pos=new_position))
        return gui_events

    return gui_events


Pacman.change_direction = change_direction
Pacman.get_position = get_position
Pacman.calculate_new_position = calculate_new_position
Pacman.eat_food = eat_food
Pacman.eat_super_food = eat_super_food
Pacman.can_eat_food = can_eat_food
Pacman.can_eat_super_food = can_eat_super_food
Pacman.can_move = can_move
Pacman.move = move
