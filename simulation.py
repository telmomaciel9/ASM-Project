#pip install osmnx networkx matplotlib scikit-learn Pillow

import osmnx as ox
import networkx as nx
import matplotlib.pyplot as plt
import tkinter as tk
from PIL import Image, ImageTk

def _download_map_area(position, distance):
    """ Download a square map of 'distance' meters around the 'point' """
    return ox.graph_from_point(position.tuple(), dist=distance, network_type='drive')

def _save_map_as_image(G, file_path, center_position, dist=1000):
    # Get the bounding box of the desired area
    bbox = ox.utils_geo.bbox_from_point(center_position.tuple(), dist=dist)
    north, south, east, west = bbox

    # Plot and save the graph to an image file
    fig, ax = ox.plot_graph(G, bbox=(north, south, east, west), show=False, close=True, node_size=0)

    # Optional: Adjust the figure layout to be more tight
    #fig.tight_layout()

    fig.savefig(file_path, dpi=300, bbox_inches='tight', pad_inches=0)
    plt.close(fig)
    return bbox

def _latlon_to_pixels(lat, lon, bbox, image_size):
    """ Convert latitude and longitude to pixel coordinates. """
    north, south, east, west = bbox
    x_ratio = image_size[0] / (east - west)
    y_ratio = image_size[1] / (north - south)
    
    x_pixels = (lon - west) * x_ratio
    y_pixels = image_size[1] - ((lat - south) * y_ratio)  # Invert y for graphical coordinate system
    return (int(x_pixels), int(y_pixels))

class Simulator:
    def __init__(self, map_image_path, truck_image_path, trash_image_path, n_collectors, n_trashes, center_location, center_distance=1000):
        self.image_size = (800, 800)
        self.G = _download_map_area(center_location, center_distance)  # center_distance are the meters around the center visible in the map
        self.bbox = _save_map_as_image(self.G, map_image_path, center_location)
        # Initialize the main window
        self.root = tk.Tk()
        self.root.title('Garbage Truck Simulation')

        # Create a canvas and add it to the window
        self.canvas = tk.Canvas(self.root, width=self.image_size[0], height=self.image_size[1])
        self.canvas.pack()

        # Open and resize the map image with Pillow
        global map_image
        map_image = Image.open(map_image_path)
        map_image = map_image.resize((self.image_size[0], self.image_size[1]), Image.LANCZOS)

        # Open and resize the truck image with Pillow
        image_truck = Image.open(truck_image_path)
        truck_width, truck_height = 20, 20
        image_truck = image_truck.resize((truck_width, truck_height), Image.LANCZOS)

        # Open and resize the trash image with Pillow
        image_trash = Image.open(trash_image_path)
        trash_width, trash_height = 20, 20
        image_trash = image_trash.resize((trash_width, trash_height), Image.LANCZOS)

        # Load and display the map image
        map_image = ImageTk.PhotoImage(map_image)
        self.canvas.create_image(0, 0, anchor='nw', image=map_image)

        # Load the truck icon image
        self.truck_icons = []
        self.trucks = []
        # global truck_icon
        for i in range(n_collectors):
            truck_icon = ImageTk.PhotoImage(image_truck)
            self.truck_icons.append(truck_icon)
            truck = self.canvas.create_image(center_location.tuple(), image=truck_icon)
            self.trucks.append(truck)
            
        # Load the trash icon image
        self.trash_icons = []
        self.trashes = []
        # global truck_icon
        for i in range(n_trashes):
            trash_icon = ImageTk.PhotoImage(image_trash)
            self.trash_icons.append(trash_icon)
            trash = self.canvas.create_image(center_location.tuple(), image=trash_icon)
            self.trashes.append(trash)

    def update_positions(self, collector_positions, trash_positions):
        for i, position in enumerate(collector_positions):
            position_pixels = _latlon_to_pixels(position[0], position[1], self.bbox, self.image_size)
            self.canvas.coords(self.trucks[i], *position_pixels)
        for i, position in enumerate(trash_positions):
            position_pixels = _latlon_to_pixels(position[0], position[1], self.bbox, self.image_size)
            self.canvas.coords(self.trashes[i], *position_pixels)
        self.root.update_idletasks()
        self.root.after(10)  # Delay between each frame; lower=faster animation