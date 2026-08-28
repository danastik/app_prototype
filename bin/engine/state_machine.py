from engine.state_runtime import StateRuntime
from engine.state_runtime import TransitionData
from engine.enums import Flag, Pulse

from engine.logger import debug_logger as debug_log

class StateMachine:
    def __init__(self, pet, CONFIG, initial, variable_manager):
        self.pet = pet
        self.STATE_CONFIG = CONFIG
        self.state = StateRuntime(pet = pet, current_state_name=initial, config=CONFIG[initial], all_configs=CONFIG, variable_manager=variable_manager)
        self.state.enter_state(initial)
        self.in_transition = False

        # for pending states
        self.pending_state = None

    def raise_flag(self, flag: Flag):
        self.state.raise_flag(flag)

        # if self.in_transition and flag == Flag.ANIMATION_FINISHED:  # logic for ending transition animation
        #     print("changing after animation finished")
        #     self.apply_pending_state()

    def remove_flag(self, flag: Flag):
        self.state.remove_flag(flag)

    def pulse(self, pulse: Pulse):
        self.state.pulse(pulse)
        
    def update_apps(self, app_state):
        self.state.update_apps(app_state)

    def update(self, dt) -> tuple[TransitionData | None, list]:
        result: TransitionData | None
        commands: list

        if self.in_transition and self.state.has_flag(Flag.ANIMATION_FINISHED):  # return pending state if we are in transition and ANIMATION_FINISHED
            next_state = self.pending_state
            cmds_on_transition = self.apply_pending_transition()
            # print("SM return", next_state)
            return TransitionData(next_state, None, None), cmds_on_transition

        result, commands = self.state.handle_global_events()
        # print("state_machine update", result)

        if not result and not self.in_transition:
            result, commands = self.state.handle_events()

        # TRANSITION LOGIC
        if result:
            next_state, transition_anim, anim_cfg = result

            cmds_on_exit = self.queue_transition(next_state) # queueing transition until transition anim is finished
            commands += cmds_on_exit

            if not transition_anim:
                cmds_on_enter = self.apply_pending_transition()
                commands += cmds_on_enter

        # print("state machine. result:", result)
        # print("state_machine next state is: ", next_state)

        self.state.clear_pulses()
        self.remove_flag(Flag.ANIMATION_FINISHED)

        # for cmd in commands:
        #     print("cmd", type(cmd))
        return result, commands

        
    def queue_transition(self, next_state) -> list:      
        commands = self.state.get_commands_on_exit(self.STATE_CONFIG[self.state.current_state_name])
        self.pending_state = next_state
        self.in_transition = True
        # print("state_machine: queue transition")
        self.remove_flag(Flag.ANIMATION_FINISHED)

        return commands

    def apply_pending_transition(self) -> list:
        if not self.pending_state:
            return []

        commands = self.state.enter_state(self.pending_state)
        # print("state_machine: pending changes applied")

        # Cleanup
        self.in_transition = False
        self.pending_state = None
        self.state.clear_pulses()

        return commands