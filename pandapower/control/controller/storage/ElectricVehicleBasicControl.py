# -*- coding: utf-8 -*-
"""
Created on Tue Sep 24 14:26:35 2019

@author: Utilisateur
"""

from pandapower.control.controller.storage_control import StorageController

class EVBasicControl(StorageController):
    """
    Models a EV
    """

    def __init__(self, net, gid, data_source, efficiency = 1):
        super(EVBasicControl, self).__init__(net, gid)
    
        # profile attributes
        self.data_source = data_source #emplacement (=endroit ou est la voiture) et capacité actuelle de la batterie
        self.last_time_step = None
        self.emplacement = None
        self.applied = False
        self.efficiency = efficiency
        self.socmin = None
        self.applied = False

        
    def time_step(self, time):
        if self.in_service:
            #gérer SOC (parce que si l'ev est branchée elle a pu se charger/décharger avec le réseau)
            p_fin = self.p_mw
            if p_fin > 0:
                self.soc_percent += p_fin * self.efficiency / 4 /self.max_e_mwh
            elif p_fin < 0:
                self.soc_percent += p_fin / self.efficiency / 4 /self.max_e_mwh
        self.last_time_step = time
    
        # read new values from a profile
        if self.data_source:
            self.emplacement = self.data_source.get_time_step_value(time_step=time,
                                                             profile_name="emplacement")
            self.soc_percent -= self.data_source.get_time_step_value(time_step=time,
                                                                    profile_name="nrj_utilisee") / self.max_e_mwh
            self.socmin = self.data_source.get_time_step_value(time_step = time, profile_name = "socmin")
        self.in_service = (self.emplacement == 0)
        self.soc_limit()
        #On met en service le noeud sur le réseau si l'ev est sur place (on attend pas la suite, c'est pas très utile)
        self.write_to_net()
        
    def write_to_net(self):
        # on check 
        self.net.storage.at[self.gid, "in_service"] = self.in_service
        self.net.storage.at[self.gid, "soc_percent"] = self.soc_percent
        self.net.storage.at[self.gid, "p_mw"] = self.p_mw
        
    def initialize_control(self):
        # at the beginning of each time step reset applied-flag
        self.applied = False
    
    def is_converged(self):
        # calculate convergence criteria
        return self.applied

    def control_step(self):
        # apply control strategy
        p = 0.1 * self.efficiency
        if self.in_service:
            if self.soc_percent <= self.socmin: #strat débile, charge max dès qu'on peut
                self.p_mw = 0.01
            else:
                self.p_mw = 0
        else:
            self.p_mw = 0
        self.write_to_net()
        self.applied = True
