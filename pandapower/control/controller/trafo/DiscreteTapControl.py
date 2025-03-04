__author__ = 'lthurner'

from pandapower.control.controller.trafo_control import TrafoController

class DiscreteTapControl(TrafoController):
    """
    Trafo Controller with local tap changer voltage control.

    INPUT:
        **net** (attrdict) - Pandapower struct

        **tid** (int) - ID of the trafo that is controlled

        **u_lower** (float) - Lower voltage limit in pu

        **u_upper** (float) - Upper voltage limit in pu

    OPTIONAL:

        **side** (string, "lv") - Side of the transformer where the voltage is controlled (hv or lv)

        **trafotype** (float, "2W") - Trafo type ("2W" or "3W")

        **tol** (float, 0.001) - Voltage tolerance band at bus in Percent (default: 1% = 0.01pu)

        **in_service** (bool, True) - Indicates if the controller is currently in_service

        **drop_same_existing_ctrl** (bool, False) - Indicates if already existing controllers of the
            same type and with the same matching parameters (e.g. at same element) should be dropped
    """

    def __init__(self, net, tid, u_lower, u_upper, side="lv", trafotype="2W",
                 tol=1e-3, in_service=True, order=0, drop_same_existing_ctrl=False,
                 **kwargs):
        super(DiscreteTapControl, self).__init__(
            net, tid, side, tol=tol, in_service=in_service, order=order, trafotype=trafotype,
            drop_same_existing_ctrl=drop_same_existing_ctrl,
            matching_params={"tid": tid, 'trafotype': trafotype}, **kwargs)
        self.update_initialized(locals())

        self.matching_params = {"tid": tid, 'trafotype': trafotype}
        self.u_lower = u_lower
        self.u_upper = u_upper

        self.tap_pos = self.net[self.trafotable].at[tid, "tap_pos"]

    def control_step(self):
        u = self.net.res_bus.at[self.controlled_bus, "vm_pu"]
        self.tap_pos = self.net[self.trafotable].at[self.tid, "tap_pos"]

        if self.tap_side_coeff * self.tap_sign == 1:
            if u < self.u_lower and self.tap_pos > self.tap_min:
                self.tap_pos -= 1
            elif u > self.u_upper and self.tap_pos < self.tap_max:
                self.tap_pos += 1
        elif self.tap_side_coeff * self.tap_sign == -1:
            if u < self.u_lower and self.tap_pos < self.tap_max:
                self.tap_pos += 1
            elif u > self.u_upper and self.tap_pos > self.tap_min:
                self.tap_pos -= 1

        # WRITE TO NET
        self.net[self.trafotable].at[self.tid, "tap_pos"] = self.tap_pos

    def is_converged(self):
        if not self.tid in self.net[self.trafotable].index or \
           not self.net[self.trafotable].at[self.tid, 'in_service']:
            return True
        u = self.net.res_bus.at[self.controlled_bus, "vm_pu"]
        self.tap_pos = self.net[self.trafotable].at[self.tid, "tap_pos"]

        # render this controller converged if he cant reach the desired point
        if self.tap_side_coeff * self.tap_sign == 1:
            if u < self.u_lower and self.tap_pos == self.tap_min:
                return True
            elif u > self.u_upper and self.tap_pos == self.tap_max:
                return True
        elif self.tap_side_coeff * self.tap_sign == -1:
            if u < self.u_lower and self.tap_pos == self.tap_max:
                return True
            elif u > self.u_upper and self.tap_pos == self.tap_min:
                return True
        return self.u_lower < u < self.u_upper

