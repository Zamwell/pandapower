# -*- coding: utf-8 -*-
"""
Created on Tue Sep 24 14:26:35 2019

@author: Utilisateur
"""

from pandapower.control.basic_controller import Controller

class AggControl(Controller):
    """
    Models a Q regulated Production
    """

    def __init__(self, net, in_service = True, level = 0, order = 0, recycle = False):
        super().__init__(net, in_service=in_service, level=level, order=order, recycle=recycle)
        self.update_initialized(locals())
    
        # profile attributes
        self.last_time_step = None
        self.applied = False
        
    def time_step(self, time):
        pass
        
    def write_to_net(self):
        # on check 
        self.net.sgen.at[self.gid, "p_mw"] = self.p_mw
        self.net.sgen.at[self.gid, "q_mvar"] = self.q_mvar
        
    def initialize_control(self):
        # at the beginning of each time step reset applied-flag
        self.applied = False
    
    def is_converged(self):
        # calculate convergence criteria
        return self.applied

    def control_step(self):
        # apply control strategy
        nb_ev = self.net.storage[self.net.storage.in_service == True].shape[0]
        sorted_loads = self.net.res_bus[self.net.res_bus.index.isin(self.net.load.bus.unique())].sort_values(by = ['p_mw', 'vm_pu'])['p_mw']
        nb_ev_freqreg = 0
        for bus,load in sorted_loads.iteritems():
            for ind,soc in self.net.storage[(self.net.storage.bus == bus) & (self.net.storage.in_service == True)].sort_values(by = ['soc_percent'])['soc_percent'].iteritems():
                control_ev = self.net.controller.controller[ind + 10] #+ 10 parce que de 0 à 10 c'est les controller des charges/productions
                if nb_ev_freqreg <= 0.8 * nb_ev:
                    control_ev.switch_mode('freq_reg')
                    nb_ev_freqreg += 1
                else:
                    control_ev.switch_mode('basic')
        self.applied = True
        