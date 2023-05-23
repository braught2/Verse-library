# Example agent.
from typing import Tuple, List

import numpy as np
from scipy.integrate import ode

from verse import BaseAgent
from verse import LaneMap


class BallAgent(BaseAgent):
    """Dynamics of a frictionless billiard ball
    on a 2D-plane"""

    def __init__(self, id, code=None, file_name=None):
        """Contructor for tha agent
        EXACTLY one of the following should be given
        file_name: name of the controller
        code: pyhton string ddefning the controller
        """
        # Calling the constructor of tha base class
        super().__init__(id, code, file_name)

    @staticmethod
    def dynamic(t, state):
        """Defines the RHS of the ODE used to simulate trajectories"""
        x, y, vx, vy = state
        x_dot = vx
        y_dot = vy
        vx_dot = 0
        vy_dot = 0
        return [x_dot, y_dot, vx_dot, vy_dot]


if __name__ == "__main__":
    aball = BallAgent(
        "red_ball", file_name="/Users/mitras/Dpp/GraphGeneration/demo/ball_bounces.py"
    )
    trace = aball.TC_simulate({"none"}, [5, 10, 2, 2], 10, 0.05)
    print(trace)
