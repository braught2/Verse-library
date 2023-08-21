from typing import Tuple, List 

import numpy as np 
from scipy.integrate import ode 

from verse import BaseAgent, Scenario
from verse.analysis.utils import wrap_to_pi 
from verse.analysis.analysis_tree import TraceType, AnalysisTree 
from verse.parser import ControllerIR
from vehicle_controller import VehicleMode, PedestrainMode

import copy 

def tree_safe(tree: AnalysisTree):
    for node in tree.nodes:
        if node.assert_hits is not None:
            return False 
    return True

def verify_refine(init_car, init_ped, scenario: Scenario):
    partition_depth = 0
    init_queue = [(init_car, init_ped, partition_depth)]
    res_list = []
    while init_queue!=[] and partition_depth < 10:
        car_init, ped_init, partition_depth = init_queue.pop(0)
        print(f"######## {partition_depth}, {car_init[0][3]}, {car_init[1][3]}")
        scenario.set_init_single('car', car_init, (VehicleMode.Normal,))
        scenario.set_init_single('pedestrain', ped_init, (PedestrainMode.Normal,))
        traces = scenario.verify(30, 0.05)
        if not tree_safe(traces):
            # Partition car and pedestrain initial state
            # if partition_depth%3==0:
            #     car_x_init = (car_init[0][0] + car_init[1][0])/2
            #     car_init1 = copy.deepcopy(car_init)
            #     car_init1[1][0] = car_x_init 
            #     init_queue.append((car_init1, ped_init, partition_depth+1))
            #     car_init2 = copy.deepcopy(car_init)
            #     car_init2[0][0] = car_x_init 
            #     init_queue.append((car_init2, ped_init, partition_depth+1))
            # else:
            if car_init[1][3] - car_init[0][3] < 0.01 or partition_depth >= 10:
                print('Threshold Reached. Stop Refining')
                res_list.append(traces)
                continue
            car_v_init = (car_init[0][3] + car_init[1][3])/2
            car_init1 = copy.deepcopy(car_init)
            car_init1[1][3] = car_v_init 
            init_queue.append((car_init1, ped_init, partition_depth+1))
            car_init2 = copy.deepcopy(car_init)
            car_init2[0][3] = car_v_init 
            init_queue.append((car_init2, ped_init, partition_depth+1))
        else:
            res_list.append(traces)
    return res_list

class PedestrainAgent(BaseAgent):
    def __init__(
        self, 
        id, 
    ):
        self.decision_logic: ControllerIR = ControllerIR.empty()
        self.id = id 

    @staticmethod
    def dynamic(t, state):
        x, y, theta, v, _ = state
        x_dot = 0
        y_dot = v
        theta_dot = 0
        v_dot = 0
        return [x_dot, y_dot, theta_dot, v_dot, 0]    

    def TC_simulate(
        self, mode: List[str], init, time_bound, time_step, lane_map = None
    ) -> TraceType:
        time_bound = float(time_bound)
        num_points = int(np.ceil(time_bound / time_step))
        trace = np.zeros((num_points + 1, 1 + len(init)))
        trace[1:, 0] = [round(i * time_step, 10) for i in range(num_points)]
        trace[0, 1:] = init
        for i in range(num_points):
            r = ode(self.dynamic)
            r.set_initial_value(init)
            res: np.ndarray = r.integrate(r.t + time_step)
            init = res.flatten()
            if init[3] < 0:
                init[3] = 0
            trace[i + 1, 0] = time_step * (i + 1)
            trace[i + 1, 1:] = init
        return trace

class VehicleAgent(BaseAgent):
    def __init__(
        self, 
        id, 
        code = None,
        file_name = None, 
        accel_brake = 5,
        accel_notbrake = 5,
        accel_hardbrake = 20,
        speed = 10
    ):
        super().__init__(
            id, code, file_name
        )
        self.accel_brake = accel_brake
        self.accel_notbrake = accel_notbrake
        self.accel_hardbrake = accel_hardbrake
        self.speed = speed
         
    @staticmethod
    def dynamic(t, state, u):
        x, y, theta, v, _ = state
        delta, a = u
        x_dot = v * np.cos(theta + delta)
        y_dot = v * np.sin(theta + delta)
        theta_dot = v / 1.75 * np.sin(delta)
        v_dot = a
        return [x_dot, y_dot, theta_dot, v_dot, 0]
    
    def action_handler(self, mode: List[str], state) -> Tuple[float, float]:
        x, y, theta, v, _ = state
        vehicle_mode,  = mode
        vehicle_pos = np.array([x, y])
        a = 0
        lane_width = 3
        d = -y
        if vehicle_mode == "Normal" or vehicle_mode == "Stop":
            pass
        elif vehicle_mode == "SwitchLeft":
            d += lane_width
        elif vehicle_mode == "SwitchRight":
            d -= lane_width
        elif vehicle_mode == "Brake":
            a = max(-self.accel_brake, -v)
            # a = -50
        elif vehicle_mode == "HardBrake":
            a = max(-self.accel_hardbrake, -v)
            # a = -50
        elif vehicle_mode == "Accel":
            a = min(self.accel_notbrake, self.speed - v)
        else:
            raise ValueError(f"Invalid mode: {vehicle_mode}")

        heading = 0
        psi = wrap_to_pi(heading - theta)
        steering = psi + np.arctan2(0.45 * d, v)
        steering = np.clip(steering, -0.61, 0.61)
        return steering, a

    def TC_simulate(
        self, mode: List[str], init, time_bound, time_step, lane_map = None
    ) -> TraceType:
        time_bound = float(time_bound)
        num_points = int(np.ceil(time_bound / time_step))
        trace = np.zeros((num_points + 1, 1 + len(init)))
        trace[1:, 0] = [round(i * time_step, 10) for i in range(num_points)]
        trace[0, 1:] = init
        for i in range(num_points):
            steering, a = self.action_handler(mode, init)
            r = ode(self.dynamic)
            r.set_initial_value(init).set_f_params([steering, a])
            res: np.ndarray = r.integrate(r.t + time_step)
            init = res.flatten()
            if init[3] < 0:
                init[3] = 0
            trace[i + 1, 0] = time_step * (i + 1)
            trace[i + 1, 1:] = init
        return trace

def dist(pnt1, pnt2):
    return np.linalg.norm(
        np.array(pnt1) - np.array(pnt2)
    )

def get_extreme(rect1, rect2):
    lb11 = rect1[0]
    lb12 = rect1[1]
    ub11 = rect1[2]
    ub12 = rect1[3]

    lb21 = rect2[0]
    lb22 = rect2[1]
    ub21 = rect2[2]
    ub22 = rect2[3]

    # Using rect 2 as reference
    left = lb21 > ub11 
    right = ub21 < lb11 
    bottom = lb22 > ub12
    top = ub22 < lb12

    if top and left: 
        dist_min = dist((ub11, lb12),(lb21, ub22))
        dist_max = dist((lb11, ub12),(ub21, lb22))
    elif bottom and left:
        dist_min = dist((ub11, ub12),(lb21, lb22))
        dist_max = dist((lb11, lb12),(ub21, ub22))
    elif top and right:
        dist_min = dist((lb11, lb12), (ub21, ub22))
        dist_max = dist((ub11, ub12), (lb21, lb22))
    elif bottom and right:
        dist_min = dist((lb11, ub12),(ub21, lb22))
        dist_max = dist((ub11, lb12),(lb21, ub22))
    elif left:
        dist_min = lb21 - ub11 
        dist_max = np.sqrt((lb21 - ub11)**2 + max((ub22-lb12)**2, (ub12-lb22)**2))
    elif right: 
        dist_min = ub21 - lb11 
        dist_max = np.sqrt((lb21 - ub11)**2 + max((ub22-lb12)**2, (ub12-lb22)**2))
    elif top: 
        dist_min = lb12 - ub22
        dist_max = np.sqrt((ub12 - lb22)**2 + max((ub21-lb11)**2, (ub11-lb21)**2))
    elif bottom: 
        dist_min = lb22 - ub12 
        dist_max = np.sqrt((ub22 - lb12)**2 + max((ub21-lb11)**2, (ub11-lb21)**2)) 
    else: 
        dist_min = 0 
        dist_max = max(
            dist((lb11, lb12), (ub21, ub22)),
            dist((lb11, ub12), (ub21, lb22)),
            dist((ub11, lb12), (lb21, ub12)),
            dist((ub11, ub12), (lb21, lb22))
        )
    return dist_min, dist_max

class VehiclePedestrainSensor:
    # The baseline sensor is omniscient. Each agent can get the state of all other agents
    def sense(self, agent: BaseAgent, state_dict, lane_map):
        len_dict = {}
        cont = {}
        disc = {}
        len_dict = {"others": len(state_dict) - 1}
        tmp = np.array(list(state_dict.values())[0][0])
        if tmp.ndim < 2:
            if agent.id == 'car':
                len_dict['others'] = 1 
                cont['ego.x'] = state_dict['car'][0][1]
                cont['ego.y'] = state_dict['car'][0][2]
                cont['ego.theta'] = state_dict['car'][0][3]
                cont['ego.v'] = state_dict['car'][0][4]
                cont['ego.dist'] = np.sqrt(
                    (state_dict['car'][0][1]-state_dict['pedestrain'][0][1])**2+\
                    (state_dict['car'][0][2]-state_dict['pedestrain'][0][2])**2
                )
                disc['ego.agent_mode'] = state_dict['car'][1][0]
        else:
            if agent.id == 'car':
                len_dict['others'] = 1 
                cont['ego.x'] = [
                    state_dict['car'][0][0][1], state_dict['car'][0][1][1]
                ]
                cont['ego.y'] = [
                    state_dict['car'][0][0][2], state_dict['car'][0][1][2]
                ]
                cont['ego.theta'] = [
                    state_dict['car'][0][0][3], state_dict['car'][0][1][3]
                ]
                cont['ego.v'] = [
                    state_dict['car'][0][0][4], state_dict['car'][0][1][4]
                ]
                dist_min, dist_max = get_extreme(
                    (state_dict['car'][0][0][1],state_dict['car'][0][0][2],state_dict['car'][0][1][1],state_dict['car'][0][1][2]),
                    (state_dict['pedestrain'][0][0][1],state_dict['pedestrain'][0][0][2],state_dict['pedestrain'][0][1][1],state_dict['pedestrain'][0][1][2]),
                )
                # dist_list = []
                # if state_dict['car'][0][0][0] < state_dict['pedestrain'][0][0][0]
                # for a in range(2):
                #     for b in range(2):
                #         for c in range(2):
                #             for d in range(2):
                #                 dist = np.sqrt(
                #                     (state_dict['car'][0][a][0] - state_dict['pedestrain'][0][b][0])**2+\
                #                     (state_dict['car'][0][c][1] - state_dict['pedestrain'][0][d][1])**2
                #                 )
                #                 dist_list.append(dist)
                cont['ego.dist'] = [
                    dist_min, dist_max
                ]
                # print(dist_min)
                disc['ego.agent_mode'] = state_dict['car'][1][0]
        return cont, disc, len_dict
