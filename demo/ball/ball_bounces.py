from verse.plotter.plotter2D import *
from verse.agents.example_agent.ball_agent import BallAgent
from verse.map.example_map.simple_map2 import SimpleMap3
from verse import Scenario, ScenarioConfig
from enum import Enum, auto
import copy

# from verse.map import Lane


class BallMode(Enum):
    '''NOTE: Any model should have at least one mode
    The one mode of this automation is called "Normal" and auto assigns it an integer value.'''
    NORMAL = auto()

class State:
    '''Defines the state variables of the model
    Both discrete and continuous variables
    '''
    x: float
    y = 0.0
    vx = 0.0
    vy = 0.0
    mode: BallMode

    def __init__(self, x, y, vx, vy, ball_mode: BallMode):
        pass

def decisionLogic(ego: State):
    '''Computes the possible mode transitions'''
    # Stores the prestate first
    output = copy.deepcopy(ego)
    if ego.x < 0:
        output.vx = -ego.vx
        output.x = 0
    if ego.y < 0:
        output.vy = -ego.vy
        output.y = 0
    if ego.x > 20:
        # TODO: Q. If I change this to ego.x >= 20 then the model does not work.
        # I suspect this is because the same transition can be take many, many times.
        # We need to figure out a clean solution
        output.vx = -ego.vx
        output.x = 20
    if ego.y > 20:
        output.vy = -ego.vy
        output.y = 20
    return output


if __name__ == "__main__":
    #Defining and using a scenario involves the following 5 easy steps:
    #1. creating a basic scenario object with Scenario()
    #2. defining the agents that will populate the object, here we have two ball agents
    #3. adding the agents to the scenario using .add_agent()
    #4. initializing the agents for this scenario.
    #   Note that agents are only initialized *in* a scenario, not individually outside a scenario
    #5. genetating the simulation traces or computing the reachable states
    from verse.scenario import Scenario, ScenarioConfig
    from verse.analysis import ReachabilityMethod
    from verse.starsproto.starset import StarSet
    import polytope as pc
    initial_set_polytope_1 = pc.box2poly([[5,15], [10,10], [2,2], [2,2]])
    initial_set_polytope_2 = pc.box2poly([[15,15], [1,1], [1,1], [-2,-2]])

    bouncingBall = Scenario(ScenarioConfig(parallel=False))  # scenario too small, parallel too slow
    BALL_CONTROLLER = "./demo/ball/ball_bounces.py"
    myball1 = BallAgent("red-ball", file_name=BALL_CONTROLLER)
    myball1.set_initial(StarSet.from_polytope(initial_set_polytope_1), (BallMode.NORMAL,))
    myball2 = BallAgent("green-ball", file_name=BALL_CONTROLLER)
    myball2.set_initial(StarSet.from_polytope(initial_set_polytope_2), (BallMode.NORMAL,))

    bouncingBall.add_agent(myball1)
    bouncingBall.add_agent(myball2)
    

    #bouncingBall.set_init(
    #    [StarSet.from_polytope(initial_set_polytope_1), StarSet.from_polytope(initial_set_polytope_2)],
    #    [(BallMode.NORMAL,), (BallMode.NORMAL,)],
    #)

    bouncingBall.config.reachability_method = ReachabilityMethod.STAR_SETS

    # TODO: We should be able to initialize each of the balls separately
    # this may be the cause for the VisibleDeprecationWarning
    # TODO: Longer term: We should initialize by writing expressions like "-2 \leq myball1.x \leq 5"
    # "-2 \leq myball1.x + myball2.x \leq 5"
    #traces = bouncingBall.simulate_simple(40, 0.01, 6)
    # TODO: There should be a print({traces}) function
    #fig = go.Figure()
    #fig = simulation_tree(traces, None, fig, 1, 2, [1, 2], "fill", "trace")
    #fig.show()
    traces_veri = bouncingBall.verify(20, 0.01, 6)


    import plotly.graph_objects as go
    from verse.plotter.plotterStar import *

    plot_reachtube_stars(traces_veri, None, 0 , 1)
