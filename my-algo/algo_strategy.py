import gamelib
import random
from sys import maxsize
import json

class AlgoStrategy(gamelib.AlgoCore):
    def __init__(self):
        super().__init__()
        seed = random.randrange(maxsize)
        random.seed(seed)
        gamelib.debug_write('Random seed: {}'.format(seed))

    def on_game_start(self, config):
        gamelib.debug_write('Configuring your custom algo strategy...')
        self.config = config
        global WALL, SUPPORT, TURRET, SCOUT, DEMOLISHER, INTERCEPTOR, MP, SP
        WALL = config["unitInformation"][0]["shorthand"]
        SUPPORT = config["unitInformation"][1]["shorthand"]
        TURRET = config["unitInformation"][2]["shorthand"]
        SCOUT = config["unitInformation"][3]["shorthand"]
        DEMOLISHER = config["unitInformation"][4]["shorthand"]
        INTERCEPTOR = config["unitInformation"][5]["shorthand"]
        MP = 1
        SP = 0
        self.scored_on_locations = []
        self.damaged_locations = []

    def on_turn(self, turn_state):
        game_state = gamelib.GameState(self.config, turn_state)
        game_state.suppress_warnings(True)
        self.strategy(game_state)
        self.scored_on_locations = []
        self.damaged_locations = []
        game_state.submit_turn()

    def strategy(self, game_state):
        self.build_reactive_defense(game_state)
        self.rebuild_defense(game_state)
        deploy_locations = self.filter_blocked_starting(game_state)
        best_location_attack = self.least_damage_spawn_location(game_state, deploy_locations)
        best_location_defense = self.best_intercept_location(game_state, deploy_locations)
        self.main_alg(game_state, best_location_attack, best_location_defense)

    def build_reactive_defense(self, game_state):

        setup = [[2,11], [3,10], [4,9], [5,8], [6,7], [7,6], [8,5], [9,4], [10, 3], [11, 3], [14, 3], [15, 3], [16, 4], [17, 5], [18, 6], [19, 7], [20, 8], [21, 9]]

        for location in self.scored_on_locations:
            nearby = [location[0] - 1, location[0], location[0] + 1]
            for i in nearby:
                if i in [x[0] for x in setup]:
                    build_location = [x for x in setup if x[0] == i]
                    if i == location[0]:
                        game_state.attempt_spawn(TURRET, build_location)
                    else:
                        game_state.attempt_spawn(WALL, build_location)
    
    def rebuild_defense(self, game_state):
        turret_locations = [[27, 13], [25, 13], [23, 13], [24, 12]]
        game_state.attempt_spawn(TURRET, turret_locations)
        turret_locations = [[0, 13], [1, 12], [2, 13], [4, 13]]
        game_state.attempt_spawn(TURRET, turret_locations)
        wall_locations = [[1, 13], [3, 13], [26, 13], [24, 13]]
        game_state.attempt_spawn(WALL, wall_locations)
        turret_locations = [[12, 4], [13, 4]]
        game_state.attempt_spawn(TURRET, turret_locations)
        support_locations = [[12, 3], [13, 3], [24, 11], [21, 9], [3, 12]]
        game_state.attempt_spawn(SUPPORT, support_locations)
        wall_locations = [[10, 3], [11, 3]]
        game_state.attempt_spawn(WALL, wall_locations)
        wall_locations = [[14, 3], [15, 3], [16, 4], [17, 5]]
        game_state.attempt_spawn(WALL, wall_locations)
        wall_locations = [[18, 6], [19, 7], [20, 8]]
        game_state.attempt_spawn(WALL, wall_locations)
        turret_locations = [[20, 9], [20, 10], [21, 10], [23, 12]]
        game_state.attempt_spawn(TURRET, turret_locations)
    
    def best_intercept_location(self, game_state, location_options):
        damages = []
        for location in location_options:
            path = game_state.find_path_to_edge(location)
            damage = 0.0
            surrounding = [-3, -2, -1, 0, 1, 2, 3]
            for path_location in path:
                for i in surrounding:
                    for j in surrounding:
                        if [path_location[0] + i, path_location[1] + j] in self.damaged_locations:
                            damage += 5 * (1 - 0.15 * (abs(i) + abs(j)))
                        if [path_location[0] + i, path_location[1] + j] in self.scored_on_locations:
                            damage += 10 * (1  - 0.15 * (abs(i) + abs(j)))
            damages.append(damage)
        return location_options[damages.index(max(damages))]
    
    def least_damage_spawn_location(self, game_state, location_options):
        damages = []
        for location in location_options:
            path = game_state.find_path_to_edge(location)
            damage = 0
            for path_location in path:
                damage += len(game_state.get_attackers(path_location, 0)) * gamelib.GameUnit(TURRET, game_state.config).damage_i
            damages.append(damage)
        return location_options[damages.index(min(damages))]
    
    def filter_blocked_starting(self, game_state):
        locations = [i for i in game_state.game_map.get_edge_locations(game_state.game_map.BOTTOM_LEFT) + game_state.game_map.get_edge_locations(game_state.game_map.BOTTOM_RIGHT) if i[1] < 6]
        filtered = []
        for location in locations:
            if not game_state.contains_stationary_unit(location):
                filtered.append(location)
        return filtered
    
    def main_alg(self, game_state, best_location_attack, best_location_defense):
        if game_state.turn_number > 5:
            if game_state.enemy_health <= 10:
                turret_locations = [[22, 11], [10, 4]]
                game_state.attempt_spawn(TURRET, turret_locations)
                game_state.attempt_spawn(SCOUT, best_location_attack, 10)

            if game_state.enemy_health > 10 or game_state.turn_number % 2 == 0:
                game_state.attempt_spawn(DEMOLISHER, best_location_attack, 5)
        
        if game_state.turn_number <= 5 or (game_state.my_health < 10 and game_state.enemy_health > 20):
            game_state.attempt_spawn(INTERCEPTOR, best_location_defense, 2)
        
        wall_locations = [[2,11], [3,10], [4,9], [5,8], [6,7], [7,6], [8,5], [9,4]]
        game_state.attempt_spawn(WALL, wall_locations)

    def on_action_frame(self, turn_string):
        state = json.loads(turn_string)
        events = state["events"]
        breaches = events["breach"]
        damages = events["damage"]
        for breach in breaches:
            location = breach[0]
            unit_owner_self = True if breach[4] == 1 else False
            if not unit_owner_self:
                self.scored_on_locations.append(location)
        for damage in damages:
            location = damage[0]
            unit_owner_self = True if damage[4] == 1 else False
            if unit_owner_self:
                self.damaged_locations.append(location)

if __name__ == "__main__":
    algo = AlgoStrategy()
    algo.start()