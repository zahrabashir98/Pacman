# -*- coding: utf-8 -*-

# project imports
from ks.commands import ECommandDirection
from extensions import world
from gui_events import *
from ks.models import World, ECell, EDirection


class LogicHandler ():

    def __init__ (self, world, sides):

        self._sides = sides
        self.world = world
        self._last_cycle_commands = {side: {} for side in self._sides}
        self._num_of_foods = 0
        self._num_of_super_foods = 0
        self._is_pacman_dead = False
        self._giant_form = False
        self._is_ghost_dead = {ghost.id : False for ghost in self.world.ghosts} 


    def initialize(self):


        for y in range(self.world.width):
            for x in range(self.world.height):
                if self.world.board[y][x] == ECell.Food:
                    self._num_of_foods += 1
                elif self.world.board[y][x] == ECell.SuperFood:
                    self._num_of_super_foods += 1


        self._convert_dir_to_pos = {
            EDirection.Up.name:(0, -1),
            EDirection.Down.name: (0, +1),
            EDirection.Right.name: (+1, 0),
            EDirection.Left.name: (-1, 0)
        }

        self._opponent_direction = {
            EDirection.Up.name: EDirection.Down.name,
            EDirection.Down.name: EDirection.Up.name,
            EDirection.Right.name: EDirection.Left.name,
            EDirection.Left.name: EDirection.Right.name
        }


    def store_command(self, side_name, command):

        if side_name == "Ghost":
            if command.id < 0 or command.id >= ( len(self.world.ghosts)):
                print('Invalid id in command: %s %i' % (side_name, command.id))
                return

        if side_name == "Ghost":
            if not self._is_ghost_dead[command.id]:
                self._last_cycle_commands[side_name][command.id] = command

        elif side_name == "Pacman":
            self._last_cycle_commands[side_name][None] = command


    def clear_commands(self):
        self._last_cycle_commands = {side: {} for side in self._sides}


    def process(self, current_cycle):

        gui_events = []

        # Giant form Recover ghosts
        for ghost in self.world.ghosts:
            if self._is_ghost_dead[ghost.id] == True:
                gui_events.extend(self._recover_ghost(ghost.id))

        if self._is_pacman_dead:
            gui_events.extend(self._recover_agents())

        else:
            # Change direction
            for side_name in self._sides:
                for command_id in self._last_cycle_commands[side_name]:
                    gui_events.extend(self.world.apply_command(side_name, self._last_cycle_commands[side_name][command_id]))
           
            # Move
            gui_events.extend(self._move_pacman())
            gui_events.extend(self._move_ghosts())
            

            # Kill pacman
            hit_ghosts_id = self._check_hit()
            if hit_ghosts_id!=[] and not self._giant_form:
                self._is_pacman_dead = True
                self._kill_pacman()

            elif hit_ghosts_id!=[] and self._giant_form:
                for ghost_id in hit_ghosts_id:
                    self._is_ghost_dead[ghost_id] = True
                    self._kill_ghost()

            # Eat food
            if not self._is_pacman_dead:
                pacman_position = self.world.pacman.get_position()
                # foood
                if self._can_be_eaten_as_a_food(pacman_position):
                    self._eat_food(pacman_position)
                    gui_events.append(GuiEvent(GuiEventType.EatFood, position=(pacman_position)))
                # super food
                if self._can_be_eaten_as_a_super_food(pacman_position):
                    self._eat_super_food(pacman_position)
                    gui_events.append(GuiEvent(GuiEventType.EatSuperFood, position=(pacman_position)))

            if self._giant_form:
                self.world.pacman.giant_form_remaining_time -= 1
                print(self.world.pacman.giant_form_remaining_time)
                # Check if giant form is ended(TODO: make it a method)
                if self.world.pacman.giant_form_remaining_time == 0:
                    gui_events.append(GuiEvent(GuiEventType.EndGiantForm))
                    self._giant_form = False

        return gui_events


    def _check_toward_move(self, pacman, ghost):

        if ghost.direction.name == self._opponent_direction[pacman.direction.name]:
            if ghost.direction.name == EDirection.Up.name and ghost.y < pacman.y:
                return True
            if ghost.direction.name == EDirection.Down.name and ghost.y > pacman.y:
                return True
            if ghost.direction.name == EDirection.Right.name and ghost.x > pacman.x:
                return True
            if ghost.direction.name == EDirection.Left.name and ghost.x < pacman.x:
                return True


    def _check_hit(self):
        hit_ghosts_id = []
        for ghost in self.world.ghosts:
    
            # Check same cell 
            if self.world.ghosts[ghost.id].get_position() == self.world.pacman.get_position():
                hit_ghosts_id.append(ghost.id)

            # Check moving toward each other
            if self._check_toward_move(self.world.pacman, ghost) and self._check_adjacency(ghost):
                hit_ghosts_id.append(ghost.id)

        return hit_ghosts_id


    def _check_adjacency(self, ghost):

        if ghost.x == self.world.pacman.x and (ghost.y == self.world.pacman.y+1 or ghost.y == self.world.pacman.y-1):
            return True

        elif ghost.y == self.world.pacman.y and (ghost.x == self.world.pacman.x+1 or ghost.x == self.world.pacman.x-1):
            return True
        else:
            return False


    def _move_pacman(self):

        gui_events = []
        pacman_position = self.world.pacman.get_position()
        new_position = (self._convert_dir_to_pos[self.world.pacman.direction.name][0]+pacman_position[0],
                         self._convert_dir_to_pos[self.world.pacman.direction.name][1]+pacman_position[1])

        if self._can_move(new_position):
            self.world.pacman.x = new_position[0]
            self.world.pacman.y = new_position[1]
            gui_events.append(GuiEvent(GuiEventType.MovePacman, new_pos=new_position))
            return gui_events

        return gui_events


    def _move_ghosts(self):

        gui_events = []

        for ghost in self.world.ghosts:
            ghost_position = self.world.ghosts[ghost.id].get_position()
            print(ghost_position)
            new_position = (self._convert_dir_to_pos[ghost.direction.name][0]+ghost_position[0],
                         self._convert_dir_to_pos[ghost.direction.name][1]+ghost_position[1])
            print(new_position)
            if self._can_move(new_position):
                ghost.x = new_position[0]
                ghost.y = new_position[1]
                if self._is_ghost_dead[ghost.id]==False:
                    print("ghost can move")
                    gui_events.append(GuiEvent(GuiEventType.MoveGhost, new_pos=new_position, id=ghost.id))


        return gui_events


    def _can_move(self, position):
        return self.world.board[(position[1])][(position[0])] != ECell.Wall


    def _can_be_eaten_as_a_food(self, position):
        return self.world.board[(position[1])][(position[0])] == ECell.Food


    def _can_be_eaten_as_a_super_food(self, position):
        return self.world.board[(position[1])][(position[0])] == ECell.SuperFood


    def _eat_food(self, position):

        # Add score to pacman
        self.world.scores["Pacman"] += self.world.constants.food_score
        # Change Food to Empty
        self.world.board[(position[1])][(position[0])] = ECell.Empty
        # Decrease the number of foods
        self._num_of_foods -= 1


    def _eat_super_food(self, position):

        # Add score to pacman
        self.world.scores["Pacman"] += self.world.constants.super_food_score
        # Change Food to Empty
        self.world.board[(position[1])][(position[0])] = ECell.Empty
        # Decrease the number of super foods
        self._num_of_super_foods -= 1
        self.giant_form()


    def giant_form(self):
                
        self.world.pacman.giant_form_remaining_time = self.world.constants.pacman_giant_form_duration
        self._giant_form = True


    def get_client_world(self):
        return self.world


    def _kill_pacman(self):

        self.world.scores["Ghost"] += self.world.constants.pacman_death_score
        self.world.pacman.health -= 1


    def _kill_ghost(self):
        self.world.scores["Pacman"] += self.world.constants.ghost_death_score


    def _recover_ghost(self, ghost_id):
        self.world.ghosts[ghost_id].x = self.world.ghosts[ghost_id].init_x
        self.world.ghosts[ghost_id].y = self.world.ghosts[ghost_id].init_y
        self.world.ghosts[ghost_id].direction = self.world.ghosts[ghost_id].init_direction
        self._is_ghost_dead[ghost_id] = False
        return [
            GuiEvent(GuiEventType.ChangeGhostDirection, id=ghost_id, direction=self.world.ghosts[ghost_id].direction),
            GuiEvent(GuiEventType.MoveGhost,new_pos=(self.world.ghosts[ghost_id].x,self.world.ghosts[ghost_id].y), id=ghost_id)
            ]


    def _recover_agents(self):
        gui_events = []

        # Pacman reset
        self.world.pacman.x = self.world.pacman.init_x
        self.world.pacman.y = self.world.pacman.init_y
        self.world.pacman.direction = self.world.pacman.init_direction
        gui_events.append(GuiEvent(GuiEventType.ChangePacmanDirection, direction=self.world.pacman.direction))
        gui_events.append(GuiEvent(GuiEventType.MovePacman, new_pos=self.world.pacman.get_position()))

        # Ghosts reset
        for ghost in self.world.ghosts:
            gui_events.extend(self._recover_ghost(ghost.id))

        # Update health
        gui_events.append(GuiEvent(GuiEventType.UpdateHealth))
        self._is_pacman_dead = False
        return gui_events


    def check_end_game(self, current_cycle):

        end_game = False
        winner = None
        details = None
        if current_cycle >= self.world.constants.max_cycles - 1:
            end_game = True

        elif self.world.pacman.health == 0:
            end_game = True
        
        elif self._num_of_foods == 0:
            end_game = True

        if end_game:
            
            if self.world.scores['Pacman'] > self.world.scores['Ghost']:
                winner = 'Pacman'
            elif self.world.scores['Ghost'] > self.world.scores['Pacman']:
                winner = 'Ghost'
            details = {
                'Scores': {
                    'Pacman': str(self.world.scores['Pacman']),
                    'Ghost': str(self.world.scores['Ghost'])
                    }
                }
        return end_game, winner, details
