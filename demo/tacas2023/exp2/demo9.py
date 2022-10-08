from verse.agents.example_agent import CarAgent, NPCAgent
from verse.map.example_map import SimpleMap3, SimpleMap6
from verse import Scenario
# from noisy_sensor import NoisyVehicleSensor
from verse.plotter.plotter2D import *
# from verse.plotter.plotter2D_old import plot_reachtube_tree, plot_map

from enum import Enum, auto
import plotly.graph_objects as go
import matplotlib.pyplot as plt


class LaneObjectMode(Enum):
    Vehicle = auto()
    Ped = auto()        # Pedestrians
    Sign = auto()       # Signs, stop signs, merge, yield etc.
    Signal = auto()     # Traffic lights
    Obstacle = auto()   # Static (to road/lane) obstacles


class VehicleMode(Enum):
    Normal = auto()
    SwitchLeft = auto()
    SwitchRight = auto()
    Brake = auto()


class TrackMode(Enum):
    T0 = auto()
    T1 = auto()
    T2 = auto()
    M01 = auto()
    M12 = auto()
    M21 = auto()
    M10 = auto()


class State:
    x: float
    y: float
    theta: float
    v: float
    agent_mode: VehicleMode
    lane_mode: TrackMode

    def __init__(self, x, y, theta, v, agent_mode: VehicleMode, lane_mode: TrackMode):
        pass


if __name__ == "__main__":
    input_code_name = './demo/tacas2023/exp2/example_controller5.py'
    scenario = Scenario()

    car = CarAgent('car1', file_name=input_code_name)
    scenario.add_agent(car)
    car = NPCAgent('car2')
    scenario.add_agent(car)
    car = NPCAgent('car3')
    scenario.add_agent(car)
    tmp_map = SimpleMap3()
    scenario.set_map(tmp_map)
    scenario.set_init(
        [
            [[5, -0.5, 0, 1.0], [5.5, 0.5, 0, 1.0]],
            [[20, -0.2, 0, 0.5], [20, 0.2, 0, 0.5]],
            [[4-2.5, 2.8, 0, 1.0], [4.5-2.5, 3.2, 0, 1.0]],
        ],
        [
            (VehicleMode.Normal, TrackMode.T1),
            (VehicleMode.Normal, TrackMode.T1),
            (VehicleMode.Normal, TrackMode.T0),
        ]
    )

    scenario.init_seg_length = 5
    traces = scenario.verify(40, 0.1, params={"bloating_method": 'GLOBAL'})
    traces.dump("./output1.json")
    traces = AnalysisTree.load('./output1.json')
    fig = go.Figure()
    fig = reachtube_tree(traces, tmp_map, fig, 1, 2, [1, 2], 'lines', 'trace')
    fig.show()

    fig = go.Figure()
    fig = reachtube_anime(traces, tmp_map, fig, 1,
                          2, 'lines', 'trace', combine_rect=1)
    fig.show()
