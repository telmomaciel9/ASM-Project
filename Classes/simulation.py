#pip install osmnx networkx matplotlib scikit-learn Pillow

import osmnx as ox
import networkx as nx
import matplotlib.pyplot as plt
import tkinter as tk
from PIL import Image, ImageTk
from geopy.distance import geodesic
import time

def _download_map_area(position, distance):
    """ Download a square map of 'distance' meters around the 'point' """
    return ox.graph_from_point(position.tuple(), dist=distance, network_type='drive')

def _save_map_as_image(G, file_path, center_position, dist=1000, image_size=(800, 800)):
    # Get the bounding box of the desired area
    bbox = ox.utils_geo.bbox_from_point(center_position.tuple(), dist=dist)
    north, south, east, west = bbox

    # Plot and save the graph to an image file
    fig, ax = ox.plot_graph(G, bbox=(north, south, east, west), show=False, close=True, node_size=0)

    # Save the figure to a temporary file
    fig.savefig(file_path, dpi=300, bbox_inches='tight', pad_inches=0)
    plt.close(fig)

    # Open the image and resize it to fit the window
    map_image = Image.open(file_path)
    map_image = map_image.resize(image_size, Image.LANCZOS)
    map_image.save(file_path)  # Save the resized image to the desired file path
    return bbox, map_image

def _latlon_to_pixels(lat, lon, bbox, image_size):
    """ Convert latitude and longitude to pixel coordinates. """
    north, south, east, west = bbox
    x_ratio = image_size[0] / (east - west)
    y_ratio = image_size[1] / (north - south)
    
    x_pixels = (lon - west) * x_ratio
    y_pixels = image_size[1] - ((lat - south) * y_ratio)  # Invert y for graphical coordinate system
    return (int(x_pixels), int(y_pixels))

class Simulator:
    def __init__(self, images_directory, n_collectors, n_trashes, center_location, trash_positions):
        assert n_trashes == len(trash_positions)

        map_image_path = f'{images_directory}/map_image.png'
        truck_image_path = f'{images_directory}/truck_icon.png'
        trash_image_path = f'{images_directory}/trash_icon.png'

        # Calculate the maximum distance to any trash position
        center_distance = self.calculate_center_distance(trash_positions, center_location) + 100  # Add buffer distance
        
        self.image_size = (800, 800)
        self.G = _download_map_area(center_location, center_distance)  # center_distance are the meters around the center visible in the map
        self.bbox, self.map_image = _save_map_as_image(self.G, map_image_path, center_position=center_location, dist=center_distance, image_size=self.image_size)
        # Initialize the main window
        self.root = tk.Tk()
        self.root.title('Garbage Truck Simulation')

        # Create a canvas and add it to the window
        self.canvas = tk.Canvas(self.root, width=self.image_size[0], height=self.image_size[1])
        self.canvas.pack()

        # Open and resize the truck image with Pillow
        image_truck = Image.open(truck_image_path)
        truck_width, truck_height = 20, 20
        image_truck = image_truck.resize((truck_width, truck_height), Image.LANCZOS)

        # Open and resize the trash image with Pillow
        image_trash = Image.open(trash_image_path)
        trash_width, trash_height = 20, 20
        image_trash = image_trash.resize((trash_width, trash_height), Image.LANCZOS)

        # Load and display the map image
        global map_image_tk
        map_image_tk = ImageTk.PhotoImage(self.map_image)
        self.canvas.create_image(0, 0, anchor='nw', image=map_image_tk)

        # Load the truck icon image
        self.truck_icons = []
        self.trucks = []
        self.truck_texts = [] # text that represents occupancy of each trash collector
        for i in range(n_collectors):
            truck_icon = ImageTk.PhotoImage(image_truck)
            self.truck_icons.append(truck_icon)
            truck = self.canvas.create_image(center_location.tuple(), image=truck_icon)
            self.trucks.append(truck)
            
            # Create a text item for each truck to display occupancy
            truck_text = self.canvas.create_text(center_location.tuple(), text="0 kg", anchor="s", fill='white')
            self.truck_texts.append(truck_text)
            
        # Load the trash icon image
        self.trash_icons = []
        self.trash_texts = []
        
        for i, position in enumerate(trash_positions):
            trash_icon = ImageTk.PhotoImage(image_trash)
            self.trash_icons.append(trash_icon)
            trash = self.canvas.create_image(center_location.tuple(), image=trash_icon)
            # set trash icon positions in canvas
            position_pixels = _latlon_to_pixels(position[0], position[1], self.bbox, self.image_size)
            self.canvas.coords(trash, position_pixels)
            
            # Create a text item for each trash to display occupancy
            trash_text = self.canvas.create_text(center_location.tuple(), text="0 kg", anchor="s", fill='white')
            self.trash_texts.append(trash_text)
        
        # Record the start time
        self.start_time = time.time()

    def calculate_center_distance(self, trash_positions, center_location):
        center_coords = center_location.tuple()
        max_distance = 0
        for trash_pos in trash_positions:
            trash_coords = trash_pos.tuple()
            distance = geodesic(center_coords, trash_coords).meters
            if distance > max_distance:
                max_distance = distance
        return max_distance
        
    def update_positions(self, collector_positions, trash_positions, collector_occupancies, trash_occupancies):
        for i, position in enumerate(collector_positions):
            position_pixels = _latlon_to_pixels(position[0], position[1], self.bbox, self.image_size)
            self.canvas.coords(self.trucks[i], *position_pixels)
            self.canvas.itemconfig(self.truck_texts[i], text=f"{collector_occupancies[i]:.2f} kg")
            self.canvas.coords(self.truck_texts[i], position_pixels[0], position_pixels[1] - 10)
        for i, position in enumerate(trash_positions):
            position_pixels = _latlon_to_pixels(position[0], position[1], self.bbox, self.image_size)
            occupancy = trash_occupancies[i]
            # set the color based on the occupancy
            if occupancy <= 33:
                color = 'green'
            elif occupancy <= 66:
                color = 'orange'
            else:
                color = 'red'
            self.canvas.itemconfig(self.trash_texts[i], text=f"{occupancy:.2f} kg", fill=color)
            self.canvas.coords(self.trash_texts[i], position_pixels[0], position_pixels[1] - 10)
        self.root.update_idletasks()

    def stop(self, trash_agents, collector_agents):
        # Calculate the elapsed time
        elapsed_time = time.time() - self.start_time
        total_initial_occupancy = sum([trash.initial_occupancy for trash in trash_agents])
        total_n_trips = sum([collector.n_trips for collector in collector_agents])
        # Print the elapsed time
        print(f"Simulation ended. Elapsed time: {elapsed_time:.2f} seconds.\n\
        Total initial trash occupancy: {total_initial_occupancy:.2f}kg\n\
        Total collectors trips: {total_n_trips}")
        # Destroy the Tkinter window
        self.root.destroy()
