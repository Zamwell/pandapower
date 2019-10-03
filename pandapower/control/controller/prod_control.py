# -*- coding: utf-8 -*-
"""
Created on Tue Sep 24 14:19:44 2019

@author: Utilisateur

Fichier pour créer controleur d'EV
"""

from pandapower.control.basic_controller import Controller

class ProdController(Controller):
    """
        Example class of a Storage-Controller. Models an abstract energy storage.
    """

    def __init__(self, net, gid, in_service = True, level = 0, order = 0, recycle = False):
        
        super().__init__(net, in_service=in_service, level=level, order=order, recycle=recycle)
        self.update_initialized(locals())
        
        # read storage attributes from net
        self.gid = gid
        self.bus = net.sgen.at[gid, "bus"]
        self.p_mw = net.sgen.at[gid, "p_mw"]
        self.q_mvar = net.sgen.at[gid, "q_mvar"]
        self.sn_mva = net.sgen.at[gid, "sn_mva"]
        self.name = net.sgen.at[gid, "name"]
        self.in_service = net.sgen.at[gid, "in_service"]


    def time_step(self, time):
        """
        Note: This method is ONLY being called during time-series simulation!

        It is the first call in each time step, thus suited for things like
        reading profiles or prepare the controller for the next control step.
        """
        pass

    def write_to_net(self):
        """
        This method will write any values the controller is in charge of to the
        data structure. It will be called at the beginning of each simulated
        loadflow, in order to ensure consistency between controller and
        data structure.

        You will probably want to write the final state of the controller to the
        data structure at the end of the control_step using this method.
        """
        pass

    def initialize_control(self):
        """
        Some controller require extended initialization in respect to the
        current state of the net (or their view of it). This method is being
        called after an initial loadflow but BEFORE any control strategies are
        being applied.

        This method may be interesting if you are aiming for a global
        controller or if it has to be aware of its initial state.
        """
        pass

    def is_converged(self):
        """
        This method calculated whether or not the controller converged. This is
        where any target values are being calculated and compared to the actual
        measurements. Returns convergence of the controller.
        """
        return True

    def control_step(self):
        """
        If the is_converged method returns false, the control_step will be
        called. In other words: if the controller did not converge yet, this
        method should implement actions that promote convergence e.g. adapting
        actuating variables and writing them back to the data structure.

        Note: You might want to store the mismatch calculated in is_converged so
        you don't have to do it again. Also, you might want to write the
        reaction back to the data structure (use write_to_net).
        """
        pass

    def finalize_step(self):
        """
        Note: This method is ONLY being called during time-series simulation!

        After each time step, this method is being called to clean things up or
        similar. The OutputWriter is a class specifically designed to store
        results of the loadflow. If the ControlHandler.output_writer got an
        instance of this class, it will be called before the finalize step.
        """
        pass

