class LiftSuccessChecker:
    def __init__(
        self,
        base_env,
        object_name,
        lift_threshold=0.05,
        required_steps=5,
    ):
        self.base_env = base_env
        self.object_name = object_name
        self.lift_threshold = lift_threshold
        self.required_steps = required_steps
        self.success_counter = 0

        self.body_id = base_env.obj_body_id[object_name]
        self.initial_z = self.get_current_z()

    def get_current_z(self):
        return float(
        self.base_env.sim.data.body_xpos[self.body_id][2]
    )
    def update(self):
        current_z = self.get_current_z()
        delta_z = current_z - self.initial_z
        lifted = delta_z >= self.lift_threshold
        if lifted:
            self.success_counter += 1
        else:
            self.success_counter = 0
        success = (
            self.success_counter >= self.required_steps
        )
        info = {
            "initial_z": self.initial_z,
            "current_z": current_z,
            "delta_z": delta_z,
            "lifted": lifted,
            "success_counter": self.success_counter,
            "success": success,
        }

        return success, info
        

        