import random
from engine.enums import Flag, Pulse
from collections import namedtuple

from engine.logger import debug_logger as debug_log

TransitionData = namedtuple("TransitionData", "next_state, transition_animation, transition_animation_cfg")


class StateRuntime:
    def __init__(self, pet, current_state_name, config, all_configs, variables):
        self.pet = pet
        self.current_state_name = current_state_name
        self.current_state_cfg = config
        self.all_configs = all_configs
        self.variables = variables

        # getting all force transitions in a dictionary for ease of use
        self.all_forced_transitions = {}
        for state in self.all_configs:
            force_transitions_to_state = self.all_configs[state].get("force_transition")
            if not force_transitions_to_state:
                continue

            for t in force_transitions_to_state:
                self.all_forced_transitions.setdefault(state, []).append(t)

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
    

    # apps
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
    
    
    # helpers
    def _apply_on_enter(self):  # called from state machine on enter
        for cmd in self.current_state_cfg.get("variables_on_enter", []):
            self._var_or_flag_command(cmd)
        for part in self.current_state_cfg.get("particles_on_enter", []):
            self._emit_particles(part)
        for c_part in self.current_state_cfg.get("constant_particles", []):
            self._emit_particles(c_part, True)
        for audio in self.current_state_cfg.get("audio_on_enter", []):
            self._play_audio(audio)

    def _apply_on_transition(self, transition_info):
        variables_on_transition = transition_info.get("variables_on_transition", [])
        if isinstance(variables_on_transition, list):
            for variable_cmd in variables_on_transition:
                self._var_or_flag_command(variable_cmd)
        else:
            self._var_or_flag_command(variables_on_transition)
        
        particles_on_transition = transition_info.get("particles_on_transition", [])
        if isinstance(particles_on_transition, list): 
            for particle_cmd in particles_on_transition:
                self._emit_particles(particle_cmd)
        else:
            self._emit_particles(particles_on_transition)

        audio_on_transition = transition_info.get("audio_on_transition", [])
        if isinstance(audio_on_transition, list):
            for audio_cmd in audio_on_transition:
                self._play_audio(audio_cmd)
        else:
            self._play_audio(audio_on_transition)

    def apply_on_exit(self): # called from state machine on exit
        for cmd in self.current_state_cfg.get("variables_on_exit", []):
            self._var_or_flag_command(cmd)
        for part in self.current_state_cfg.get("particles_on_exit", []):
            self._emit_particles(part)
        for audio in self.current_state_cfg.get("audio_on_exit", []):
            self._play_audio(audio)

        for emitter in self.constant_emitters:
            emitter.done_emitting = True
        self.constant_emitters.clear()

    # executing commands
    def _emit_particles(self, particle_cmd, constant = False):
        if "emit" in particle_cmd:
            # print("emitting")
            name = particle_cmd["emit"]
            self.pet.particle_engine.raise_()
            emitter = self.pet.particle_engine.start_emitting(name, constant)
            if constant:
                self.constant_emitters.append(emitter)

    def _var_or_flag_command(self, cmd):
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
        if "play" in audio_cmd:
            name = audio_cmd["play"]

            volume = audio_cmd.get("volume")
            speed = audio_cmd.get("speed")

            self.pet.audio_engine.play(
                name,
                volume=volume,
                speed=speed
            )


    # transitions

    def enter_state(self, next_state):
        self.current_state_name = next_state
        self.current_state_cfg = self.all_configs[next_state]
        self._apply_on_enter()
        self.variables.reset("times_clicked_this_state")
        self.variables.reset("time_spent_in_this_state")
        self.remove_flag(Flag.ANIMATION_FINISHED)
        self.remove_flag(Flag.MOVEMENT_FINISHED)

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

    def handle_global_events(self) -> TransitionData | None:
        """
        Checks if forced transitions apply in any of the states.
        Returns a tuple(next state's name, transition_animation, transition_animation_config)
        """
        for state in self.all_forced_transitions:
            force_transitions = self.all_forced_transitions[state]

            for t in force_transitions:
                if self.current_state_name in t.get("except_states", []): continue

                conditions = t.get("when", [])
                chance = t.get("chance", 1)

                if all(self._check_condition(c) for c in conditions) and random.random() <= chance:
                    # print("Forced transition:", conditions)
                    self._apply_on_transition(t)
                    debug_log.debug(f"Forced transition from {self.current_state_name} to {state} - satisfied all conditions {conditions} and chance {chance}\nTransition animation: {t.get("transition_animation")}, config: {t.get("transition_animation_cfg")}")
                    
                    result = TransitionData(
                        next_state=state,
                        transition_animation=t.get("transition_animation"),
                        transition_animation_cfg=t.get("transition_animation_cfg", {}))
                    
                    return result
            
        return None 

    def handle_events(self) -> TransitionData | None:
        # print(f"state_runtime: handling events: Flags: ", self.flags, " Pulses: ", self.pulses)
        particle_commands = self.current_state_cfg.get("conditional_particles", [])
        for p in particle_commands:
            conditions = p["when"]
            chance = p.get("chance", 1)
            if all(self._check_condition(c) for c in conditions) and random.random() <= chance:
                self._emit_particles(p)
                debug_log.debug(f"Emitting conditional_particles {p["emit"]} - satisfied all conditions {conditions} and chance {chance}")

        audio_commands = self.current_state_cfg.get("conditional_audio", [])
        for au in audio_commands:
            conditions = au["when"]
            chance = au.get("chance", 1)

            if all(self._check_condition(c) for c in conditions) and random.random() <= chance:
                self._play_audio(au)

        # --- Checking for state transitions ---
        transitions = self.current_state_cfg.get("transitions", [])
        for t in transitions:  # handling the list of "transitions:" from configs
            conditions = t["when"]
            chance = t.get("chance", 1)

            if all(self._check_condition(c) for c in conditions) and random.random() <= chance: # if all conditions are True - we make the transition
                self._apply_on_transition(transition_info=t)
                debug_log.debug(f"Transition from {self.current_state_name} to {t["to"]} - satisfied all conditions {conditions} and chance {chance}\nTransition animation: {t.get("transition_animation")}, config: {t.get("transition_animation_cfg")}")
        
                result = TransitionData(
                    next_state=t["to"], 
                    transition_animation=t.get("transition_animation"), 
                    transition_animation_cfg=t.get("transition_animation_cfg", {}))

                return result
            
        exit_conditions = self.current_state_cfg.get("exit_when")
        if exit_conditions and all(self._check_condition(c) for c in exit_conditions):
            debug_log.debug(f"Exiting from {self.current_state_name} to {self.current_state_cfg["exit_to"]} - satisfied all exit conditions {exit_conditions}\nExit animation: {self.current_state_cfg.get("exit_animation")}, config: {self.current_state_cfg.get("exit_animation_cfg")}")
            
            result = TransitionData(
                next_state=self.current_state_cfg["exit_to"], 
                transition_animation=self.current_state_cfg.get("exit_animation"),
                transition_animation_cfg=self.current_state_cfg.get("exit_animation_cfg", {}))

            return result
        
        return None

        
        