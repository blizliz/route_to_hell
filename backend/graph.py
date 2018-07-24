# -*- coding: utf-8 -*-
import xml.etree.cElementTree as ET
from time import sleep

from geopy.distance import vincenty
from queue import PriorityQueue

NODES = {}
STREETS = {}


class Street():
    def __init__(self, street_id, points):
        super(Street, self).__init__()
        self.street_id = street_id
        self.points = points


class Node():
    def __init__(self, node_id, street_id, cost):
        super(Node, self).__init__()
        self.node_id = node_id
        self.street_id = street_id
        self.cost = cost


class Graph():
    def __init__(self, file_name):
        super(Graph, self).__init__()
        self.osm_name = file_name
        self.edges = []
        self.data = {}

        self.parse_osm()
        self.build_graph()

    def parse_osm(self):
        tree = ET.ElementTree(file=self.osm_name)
        root = tree.getroot()

        for child in root:
            if child.tag == "node":
                id = child.attrib['id']
                lat = float(child.attrib['lat'])
                lon = float(child.attrib['lon'])
                NODES[id] = {'lat': lat, 'lon': lon}
            elif child.tag == "way":
                id = child.attrib['id']
                points = []
                is_highway = False
                for item_child in child:
                    if item_child.tag == 'nd':
                        ref = item_child.attrib['ref']
                        points.append(ref)
                    elif item_child.tag == 'tag':
                        if item_child.attrib['k'] == "highway":
                            is_highway = True
                        elif item_child.attrib['k'] == "name" and is_highway:
                            street_name = item_child.attrib['v']
                            STREETS[id] = street_name
                            edge = Street(id, points)
                            self.edges.append(edge)

    def build_graph(self):
        graph = self.data

        for edge in self.edges:
            for ind, point in enumerate(edge.points):
                if ind == 0:
                    lat1 = NODES[point]['lat']
                    lon1 = NODES[point]['lon']

                    lat2 = NODES[edge.points[1]]['lat']
                    lon2 = NODES[edge.points[1]]['lon']

                    cost = vincenty((lat1, lon1), (lat2, lon2)).meters

                    if point in graph:
                        graph[point].append(Node(edge.points[1], edge.street_id, cost))
                    else:
                        graph[point] = [Node(edge.points[1], edge.street_id, cost)]
                elif ind == len(edge.points) - 1:
                    lat1 = NODES[point]['lat']
                    lon1 = NODES[point]['lon']

                    lat2 = NODES[edge.points[-2]]['lat']
                    lon2 = NODES[edge.points[-2]]['lon']

                    cost = vincenty((lat1, lon1), (lat2, lon2)).meters

                    if point in graph:
                        graph[point].append(Node(edge.points[-2], edge.street_id, cost))
                    else:
                        graph[point] = [Node(edge.points[-2], edge.street_id, cost)]
                else:
                    lat1 = NODES[point]['lat']
                    lon1 = NODES[point]['lon']

                    lat2 = NODES[edge.points[ind - 1]]['lat']
                    lon2 = NODES[edge.points[ind - 1]]['lon']

                    cost1 = vincenty((lat1, lon1), (lat2, lon2)).meters

                    lat1 = NODES[point]['lat']
                    lon1 = NODES[point]['lon']

                    lat2 = NODES[edge.points[ind + 1]]['lat']
                    lon2 = NODES[edge.points[ind + 1]]['lon']

                    cost2 = vincenty((lat1, lon1), (lat2, lon2)).meters

                    if point in graph:
                        graph[point].extend([Node(edge.points[ind - 1], edge.street_id, cost1),
                                             Node(edge.points[ind + 1], edge.street_id, cost2)])
                    else:
                        graph[point] = [Node(edge.points[ind - 1], edge.street_id, cost1),
                                        Node(edge.points[ind + 1], edge.street_id, cost2)]

    def search_start_and_end(self, giv_start, giv_end):

        start = 0
        end = 0
        min_dist_start = 10000
        min_dist_end = 10000

        for node in self.data:
            # for start
            new_dist = vincenty((NODES[node]['lat'], NODES[node]['lon']),
                                (giv_start[0], giv_start[1])).meters
            if new_dist <= min_dist_start:
                start = node
                min_dist_start = new_dist

            # for end
            new_dist = vincenty((NODES[node]['lat'], NODES[node]['lon']),
                                (giv_end[0], giv_end[1])).meters
            if new_dist <= min_dist_end:
                end = node
                min_dist_end = new_dist

        return start, end

    def heuristic(self, a, b):
        lat1 = float(NODES[a]['lat'])
        lon1 = float(NODES[a]['lon'])

        lat2 = float(NODES[b]['lat'])
        lon2 = float(NODES[b]['lon'])

        return abs(lat1 - lat2) + abs(lon1 - lon2)

    def search_path(self, giv_start, giv_end):  # A* algorithm
        pair = self.search_start_and_end(giv_start, giv_end)
        start = pair[0]
        end = pair[1]

        frontier = PriorityQueue()
        frontier.put(start, 0)
        came_from = {}
        cost_so_far = {}
        came_from[start] = None
        cost_so_far[start] = 0

        while not frontier.empty():
            current = frontier.get()

            if current == end:
                break

            for next in self.data[current]:
                new_cost = cost_so_far[current] + next.cost
                if next.node_id not in cost_so_far or new_cost < cost_so_far[next.node_id]:
                    cost_so_far[next.node_id] = new_cost
                    priority = new_cost + self.heuristic(end, next.node_id)
                    frontier.put(next.node_id, priority)
                    # came_from[next.node_id] = (current, next.street_id)
                    came_from[next.node_id] = current

        res_path = []

        # res_path.append(end)
        res_path.append([NODES[end]['lat'], NODES[end]['lon']])
        prev = came_from[end]
        while True:
            res_path.append([NODES[prev]['lat'], NODES[prev]['lon']])
            prev = came_from[prev]
            if prev == start:
                res_path.append([NODES[prev]['lat'], NODES[prev]['lon']])
                break
        res_path.reverse()

        return res_path


def print_path(nodes_list):
    cur_street = STREETS[nodes_list[0][1]]
    print(cur_street + ": ")

    lat = NODES[nodes_list[0][0]]['lat']
    lon = NODES[nodes_list[0][0]]['lon']

    print("(" + lat + ", " + lon + ")", end=" ")
    for node in nodes_list[1:]:
        lat = NODES[node[0]]['lat']
        lon = NODES[node[0]]['lon']

        if node[1] == None:
            print("(" + lat + ", " + lon + ")", end=" ")
            break
        if STREETS[node[1]] == cur_street:
            print("(" + lat + ", " + lon + ")", end=" ")
        else:
            cur_street = STREETS[node[1]]
            print('\n' + cur_street + ": ")

            print("(" + lat + ", " + lon + ")", end=" ")

    #
    # graph = Graph("map2.osm")
    # path = graph.search_path(giv_start, giv_end)
    # print_path(path)
