# -*- coding: utf-8 -*-
"""
Created on Tue Sep 24 14:26:35 2019

@author: Utilisateur
"""

from pandapower.control.controller.storage_control import StorageController

class EVQRegControl(StorageController):
    """
    Models a EV
    """

    def __init__(self, net, gid, data_source, efficiency = 1):
        super(EVQRegControl, self).__init__(net, gid)
    
        # profile attributes
        self.data_source = data_source #emplacement (=endroit ou est la voiture) et capacité actuelle de la batterie
        self.last_time_step = None
        self.emplacement = None
        self.applied = False
        self.efficiency = efficiency
        self.socmin = None
        self.reserve = 0
        self.fluct_freq = 0
        self.q_mvar = 0
        
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
        self.in_service = (self.emplacement == 0)
        self.soc_limit()
        #On met en service le noeud sur le réseau si l'ev est sur place (on attend pas la suite, c'est pas très utile)
        self.write_to_net()
        
    def write_to_net(self):
        # on check 
        self.net.storage.at[self.gid, "in_service"] = self.in_service
        self.net.storage.at[self.gid, "soc_percent"] = self.soc_percent
        self.net.storage.at[self.gid, "p_mw"] = self.p_mw
        self.net.storage.at[self.gid, "q_mvar"] = self.q_mvar
        
    def initialize_control(self):
        # at the beginning of each time step reset applied-flag
        if self.in_service:
            if self.soc_percent <= self.socmin:
                self.p_mw = 0.1 * self.efficiency
            else:
                self.p_mw = 0
        else:
            self.p_mw = 0
        self.applied = False
    
    def is_converged(self):
        # calculate convergence criteria
        if not self.net['storage'].at[self.gid, 'in_service']:
            return True
        if self.applied == False:
            return False
        if self.p_mw == 0:
            return True
        u = self.net.res_bus.at[self.bus, "vm_pu"]
        p = 0.1 * self.efficiency
        q = self.net.storage.at[self.gid, "q_mvar"]
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

    def control_step(self):
        # apply control strategy
        u = self.net.res_bus.at[self.bus, "vm_pu"]
        p = 0.1 * self.efficiency
        if self.in_service:
            if self.soc_percent <= self.socmin: #strat débile, charge max dès qu'on peut
                self.p_mw = 0.1* self.efficiency
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
            else:
                self.p_mw = 0
        else:
            self.p_mw = 0
        self.write_to_net()
        self.applied = True
