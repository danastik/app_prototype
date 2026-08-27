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
        self.pending_transition_anim = None
        self.pending_transition_cfg = None

    def raise_flag(self, flag: Flag):
        self.state.raise_flag(flag)

        if self.in_transition and flag == Flag.ANIMATION_FINISHED:  # logic for ending transition animation
            # print("changing after animation finished")
            self.apply_pending_changes()

    def remove_flag(self, flag: Flag):
        self.state.remove_flag(flag)

    def pulse(self, pulse: Pulse):
        self.state.pulse(pulse)
        
    def update_apps(self, app_state):
        self.state.update_apps(app_state)

    def update(self, dt) -> tuple[TransitionData | None, list]:
        result: TransitionData | None
        commands: list

        result, commands = self.state.handle_global_events()
        # print("state_machine update", result)

        if not result and not self.in_transition:
            result, commands = self.state.handle_events()

        # TRANSITION LOGIC
        # if result:
        #     next_state, transition_anim, anim_cfg = result

        #     if transition_anim:
        #         self.queue_transition(next_state, transition_anim, anim_cfg) # queueing transition until transition anim is finished
        #     else:
        #         self.queue_transition(next_state, None, None)
        #         self.apply_pending_changes()    # immediately executing transition

        # print("state machine. result:", result)
        # print("state_machine next state is: ", next_state)

        self.state.clear_pulses()

        return result, commands

        
    def queue_transition(self, next_state, anim, cfg):      
        self.state.get_commands_on_exit(self.STATE_CONFIG[self.state.current_state_name])
        self.pending_state = next_state
        self.in_transition = True        

    def apply_pending_changes(self):
        if not self.pending_state:
            return
        
        # self.state.clear_pulses() #just in case any pulses arent cleared too fast

        self.state.enter_state(self.pending_state)
        # print("state_machine: pending changes applied")

        # Cleanup
        self.in_transition = False
        self.pending_state = None
        self.pending_transition_anim = None
        self.pending_transition_cfg = None