# -*- coding: utf-8 -*-
"""
Created on Tue Sep 24 14:26:35 2019

@author: Utilisateur
"""

from pandapower.control.controller.storage_control import StorageController

class EVControl(StorageController):
    """
    Models a EV
    """

    def __init__(self, net, gid, data_source, efficiency = 1):
        super(EVControl, self).__init__(net, gid)
    
        # profile attributes
        self.bus_residence = self.bus
        self.data_source = data_source #emplacement (=endroit ou est la voiture) et capacité actuelle de la batterie
        self.last_time_step = None
        self.emplacement = None
        self.applied = False
        self.efficiency = efficiency
        self.socmin = None
        self.reserve = 0
        self.fluct_freq = 0
        
    def time_step(self, time):
        if self.in_service:
            #gérer SOC (parce que si l'ev est branchée elle a pu se charger/décharger avec le réseau)
            p_fin = self.p_mw + self.fluct_freq * self.reserve
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
            self.fluct_freq = self.data_source.get_time_step_value(time_step = time, profile_name = "freq")
        self.in_service = (self.emplacement == 0)
        self.soc_limit()
        self.changement_endroit()
        #On met en service le noeud sur le réseau si l'ev est sur place (on attend pas la suite, c'est pas très utile)
        self.write_to_net()
        
    def write_to_net(self):
        # on check 
        self.net.storage.at[self.gid, "in_service"] = self.in_service
        self.net.storage.at[self.gid, "bus"] = self.bus
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
        if self.in_service:
            p_withdrawn = - min(0.01 / self.efficiency, max(self.max_e_mwh * (self.soc_percent - self.socmin) * 4, -0.01 * self.efficiency))
            p_inject = min (0.01 * self.efficiency, self.max_e_mwh * (1 - self.soc_percent) * 4)
            if p_withdrawn < 0:
                p_withdrawn = p_withdrawn * self.efficiency
            else:
                p_withdrawn = p_withdrawn / self.efficiency
            if p_inject < 0:
                p_inject = p_inject * self.efficiency
            else:
                p_inject = p_inject / self.efficiency
            self.p_mw = (p_withdrawn + p_inject)/2
            self.reserve = abs(p_inject - self.p_mw)
#            if self.soc_percent <= self.socmin: #strat débile, charge max dès qu'on peut
#                self.p_mw = 0.1
#            else:
#                self.p_mw = 0
        else:
            self.p_mw = 0
        self.write_to_net()
        self.applied = True


    def changement_endroit(self):
        if self.emplacement == 2:
            self.bus  = 10
            self.in_service = True
        else:
            self.bus = self.bus_residence
