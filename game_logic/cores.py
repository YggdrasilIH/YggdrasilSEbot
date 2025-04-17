# game_logic/cores.py

class CoreOfOrigin:
    def modify_control_duration(self, duration):
        """
        Modify control effect duration.
        For PDE's Core, reduce duration by 1 round (minimum 1 round).
        """
        return max(1, duration - 1)

# For now, we only support PDE's Core of Origin.
class PDECore(CoreOfOrigin):
    pass  # Inherits the default behavior.

# Global variable to store the active core for the battle.
active_core = None
