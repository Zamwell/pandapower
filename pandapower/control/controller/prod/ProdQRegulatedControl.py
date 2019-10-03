# -*- coding: utf-8 -*-
"""
Created on Tue Sep 24 14:26:35 2019

@author: Utilisateur
"""

from pandapower.control.controller.prod_control import ProdController

class ProdQRegulatedControl(ProdController):
    """
    Models a Q regulated Production
    """

    def __init__(self, net, gid, data_source, pmax):
        super(ProdQRegulatedControl, self).__init__(net, gid)
    
        # profile attributes
        self.data_source = data_source
        self.last_time_step = None
        self.p_max = pmax
        
    def time_step(self, time):
        self.last_time_step = time
    
        # read new values from a profile
        if self.data_source:
            self.p_mw = self.data_source.get_time_step_value(time_step=time,
                                                             profile_name="prod")
        
    def write_to_net(self):
        # on check 
        self.net.sgen.at[self.gid, "p_mw"] = self.p_mw
        self.net.sgen.at[self.gid, "q_mvar"] = self.q_mvar
        
    def initialize_control(self):
        # at the beginning of each time step reset applied-flag
        self.applied = False
    
    def is_converged(self):
        # calculate convergence criteria
        if not self.net['sgen'].at[self.gid, 'in_service']:
            return True
        u = self.net.res_bus.at[self.bus, "vm_pu"]
        p = self.p_max
        q = self.net.res_sgen.at[self.gid, "q_mvar"]
        if 0.9725 < u < 1.0375:
            return q == 0
        elif u <= 0.96:
            return q == -p*0.4
        elif u >= 1.05:
            return q == p*0.35
        elif 0.96 < u <= 0.9725:
            return (-0.05*p <= q + p*0.4*(0.9725-u)/0.0125 <= 0.05*p)
        elif 1.0375 <= u < 1.05:
            return (-0.05 * p <= q - p*0.35(u - 1.0375)/0.0125 <= 0.05*p)
        return False

    def control_step(self):
        # apply control strategy
        u = self.net.res_bus.at[self.bus, "vm_pu"]
        p = self.p_max
        if 0.9725 < u < 1.0375:
            q = 0
        elif u <= 0.96:
            q =  -p*0.4
        elif u >= 1.05:
            q = p*0.35
        elif 0.96 < u <= 0.9725:
            q = -p*0.4*(0.9725-u)/0.0125
        elif 1.0375 <= u < 1.05:
            q = p*0.35(u - 1.0375)/0.0125
        self.q_mvar = q
        self.write_to_net()