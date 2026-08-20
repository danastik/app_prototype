from engine.logger import debug_logger as debug_log

class VariableManager:
    def __init__(self, variables):
        self.values = {}
        self.rates = {}

        config = variables

        self.values["times_clicked_this_state"] = 0

        self.values["time_spent_in_this_state"] = 0
        self.rates["time_spent_in_this_state"] = 1

        # loading values and rates from data.variables
        for name, cfg in config.items():
            self.values[name] = float(cfg.get("value", 0.0))
            self.rates[name] = float(cfg.get("rate", 0.0))

    def update(self, dt):
        for name, rate in self.rates.items():
            self.values[name] += rate * dt

    def get(self, name):
        return self.values.get(name, 0.0)

    def set(self, name, value):
        debug_log.debug(f"[Variables] Setting {name} = {value} (previous value: {self.values[name]})")
        self.values[name] = float(value)

    def reset(self, name):
        self.values[name] = 0

    def add(self, name, delta):
        debug_log.debug(f"[Variables] Adding {name} += {delta} (previous value: {self.values[name]})")
        self.values[name] += delta