import random
from engine.enums import Flag, Pulse
from engine.variable_manager import VariableManager
from collections import namedtuple

from engine.state_commands import *
from engine.logger import debug_logger as debug_log

TransitionData = namedtuple("TransitionData", "next_state, transition_animation, transition_animation_cfg")


class StateRuntime:
    def __init__(self, pet, current_state_name, config, all_configs, variable_manager: VariableManager):
        self.pet = pet
        self.current_state_name = current_state_name
        self.current_state_cfg = config
        self.all_configs = all_configs
        self.variable_manager = variable_manager

        # getting all force transitions in a dictionary for ease of use
        self.all_forced_transitions = {}
        for state in self.all_configs:
            force_transitions_to_state = self.all_configs[state].get("force_transition")
            if not force_transitions_to_state:
                continue

            for t in force_transitions_to_state:
                self.all_forced_transitions.setdefault(state, []).append(t)

        self.flags = set(Flag)
        self.pulses = set(Pulse)

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
    
    
    # big helpers
    def _get_commands_on_enter(self, state_cfg) -> list:  # called from state machine on enter
        commands = []

        var_cmds = self._get_variable_cmds(state_cfg, "variables_on_enter")
        commands += var_cmds

        bool_cmds = self._get_bool_cmds(state_cfg, "bools_on_enter")
        commands += bool_cmds

        particle_cmds = self._get_particle_cmds(state_cfg, "particles_on_enter")
        commands += particle_cmds

        c_particle_cmds = self._get_particle_cmds(state_cfg, "constant_particles")
        for c_part in c_particle_cmds:
            c_part.constant=True
        commands += c_particle_cmds
        
        audio_cmds = self._get_audio_cmds(state_cfg, "audio_on_enter")
        commands += audio_cmds

        # print("_get_commands_on_enter", commands)

        return commands

    def _get_commands_on_transition(self, transition_cfg) -> list:
        commands = []

        var_cmds = self._get_variable_cmds(transition_cfg, "variables_on_transition")
        commands += var_cmds

        bool_cmds = self._get_bool_cmds(transition_cfg, "bools_on_transition")
        commands += bool_cmds

        particle_cmds = self._get_particle_cmds(transition_cfg, "particles_on_transition")
        commands += particle_cmds
        
        audio_cmds = self._get_audio_cmds(transition_cfg, "audio_on_transition")
        commands += audio_cmds

        return commands
    
    def _get_conditional_commands(self, config) -> list:
        commands = []

        variable_commands = config.get("conditional_variables", [])
        for var in variable_commands:
            if self._check_all_conditions(var):
                cmd = self._var_cmd(var)
                if cmd:commands.append(cmd)

        bool_commands = config.get("conditional_bools", [])
        for bool in bool_commands:
            if self._check_all_conditions(bool):
                cmd = self._bool_cmd(bool)
                if cmd:commands.append(cmd)

        particle_commands = config.get("conditional_particles", [])
        for p in particle_commands:
            if self._check_all_conditions(p):
                cmd = self._particle_cmd(p)
                if cmd:commands.append(cmd)
                    # debug_log.debug(f"Emitting conditional_particles {p["emit"]} - satisfied all conditions {conditions} and chance {chance}")

        audio_commands = config.get("conditional_audio", [])
        for au in audio_commands:
            if self._check_all_conditions(au):
                cmd = self._audio_cmd(au)
                if cmd:commands.append(cmd)

        return commands

    def get_commands_on_exit(self, state_cfg): # called from state machine on exit
        commands = []

        var_cmds = self._get_variable_cmds(state_cfg, "variables_on_exit")
        commands += var_cmds

        bool_cmds = self._get_bool_cmds(state_cfg, "bools_on_exit")
        commands += bool_cmds

        particle_cmds = self._get_particle_cmds(state_cfg, "particles_on_exit")
        commands += particle_cmds
        
        audio_cmds = self._get_audio_cmds(state_cfg, "audio_on_exit")
        commands += audio_cmds

        # for emitter in self.constant_emitters:
        #     emitter.done_emitting = True
        # self.constant_emitters.clear()

        return commands



    # helpers per type
    def _get_variable_cmds(self, cfg: dict, runtime_type: str) -> list[VariableCommand]:
        variables = cfg.get(runtime_type)
        if not variables: return []

        cmds = []
        if isinstance(variables, list):
            for variable_cmd in variables:
                cmd = self._var_cmd(variable_cmd)
                if cmd: cmds.append(cmd)
        else:
            cmd = self._var_cmd(variables)
            if cmd: cmds.append(cmd)

        return(cmds)
    
    def _get_bool_cmds(self, cfg: dict, runtime_type: str) -> list[BoolCommand]:
        bools = cfg.get(runtime_type)
        if not bools: return []

        cmds = []
        if isinstance(bools, list):
            for bool_cmd in bools:
                cmd = self._bool_cmd(bool_cmd)
                if cmd: cmds.append(cmd)
        else:
            cmd = self._bool_cmd(bools)
            if cmd: cmds.append(cmd)

        return(cmds)
    
    def _get_particle_cmds(self, cfg: dict, runtime_type: str) -> list[ParticleCommand]:
        particles = cfg.get(runtime_type)
        if not particles: return []

        cmds = []
        if isinstance(particles, list):
            for part_cmd in particles:
                cmd = self._particle_cmd(part_cmd)
                if cmd: cmds.append(cmd)
        else:
            cmd = self._particle_cmd(particles)
            if cmd: cmds.append(cmd)

        return(cmds)
    
    def _get_audio_cmds(self, cfg: dict, runtime_type: str) -> list[AudioCommand]:
        audio = cfg.get(runtime_type)
        if not audio: return []

        cmds = []
        if isinstance(audio, list):
            for au_cmd in audio:
                cmd = self._audio_cmd(au_cmd)
                if cmd: cmds.append(cmd)
        else:
            cmd = self._audio_cmd(audio)
            if cmd: cmds.append(cmd)

        return(cmds)


    # lil command helpers
    def _var_cmd(self, cmd) -> VariableCommand | None:
        if "var" in cmd:
            name = cmd["var"]
            op = cmd["op"]
            value = cmd["value"]
            print("var", name, op, value)
            return VariableCommand(name, op, value)

    def _bool_cmd(self, cmd) -> BoolCommand | None:
        if "set_bool" in cmd:
            name = cmd["set_bool"]
            value = cmd["value"]
            return BoolCommand(name, value)

    def _particle_cmd(self, particle_cmd, constant = False) -> ParticleCommand | None:
        if "emit" in particle_cmd:
            name = particle_cmd["emit"]
            # self.pet.particle_engine.raise_()
            # emitter = self.pet.particle_engine.start_emitting(name, constant)
            # if constant:
                # self.constant_emitters.append(emitter)
            
            print("particle cmd", name, constant)
            return ParticleCommand(name, constant)
        
    def _audio_cmd(self, audio_cmd) -> AudioCommand | None:
        if "play" in audio_cmd:
            name = audio_cmd["play"]

            volume = audio_cmd.get("volume")
            speed = audio_cmd.get("speed")

            # self.pet.audio_engine.play(
            #     name,
            #     volume=volume,
            #     speed=speed
            # )
            return AudioCommand(name, volume, speed)


    # transitions
    def _check_all_conditions(self, cfg):
        conditions = cfg["when"]
        chance = cfg.get("chance", 1)

        return all(self._check_condition(c) for c in conditions) and random.random() <= chance

    def _check_condition(self, cond) -> bool:
        if "flag" in cond:
            return Flag.__members__.get(cond["flag"]) in self.flags

        if "pulse" in cond:
            return Pulse.__members__.get(cond["pulse"]) in self.pulses

        if "var" in cond:
            val = self.variable_manager.get_var(cond["var"])
            match cond["op"]:
                case "<": return val < cond["value"]
                case ">": return val > cond["value"]
                case "==": return val == cond["value"]
                case "<=": return val <= cond["value"]
                case ">=": return val >= cond["value"]

        if "bool" in cond:
            return self.variable_manager.get_bool(cond["bool"])

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

    def enter_state(self, next_state) -> list:
        self.current_state_name = next_state
        self.current_state_cfg = self.all_configs[next_state]
        self.variable_manager.reset_var("times_clicked_this_state")
        self.variable_manager.reset_var("time_spent_in_this_state")
        self.remove_flag(Flag.ANIMATION_FINISHED)
        self.remove_flag(Flag.MOVEMENT_FINISHED)
        return self._get_commands_on_enter(self.current_state_cfg)

    def handle_global_events(self) -> tuple[TransitionData | None, list]:
        """
        Checks if forced transitions apply in any of the states.
        Returns a tuple(next state's name, transition_animation, transition_animation_config)
        """
        commands = []

        for state in self.all_forced_transitions:
            force_transitions = self.all_forced_transitions[state]

            for t in force_transitions:
                if self.current_state_name in t.get("except_states", []): continue

                conditions = t.get("when", [])
                chance = t.get("chance", 1)

                if all(self._check_condition(c) for c in conditions) and random.random() <= chance:
                    debug_log.debug(f"Forced transition from {self.current_state_name} to {state} - satisfied all conditions {conditions} and chance {chance}\nTransition animation: {t.get("transition_animation")}, config: {t.get("transition_animation_cfg")}")
                    # print("Forced transition:", conditions)

                    commands = self._get_commands_on_transition(t)
                    
                    trans_data = TransitionData(
                        next_state=state,
                        transition_animation=t.get("transition_animation"),
                        transition_animation_cfg=t.get("transition_animation_cfg", {}))
                    
                    return trans_data, commands
            
        return None, []

    def handle_events(self) -> tuple[TransitionData | None, list]:
        # print(f"state_runtime: handling events: Flags: ", self.flags, " Pulses: ", self.pulses)
        commands = []

        cond_commands = self._get_conditional_commands(self.current_state_cfg)
        commands += cond_commands

        # --- Checking for state transitions ---
        transitions = self.current_state_cfg.get("transitions", [])
        for t in transitions:  # handling the list of "transitions:" from configs
            if self._check_all_conditions(t):
                debug_log.debug(f"Transition from {self.current_state_name} to {t["to"]} - satisfied all conditions {t.get("conditions")} and chance {t.get("chance")}\nTransition animation: {t.get("transition_animation")}, config: {t.get("transition_animation_cfg")}")
                
                trans_data = TransitionData(
                    next_state=t["to"], 
                    transition_animation=t.get("transition_animation"), 
                    transition_animation_cfg=t.get("transition_animation_cfg", {}))
                
                trans_commands = self._get_commands_on_transition(transition_cfg=t)
                commands += trans_commands

                return trans_data, commands
            
        exit_conditions = self.current_state_cfg.get("exit_when")
        if exit_conditions and all(self._check_condition(c) for c in exit_conditions):
            debug_log.debug(f"Exiting from {self.current_state_name} to {self.current_state_cfg["exit_to"]} - satisfied all exit conditions {exit_conditions}\nExit animation: {self.current_state_cfg.get("exit_animation")}, config: {self.current_state_cfg.get("exit_animation_cfg")}")
            
            trans_data = TransitionData(
                next_state=self.current_state_cfg["exit_to"], 
                transition_animation=self.current_state_cfg.get("exit_animation"),
                transition_animation_cfg=self.current_state_cfg.get("exit_animation_cfg", {}))
            
            exit_commands = self.get_commands_on_exit(self.current_state_cfg)
            commands += exit_commands

            return trans_data, commands
        
        return None, []

        
        