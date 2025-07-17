from model.vehical_model import Vehicle_Input, Vehicle_State, Dynamics_Model
import casadi
import numpy as np
from scipy.optimize import minimize
from typing import List
from nav_msgs.msg import Path

class Model_Predictive_Contol():

    def __init__(self,timestep:float,):
        self.timestep = timestep
        self.horizon = 50

        self.dynamics_model = Dynamics_Model(timestep=timestep)
        self.previous_inputs = [Vehicle_Input(1,0) for x in range(self.horizon)]
        
    def forward_simulation(self, initial_state:Vehicle_State, inputs:List[Vehicle_Input]) -> List[Vehicle_State]:
        """This function should make a predicted path based upon the current state of the car, and the given inputs
        
        Returns:
            path - the predicted sequence of states that the car should go through
        """

        states = [initial_state]
        
        #reset state of model
        self.dynamics_model.set_state(initial_state)


        # calculate each state on the path (model stores its own state after each calculation)
        for i in range(1,self.horizon):
            self.dynamics_model.calculate_next_state(input=inputs[i])
            states.append(self.dynamics_model.get_state())

        return states

    def stage_cost(self, state:Vehicle_State,input:Vehicle_Input) -> float:
        pass
    def cost_function(self,initial_state:Vehicle_State,inputs:List[Vehicle_Input],required_path) -> float:
        """This function should calculate the cost of any given route.
        It should do this by computing the sum of the cost of each individual stage.
        
        Arguments:
            state {Vehical_state} -- the current state of the car
            inputs {list[Vehicle_input]} -- a chronological list of each input the car will use on its route

        Returns:
            cost -- the cost of a route"""
        
        #use forward simulation to calculate the predicted states
        states = self.forward_simulation(initial_state=initial_state,inputs=inputs)

        #calculate the cost for each and sum them
        total_cost = 0
        for i in range(0,self.horizon):
            total_cost += self.stage_cost(state=states,input=inputs[i])

        return total_cost

    def main(self,initial_state:Vehicle_State,required_path:Path,inputs=[Vehicle_Input(1,0) for x in range(50)]) -> Vehicle_Input:
        """This function is the main model predictive control loop.
        It should minimize the cost of the path by creating a set of inputs to 
        follow a dynamically feasible trajectory, 
        without violating the constraints (going off track)
        
        Returns:
            Vehicle_Input -- the inputs to be passed to the car
        """

        # calculate cost for a bunch of different states, use the one with the lowest cost
        
        if inputs == None:
            inputs = self.previous_inputs
        if required_path == None: # if no path, dont do anything
            return Vehicle_Input(acceleration=0.0,steering_angle=0.0)

        # Initial guess: flatten list of Vehicle_Input into [a0, s0, a1, s1, ...]
        u0 = np.array([1, 0] * self.horizon)

        # Bounds for acceleration and steering (example: acceleration [-5, 5], steering [-0.5, 0.5])
        bounds = [(-5, 5), (-0.5, 0.5)] * self.horizon

        def unpack_inputs(u):
            """Convert flat array to list of Vehicle_Input."""
            return [Vehicle_Input(u[2*i], u[2*i+1]) for i in range(self.horizon)]

        def objective(u):
            inputs = unpack_inputs(u)
            return self.cost_function(initial_state, inputs,required_path)

        res = minimize(objective, u0, bounds=bounds, method='SLSQP', options={'maxiter': 100, 'disp': True})

        best_inputs = unpack_inputs(res.x)
        return best_inputs[0]  # Return the first input to apply now
