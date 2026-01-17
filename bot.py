import random
from game_message import *

BIOMASSE_MAX_TO_SPAWNER = 8
NUTRIENTS_MIN_TO_SPORE = 5
BIOMASS_FOR_SPORE = 4
SPORE_AMOUNT_FOR_PROTECTOR = 10
SPORE_AMOUNT_FOR_BIG_PROTECTOR = 20
SPORE_SMALL_PROTECTOR = 15 
SPORE_BIG_PROTECTOR = 30 
MAX_DISTANCE_FOR_TARGET = 40
BASE_TARGET_PRIORITY = 9999
PRIORITY_DONT_TOUCH = -1
DISTANCE_COEFF_FOR_TILE_RATING = 5
NUTRIENTS_RATING = 80
DISTANCE_MALUS_COEFFICIENT = 5
DEFENDER_DISTANCE_MALUS_COEFFICIENT = 20
BIOMASS_MALUS_COEFFICIENT = 2

NUTRIMENT_NEXT_GENERATOR = 30
GENERATOR_NEXT = 10

DEFENDER = "Defender"
ATTACKER = "Attacker"
SCOUT = "Scout"
GENERATOR = "Generator"

BIOMASS_SCOUT = 2
BIOMASS_ATTACKER = 4
BIOMASS_DEFFENDER = 7
BIOMASS_GENERATOR = 1

# A* Pathfinding cost factors
A_STAR_OUR_TILE_COST = 0
A_STAR_EMPTY_TILE_COST = 1
A_STAR_NUTRIENTS_DIVISOR = 4  # Reduces nutrients impact (divide by this value)
A_STAR_BIOMASS_MULTIPLIER = 1  # Multiplies biomass cost impact

class Bot:
    def __init__(self):
        self.state: TeamGameState = None
        self.biomass_to_spawner = BIOMASSE_MAX_TO_SPAWNER
        self.Spore_roles = {
            DEFENDER : [],
            ATTACKER : [],
            SCOUT    : [],
            GENERATOR: []
        }

        print("Initializing your super mega duper bot")

    def get_next_move(self, game_message: TeamGameState) -> list[Action]:
        """
        Here is where the magic happens, for now the moves are not very good. I bet you can do better ;)
        """
        self.actions = []
        self.state = game_message

        print(self.state.lastTickErrors)


        self.actions += self.decision_spawner(game_message)
        self.actions += self.sporeMovementActions()
        self.actions += self.create_spore(game_message)

        ########################################################
        # to be removed
        # my_team: TeamInfo = self.state.world.teamInfos[self.state.yourTeamId]
        # if len(my_team.spores) == 0:
        #     self.actions.append(
        #         SpawnerProduceSporeAction(spawnerId=my_team.spawners[0].id, biomass=20)
        #     )

        # else:
        #     self.actions.append(
        #         SporeMoveToAction(
        #             sporeId=my_team.spores[0].id,
        #             position=Position(
        #                 x=random.randint(0, game_message.world.map.width - 1),
        #                 y=random.randint(0, game_message.world.map.height - 1),
        #             ),
        #         )
        #     )
        ###########################################################

        # You can clearly do better than the random actions above. Have fun!!
        return self.actions

    def sporeMovementActions(self) -> list[SporeMoveToAction]:
        print("heere")
        possibleTargets: list[list[int]] = self.getTargets()

        # print(f">>> Possible targets:\n{possibleTargets}")

        wantedTargets: dict[str, (Position, Position)] = self.scout_target_assignement(possibleTargets)
        
        # print(f">>> Wanted targets:\n{wantedTargets}")
        
        actions: list[SporeMoveToAction] = []

        for spore in wantedTargets:
            path = self.a_star_pathfinding(wantedTargets[spore][0], wantedTargets[spore][1])
            # print(" Spore ", spore, " path for pos ", wantedTargets[spore][0], " to ", wantedTargets[spore][1], ":")
            # for pos in path:
            #     print("  ", pos)
            action = SporeMoveToAction(spore, path[1])
            actions.append(action)

        # print(f">>> MoveToActions:\n   ")

        return actions

    def defender_target_assignement(self) -> list[SporeMoveToAction]:
        grid = self.state.world.ownershipGrid
        width = self.state.world.map.width
        height = self.state.world.map.height
        us = self.state.yourTeamId
        targets: list[list[int]] = [
            [BASE_TARGET_PRIORITY] * width for _ in range(height)
        ]
        actions: list[SporeMoveToAction] = []
        spores = self.Spore_roles[DEFENDER].copy()

        print(f">>> getting targets on grid:\n{grid}")

        for i in range(width):
            for j in range(height):
                malus = (
                    self.deltaBase(Position(i, j)) * DEFENDER_DISTANCE_MALUS_COEFFICIENT
                )
                targets[i][j] -= malus
                if grid[i][j] == us:
                    targets[i][j] = PRIORITY_DONT_TOUCH

        for spore in spores:
            best: Position = Position(0, 0)
            for i in range(width):
                for j in range(height):
                    if targets[i][j] > targets[best.x][best.y]:
                        best = Position(i, j)
            targets[best.x][best.y] = PRIORITY_DONT_TOUCH
            action = SporeMoveToAction(spore.id, best)
            actions.append(action)

        return actions

    def scout_target_assignement(self, targetTiles: list[list[int]]) -> dict[str, (Position, Position)]:
        # print("<<< Target tiles:")
        # for row in targetTiles:
        #     print(row)
        # print(">>> Target assignment")
        # spores = self.Spore_roles[SCOUT]
        spores = self.state.world.teamInfos[self.state.yourTeamId].spores
        assignments: dict[str, (Position, Position)] = {}
        assigned_tiles: set[Position] = set()

        for spore in spores:
            # check if spore already has an action
            spore_already_has_action = False
            # for action in self.actions:
            #     if action.sporeId == spore.id:
            #         spore_already_has_action = True
            #         print(" Spore ", spore.id, " already has an action, skipping")
            #         break
            if spore_already_has_action:
                continue
            # print("Assigning target for spore ", spore.id)
            # print("spore pos: ", spore.position)
            best_tile = None

            distance = 1
            spore_pos = spore.position
            
            # tile ratings to spore
            tileratings = [[] for _ in range(self.state.world.map.height)]
            for i in range(self.state.world.map.width):
                for j in range(self.state.world.map.height):
                    rating = self.tile_rating(targetTiles, Position(i,j), spore_pos)
                    tileratings[i].append(rating)
            # print(" Tile ratings to spore:")
            # for row in tileratings:
            #     print(row)
            
            while distance < MAX_DISTANCE_FOR_TARGET - 1:
                # print(" Checking distance ", distance)
                rand_pos = random.randint(0,3)
                pos_x = spore_pos.x
                pos_y = spore_pos.y
                if rand_pos == 0:
                    pos_x += distance
                elif rand_pos == 1:
                    pos_x -= distance
                elif rand_pos == 2:
                    pos_y += distance
                else:
                    pos_y -= distance
                pos = Position(spore_pos.x + distance, spore_pos.y)  # starting position
                
                # pos = Position(spore_pos.x + distance ,spore_pos.y) # TODO : random start position
                nb_to_check = distance * 4 # number of tiles to check at this distance
                dir_x = 1
                dir_y = 1
                for _ in range(nb_to_check):
                    if (0 <= pos.x < self.state.world.map.width) and (0 <= pos.y < self.state.world.map.height):
                        # print("  Position ", pos, " has target value ", targetTiles[pos.x][pos.y])
                        if (targetTiles[pos.x][pos.y] > PRIORITY_DONT_TOUCH
                        and (pos.x, pos.y) not in assigned_tiles 
                        and (best_tile is None or self.tile_rating(targetTiles, Position(pos.x, pos.y), spore_pos) > self.tile_rating(targetTiles, best_tile, spore_pos))):
                            best_tile = Position(x = pos.x, y = pos.y)
                    
                    if pos.x == spore_pos.x + distance:
                        dir_x = -1
                    elif pos.x == spore_pos.x - distance:
                        dir_x = 1
                        
                    if pos.y == spore_pos.y + distance:
                        dir_y = -1
                    elif pos.y == spore_pos.y - distance:
                        dir_y = 1
                        
                    pos.x += dir_x
                    pos.y += dir_y
                    
                    # # Move to next tile in diamond (distance doesn't account for diagonals)
                    # if pos.x == spore_pos.x + distance and pos.y < spore_pos.y + distance:
                    #     pos.y += 1
                    #     pos.x -= 1
                    # elif pos.y == spore_pos.y + distance and pos.x > spore_pos.x - distance:
                    #     pos.y += 1
                    #     pos.x -= 1
                    # elif pos.x == spore_pos.x - distance and pos.y > spore_pos.y - distance:
                    #     pos.y -= 1
                    #     pos.x += 1
                    # elif pos.y == spore_pos.y - distance and pos.x < spore_pos.x + distance:
                    #     pos.y -= 1
                    #     pos.x += 1
                    # elif pos.x < spore_pos.x + distance and pos.y < spore_pos.y + distance:
                    #     pos.x += 1
                    #     pos.y += 1
                    # elif pos.x > spore_pos.x - distance and pos.y > spore_pos.y - distance:
                    #     pos.x -= 1
                    #     pos.y -= 1
                    # elif pos.x < spore_pos.x + distance and pos.y > spore_pos.y - distance:
                    #     pos.x += 1
                    #     pos.y -= 1
                    # elif pos.x > spore_pos.x - distance and pos.y < spore_pos.y + distance:
                    #     pos.x -= 1
                    #     pos.y += 1
                    # else:
                    #     print("Error in target assignment")
                    #     break # should not happen
                    
                distance += 1
                if distance > MAX_DISTANCE_FOR_TARGET:
                    print(" No target found within max distance")
                    break
            if best_tile:
                assignments[spore.id] = (spore_pos, best_tile)
                assigned_tiles.add((best_tile.x, best_tile.y))

        print("<<< Target assignment")
        return assignments

    def getTargets(self) -> list[list[int]]:
        grid = self.state.world.ownershipGrid
        width = self.state.world.map.width
        height = self.state.world.map.height
        us = self.state.yourTeamId
        nutrientsBonus = self.coolNutrients()
        targets: list[list[int]] = [
            [BASE_TARGET_PRIORITY] * width for _ in range(height)
        ]

        # print(f">>> getting targets on grid:\n{grid}")

        for i in range(width):
            for j in range(height):
                targets[i][j] += nutrientsBonus[i][j]
                malus = self.evaluateTile(Position(i, j))
                targets[i][j] -= malus
                if grid[i][j] == us:
                    targets[i][j] = PRIORITY_DONT_TOUCH

        return targets

    def evaluateTile(self, position: Position) -> int:
        grid = self.state.world.ownershipGrid
        biomassGrid = self.state.world.biomassGrid
        us = self.state.yourTeamId
        i = position.x
        j = position.y
        malus = 0

        if grid[i][j] != us:
            malus = (biomassGrid[i][j] * BIOMASS_MALUS_COEFFICIENT) + (
                self.deltaBase(Position(i, j)) * DISTANCE_MALUS_COEFFICIENT
            )

        return malus

    def ourSpawners(self) -> list[Spawner]:
        us = self.state.yourTeamId
        ourSpawners: list[Spawner] = []

        for spawner in self.state.world.spawners:
            if spawner.teamId == us:
                ourSpawners.append(spawner)

        return ourSpawners

    def baseCenter(self, position: Position) -> Position:
        totalPos: Position = Position(0, 0)
        ourSpawners = self.ourSpawners()

        if len(ourSpawners) <= 0:
            return None

        for spawner in ourSpawners:
            totalPos.x += spawner.position.x
            totalPos.y += spawner.position.y


        avgPos = Position(
            int(totalPos.x / len(self.state.world.spawners)),
            int(totalPos.y / len(self.state.world.spawners)),
        )

        return avgPos

    def deltaBase(self, position: Position) -> int:
        basePos = self.baseCenter(position)

        if basePos is None:
            return 0

        delta = 0
        if basePos.x > position.x:
            delta += basePos.x - position.x
        else:
            delta += position.x - basePos.x

        if basePos.y > position.y:
            delta += basePos.y - position.y
        else:
            delta += position.y - basePos.y

        return delta
        
    def coolNutrients(self) -> list[list[int]]:
        nutrients = self.state.world.map.nutrientGrid
        width = self.state.world.map.width
        height = self.state.world.map.height
        bonusRating: list[list[int]] = [
            [0 for _ in range(height)] for _ in range(width)
        ]

        for i in range(width):
            for j in range(height):
                bonusRating[i][j] = nutrients[i][j] * NUTRIENTS_RATING

        return bonusRating

    def check_spawner_positions(self, game_state: TeamGameState, spore):
        my_team: TeamInfo = game_state.world.teamInfos[game_state.yourTeamId]

        for spawner in my_team.spawners:
            if(spore.position == spawner.position):
                return True

        return False
    
    def create_spawner(self, game_state: TeamGameState):
        actions = []
        my_team: TeamInfo = game_state.world.teamInfos[game_state.yourTeamId]

        if(my_team.nutrients > NUTRIMENT_NEXT_GENERATOR):
            self.biomass_to_spawner = my_team.nextSpawnerCost + GENERATOR_NEXT
            
        for spore in my_team.spores:
            if (my_team.nextSpawnerCost < self.biomass_to_spawner and
                 spore.biomass >= my_team.nextSpawnerCost and
                 not self.check_spawner_positions(game_state, spore)):
                actions.append(SporeCreateSpawnerAction(sporeId=spore.id))

        return actions
    
    def decision_spawner(self, game_state: TeamGameState):
        actions = []
        actions += self.create_spawner(game_state)

        return actions
    
    def create_spore(self, game_state: TeamGameState):
        actions = []
        my_team: TeamInfo = game_state.world.teamInfos[game_state.yourTeamId]

        for spawner in my_team.spawners:
            if(my_team.nutrients > NUTRIENTS_MIN_TO_SPORE):
                actions.append(SpawnerProduceSporeAction(spawner.id, self.spore_size_decision(game_state)))

        return actions
    
    def spore_size_decision(self, game_state: TeamGameState):
        actions = []
        my_team: TeamInfo = game_state.world.teamInfos[game_state.yourTeamId]
        spore_amount = len(my_team.spores)

        if(spore_amount > SPORE_AMOUNT_FOR_BIG_PROTECTOR):
            return SPORE_BIG_PROTECTOR
        elif(spore_amount > SPORE_AMOUNT_FOR_PROTECTOR):
            return SPORE_SMALL_PROTECTOR
        
        return  BIOMASS_FOR_SPORE
    
    def tile_rating(self, targets: list[list[int]], tile_pos: Position, spore_pos: Position) -> int:
        distance = abs(tile_pos.x - spore_pos.x) + abs(tile_pos.y - spore_pos.y)
        if distance == 0:
            return PRIORITY_DONT_TOUCH
        # return targets[tile_pos.x][tile_pos.y]
        return targets[tile_pos.x][tile_pos.y] - (distance * DISTANCE_COEFF_FOR_TILE_RATING)
    
    def assign_spore_role(self):
        my_team: TeamInfo = self.state.world.teamInfos[self.state.yourTeamId]

        for spore in my_team.spores:
            if(spore.biomass >= BIOMASS_DEFFENDER):
                self.Spore_roles[DEFENDER].append(spore)

            elif(spore.biomass < BIOMASS_DEFFENDER and spore.biomass >= BIOMASS_ATTACKER):
                self.Spore_roles[ATTACKER].append(spore)
            
            elif(spore.biomass >= BIOMASS_DEFFENDER and spore.biomass >= BIOMASS_SCOUT):
                self.Spore_roles[SCOUT].append(spore)
            
            elif(spore.biomass < BIOMASS_GENERATOR):
                self.Spore_roles[GENERATOR].append(spore)
    
    def a_star_pathfinding(self, start: Position, goal: Position) -> list[Position]:
        """
        A* pathfinding algorithm to find optimal path from start to goal.
        Cost factors:
        - Base cost: 1 per tile moved
        - Movement cost: 0 for our tiles, 1 for empty, biomass for opponent tiles
        - Nutrients: reduce cost slightly (bonus)
        """
        from heapq import heappush, heappop
        
        width = self.state.world.map.width
        height = self.state.world.map.height
        us = self.state.yourTeamId
        
        def heuristic(pos: Position) -> int:
            """Manhattan distance heuristic"""
            return abs(pos.x - goal.x) + abs(pos.y - goal.y)
        
        def get_movement_cost(pos: Position) -> int:
            """
            Get the cost to enter a tile.
            Our tiles: 0
            Empty tiles (not owned by anyone): 1
            Other tiles: biomass on that tile
            Nutrients provide a small bonus
            """
            ownership = self.state.world.ownershipGrid[pos.x][pos.y]
            biomass = self.state.world.biomassGrid[pos.x][pos.y]
            nutrients = self.state.world.map.nutrientGrid[pos.x][pos.y]
            
            # Our tiles have no movement cost
            if ownership == us:
                cost = A_STAR_OUR_TILE_COST
            # Empty/neutral tiles cost 1
            elif ownership is None or ownership == "":
                cost = A_STAR_EMPTY_TILE_COST
            # Other team's tiles cost equal to biomass
            else:
                cost = biomass * A_STAR_BIOMASS_MULTIPLIER
            
            # Nutrients provide a small bonus (reduce cost)
            if nutrients > 0:
                cost = max(0, cost - nutrients // A_STAR_NUTRIENTS_DIVISOR)
            
            return cost
        
        # Open set: heap of (f_score, counter, position)
        open_set = [(0, 0, start)]
        counter = 1
        
        # Closed set: visited nodes
        closed_set = set()
        
        # For path reconstruction
        came_from = {}
        
        # g_score: actual cost from start to each node
        g_score = {(start.x, start.y): 0}
        
        while open_set:
            _, _, current = heappop(open_set)
            
            # Goal reached
            if current.x == goal.x and current.y == goal.y:
                # Reconstruct path
                path = []
                pos = (current.x, current.y)
                while pos in came_from:
                    path.append(Position(pos[0], pos[1]))
                    pos = came_from[pos]
                path.append(start)
                return path[::-1]
            
            closed_set.add((current.x, current.y))
            
            # Check all 4 neighbors (up, down, left, right - no diagonals)
            neighbors = [
                Position(current.x + 1, current.y),
                Position(current.x - 1, current.y),
                Position(current.x, current.y + 1),
                Position(current.x, current.y - 1),
            ]
            
            for neighbor in neighbors:
                # Check bounds
                if not (0 <= neighbor.x < width and 0 <= neighbor.y < height):
                    continue
                
                if (neighbor.x, neighbor.y) in closed_set:
                    continue
                
                # Calculate tentative g_score
                tentative_g = g_score[(current.x, current.y)] + get_movement_cost(neighbor)
                
                # If this is a better path, update it
                if (neighbor.x, neighbor.y) not in g_score or tentative_g < g_score[(neighbor.x, neighbor.y)]:
                    came_from[(neighbor.x, neighbor.y)] = (current.x, current.y)
                    g_score[(neighbor.x, neighbor.y)] = tentative_g
                    f_score = tentative_g + heuristic(neighbor)
                    heappush(open_set, (f_score, counter, neighbor))
                    counter += 1
        
        # No path found, return empty list
        return []