from engine.logger import debug_logger as debug_log

class VariableManager:
    """
    Docstring for VariableManager
    """
    def __init__(self, variables):
        self.values: dict[str, float] = {}
        self.rates: dict[str, float] = {}

        self.bools: dict[str, bool] = {}

        config = variables

        self.values["times_clicked_this_state"] = 0

        self.values["time_spent_in_this_state"] = 0
        self.rates["time_spent_in_this_state"] = 1

        # getting values and rates from data.variables
        for name, cfg in config.items():
            self.values[name] = float(cfg.get("value", 0.0))
            self.rates[name] = float(cfg.get("rate", 0.0))

    def update(self, dt):
        for name, rate in self.rates.items():
            self.values[name] += rate * dt


    # variables
    def get_var(self, name) -> float:
        return self.values.get(name, 0.0)

    def set_var(self, name, value: float):
        debug_log.debug(f"[Variables] Setting {name} = {value} (previous value: {self.values.get(name)})")
        self.values[name] = float(value)

    def reset_var(self, name):
        self.values[name] = 0

    def add_var(self, name, delta: float):
        debug_log.debug(f"[Variables] Adding {name} += {delta} (previous value: {self.values.get(name)})")
        self.values[name] += delta


    def get_bool(self, flag) -> bool:
        return self.bools.get(flag, False)

    def set_bool(self, name, value):
        debug_log.debug(f"[Variables] Raising flag {name} (previous value: {self.bools.get(name)}")
        self.bools[name] = value