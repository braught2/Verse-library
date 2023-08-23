from enum import Enum, auto
import copy
from typing import List

class PedestrianMode(Enum):
    Normal=auto()

class VehicleMode(Enum):
    Normal = auto()
    Brake = auto()
    Accel = auto()
    HardBrake = auto()

class State:
    x: float 
    y: float 
    theta: float 
    v: float 
    dist: float 
    agent_mode: VehicleMode 

    def __init__(self, x, y, theta, v, dist, agent_mode: VehicleMode):
        pass 

def decisionLogic(ego: State, other: State):
    output = copy.deepcopy(ego)
    if ego.agent_mode == VehicleMode.Normal and ego.dist < 30 :
        output.agent_mode = VehicleMode.HardBrake 

    if (ego.agent_mode == VehicleMode.Brake or ego.agent_mode == VehicleMode.HardBrake) and ego.dist>35 and other.y>3:
        output.agent_mode = VehicleMode.Accel

    assert ego.dist > 2.0

    return output 