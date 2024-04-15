
import numpy as np
import random
from search_algorithms import greedy_path

class GraphMap:
    def __init__(self, trash_agents, central_agent):
        np.random.seed(0) # set the seed to 0 for uniform results
        self.n_locations = len(trash_agents) + 1 # +1 because the central is also a location
        # Initialize the distance matrix with zeros
        self.distance_matrix = np.zeros((self.n_locations, self.n_locations))
        # set up a dictionary that maps agent index to their respective jid (string)
        self.index_to_agent = {}
        for i, agent in enumerate(trash_agents):
            self.index_to_agent[i] = str(agent.jid)
        # the central agent is the last index
        self.index_to_agent[self.n_locations-1] = str(central_agent.jid)

        min_distance = 5
        max_distance = 15

        # fill the distance matrix with random values
        # the matrix is symmetric, because the distance from 'i' to 'j' is the same as from 'j' to 'i'
        for i in range(self.n_locations):
            for j in range(i):
                random_distance = random.randint(min_distance, max_distance)
                self.distance_matrix[i][j] = self.distance_matrix[j][i] = random_distance

    def find_best_path(self):
        best_path = greedy_path(self.n_locations-1, self.distance_matrix, [])
        # best_path[0] == best_path[-1] -> the start and end location is the same (trash center)

        # now we need to change best_path, because it contains the indexes of the agents in the path, instead of their jid's
        jids_path = [self.index_to_agent[i] for i in best_path]

        # get cost array based on best path
        cost_array = []
        for i in range(len(best_path)-1):
            start = best_path[i]
            end = best_path[i+1]
            cost = self.distance_matrix[start][end]
            cost_array.append(cost)
        return jids_path, cost_array
