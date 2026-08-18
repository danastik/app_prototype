import random
from engine.enums import Flag, Pulse

class StateRuntime:
    def __init__(self, pet, current_state_name, config, all_configs, variables):
        self.pet = pet
        self.current_state_name = current_state_name
        self.config = config
        self.all_configs = all_configs
        self.variables = variables

        # getting all force transitions in a dictionary for ease of use
        self.all_forced_transitions = {}

        for state in self.all_configs:
            try:
                force_transition = self.all_configs[state].get("force_transition")
                if not force_transition: continue
            except Exception:
                continue

            for t in force_transition:
                conditions = t.get("when")
                exception_states = t.get("except_states")
                to = state
                chance = t.get("chance", 1)
                trans_anim = t.get("transition_animationation")
                trans_anim_cfg = t.get("transition_animationation_cfg")

                # print(conditions)
                # print(to)
                # print(chance)

                self.all_forced_transitions[to] = {"conditions": conditions, "except_states": exception_states, "chance": chance, "transition_animationation": trans_anim, "transition_animationation_cfg": trans_anim_cfg}

        # print(self.all_forced_transitions)

        self.flags = set()
        self.pulses = set()

        self.visible_apps = set()
        self.active_apps = set()
        self.maximised_apps = set()
        self.fullscreen_apps = set()
        self.focused_app_title = ""
        self.focused_app = set()

        #particle stuff
        self.constant_emitters = []

    # flags
    def raise_flag(self, flag: Flag):
        if flag == Flag.DRAGGING and not flag in self.flags:  # special check for sending a pulse dragging started when dragging flag is raised
            self.pulse(Pulse.DRAGGING_STARTED)

        self.flags.add(flag)

    def remove_flag(self, flag: Flag):
        self.flags.discard(flag)

    def has_flag(self, flag: Flag):
        return flag in self.flags

    # pulses
    def pulse(self, pulse: Pulse):
        self.pulses.add(pulse)

    def has_pulse(self, pulse: Pulse):
        return pulse in self.pulses

    def clear_pulses(self):
        self.pulses.clear()
    
    def update_apps(self, app_state):
        # print("apps")
        active, visible, maximised, fullscreen, focused_title, focused = app_state
        # print(active)
        # print("runtime update apps visible:", visible)
        # print(maximised)
        # print(fullscreen)
        # print(focused_title)
        # print(focused)
        self.active_apps = active
        self.visible_apps = visible
        self.maximised_apps = maximised
        self.fullscreen_apps = fullscreen
        self.focused_app_title = focused_title
        self.focused_app = focused
    
    def _apply_on_enter(self):  # called from state machine on enter
        for cmd in self.config.get("variables_on_enter", []):
            self._execute_command(cmd)
        for part in self.config.get("particles_on_enter", []):
            self._emit_particles(part)
        for c_part in self.config.get("constant_particles", []):
            self._emit_particles(c_part, True)

    def _apply_on_transition(self, transition_info):
        
        variables_on_transition = transition_info.get("variables_on_transition", [])
        if isinstance(variables_on_transition, list):
            for variable_cmd in variables_on_transition:
                self._execute_command(variable_cmd)
        else:
            self._execute_command(variables_on_transition)
        
        particles_on_transition = transition_info.get("particles_on_transition", [])
        if isinstance(particles_on_transition, list): 
            for particle_cmd in particles_on_transition:
                self._emit_particles(particle_cmd)
        else:
            self._emit_particles(particles_on_transition)

        # сюда скопировать вот то что сверху только переделать под звук


    def _apply_on_exit(self): # called from state machine on exit
        for cmd in self.config.get("variables_on_exit", []):
            self._execute_command(cmd)
        for part in self.config.get("particles_on_exit", []):
            self._emit_particles(part)

        for emitter in self.constant_emitters:
            emitter.done_emitting = True
        self.constant_emitters.clear()

        # сюда добавить чтоб он тоже для всех "audio_on_exit" играл аудио


    def _emit_particles(self, particle_cmd, constant = False):
        if "emit" in particle_cmd:
            # print("emitting")
            name = particle_cmd["emit"]
            self.pet.particle_engine.raise_()
            emitter = self.pet.particle_engine.start_emitting(name, constant)
            if constant:
                self.constant_emitters.append(emitter)

    def _execute_command(self, cmd):
        if "var" in cmd:
            name = cmd["var"]
            op = cmd["op"]
            value = cmd["value"]

            if op == "+=":
                self.variables.add(name, value)
            elif op == "-=":
                self.variables.add(name, -value)
            elif op == "=":
                self.variables.set(name, value)

        elif "set_flag" in cmd:
            self.flags.add(cmd["set_flag"])

        elif "clear_flag" in cmd:
            self.flags.discard(cmd["clear_flag"])

    def _play_audio(self, audio_cmd):
        pass
        # а тут надо обработать команду, можешь посмотреть как это в партиклах и в _execute_command делается
        # if "play" in audio_cmd:
        #     # print("Playing audio")

    def _check_condition(self, cond):
        if "flag" in cond:
            return Flag.__members__.get(cond["flag"]) in self.flags

        if "pulse" in cond:
            return Pulse.__members__.get(cond["pulse"]) in self.pulses

        if "var" in cond:
            val = self.variables.get(cond["var"])
            match cond["op"]:
                case "<": return val < cond["value"]
                case ">": return val > cond["value"]
                case "==": return val == cond["value"]
                case "<=": return val <= cond["value"]
                case ">=": return val >= cond["value"]

        if "app" in cond:
            # print("checking condition:", cond, "its", cond["app"] in self.visible_apps)
            # print("visible", self.visible_apps)
            match cond["is"]:
                case "visible": return cond["app"] in self.visible_apps
                case "maximised": return cond["app"] in self.maximised_apps
                case "fullscreen": return cond["app"] in self.fullscreen_apps
                case "active": return cond["app"] in self.active_apps
                case "focused": return cond["app"] in self.focused_app
                case "title": return cond["app"] in self.focused_app_title


        return Flag.__members__.get(cond) in self.flags or Pulse.__members__.get(cond) in self.pulses   # THIS makes it so instead of Flag.FLAG_NAME you can just FLAG_NAME

    def handle_global_events(self) -> tuple[str, str, dict] | None:
        """
        Checks if forced transitions apply in any of the states.
        Returns a tuple(next state's name, transition_animation, transition_animation_config)
        """
        for state in self.all_forced_transitions:
            force_trans = self.all_forced_transitions[state]

            if self.current_state_name in force_trans.get("except_states"): break

            conditions = force_trans.get("conditions")
            chance = force_trans.get("chance", 1)

            if all(self._check_condition(c) for c in conditions) and random.random() <= chance:
                # print("Forced transition:", conditions)
                return (
                    state,  # return the destination state
                    force_trans.get("transition_animation", None),
                    force_trans.get("transition_animation_cfg", {})
                )
            
        return None 


    def handle_events(self) -> tuple[str, str, dict] | None:
        # print(f"state_runtime: handling events: Flags: ", self.flags, " Pulses: ", self.pulses)
        particle_commands = self.config.get("conditional_particles", [])

        for p in particle_commands:
            conditions = p["when"]
            chance = p.get("chance", 1)
            if all(self._check_condition(c) for c in conditions) and random.random() <= chance:
                self._emit_particles(p)

        # чето типа такого тебе надо
        # это чтоб в любом месте можно было звук проигрывать
        # audio_commands = self.config.get("conditional_audio", [])

        # for au in audio_commands:
        #     conditions = au["when"]
        #     chance = au.get("chance", 1)
        #     if all(self._check_condition(c) for c in conditions) and random.random() <= chance:
        #         self._play_audio(au)

        # --- Checking for state transitions ---
        transitions = self.config.get("transitions", [])

        for t in transitions:  # handling all "transitions:" from configs
            conditions = t["when"]
            chance = t.get("chance", 1)

            if all(self._check_condition(c) for c in conditions) and random.random() <= chance: # if all conditions are True - we make the transition
                self._apply_on_transition(transition_info=t)
                return (
                    t["to"],  # next state
                    t.get("transition_animation", None),
                    t.get("transition_animation_cfg", {})
                )
            
        exit_conditions = self.config.get("exit_when")
        if exit_conditions and all(self._check_condition(c) for c in exit_conditions):
            # print("exiting state")
            return(self.config["exit_to"], self.config.get("exit_animation"), self.config.get("exit_animation_cfg"))

        return None

        
        