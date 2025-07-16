from ..model.vehical_model import Vehicle_Input, Vehicle_State, Dynamics_Model
import casadi

class Model_Predictive_Contol():

    def __init__(self,timestep:float,):
        self.timestep = timestep
        self.horizon = 50

        self.dynamics_model = Dynamics_Model(timestep=timestep)
        
    def forward_simulation(self, initial_state:Vehicle_State, inputs:list[Vehicle_Input]) -> list[Vehicle_State]:
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
    def cost_function(self,initial_state:Vehicle_State,inputs:list[Vehicle_Input]) -> float:
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

    def main(self) -> Vehicle_Input:
        """This function is the main model predictive control loop.
        It should minimize the cost of the path by creating a set of inputs to 
        follow a dynamically feasible trajectory, 
        without violating the constraints (going off track)
        
        Returns:
            Vehicle_Input -- the inputs to be passed to the car
        """

        # calculate cost for a bunch of different states, use the one with the lowest cost
        

        return 