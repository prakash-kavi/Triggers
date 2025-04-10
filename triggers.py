import os
import random
import datetime
import pandas as pd
from psychopy import core, visual, sound, event, gui, parallel, prefs

# Set audio backend to PsychToolbox for precise timing
prefs.hardware['audioLib'] = ['ptb']

# Constants
SOA = 2.0  # Stimulus Onset Asynchrony in seconds
TRIGGER_DURATION = 0.01  # Duration to hold trigger high
PORT_ADDRESS = 0x0378  # Parallel port address
NUM_AUTO_BLOCKS = 20  # Number of automatic blocks
NUM_MANUAL_SETS = 2  # Number of manual sets
BLOCKS_PER_MANUAL_SET = 5  # Number of blocks per manual set
INITIAL_DELAY = 60  # Initial delay in seconds (1 minute)
INTER_BLOCK_DELAY = 30  # Delay between blocks in seconds

# Paths
STIM_PATH = 'stim'
RES_PATH = 'Res'
if not os.path.exists(RES_PATH):
    os.makedirs(RES_PATH)

# Get subject code via dialog box
dlg = gui.Dlg(title="Subject Information")
dlg.addField("Subject Code:")
subject_code = dlg.show()
if dlg.OK:
    subject_code = subject_code[0]
else:
    core.quit()

# Initialize parallel port
port = parallel.ParallelPort(address=PORT_ADDRESS)

# Load audio stimuli
std_sound = sound.Sound(os.path.join(STIM_PATH, 'std.wav'))
dev_sound = sound.Sound(os.path.join(STIM_PATH, 'dev.wav'))
std_sound.setVolume(0.2)
dev_sound.setVolume(0.2)

# Stimulus types and trigger values
stim_types = [std_sound, dev_sound]
trigger_values = [1, 2]  # 1 for standard, 2 for deviant

# Open a visual window for messages
win = visual.Window(fullscr=False, color='black')

# Function to generate a sequence of 10 stimuli for one block
def generate_sequence():
    sequence = [0] * 10  # 0 represents standard, create a list of 10
    # Choose 2 non-consecutive positions from indices 4 to 9 for deviants
    possible_pairs = [(i, j) for i in range(4, 10) for j in range(i + 2, 10)]
    deviant_positions = random.choice(possible_pairs)
    sequence[deviant_positions[0]] = 1  # 1 represents deviant
    sequence[deviant_positions[1]] = 1
    return sequence

# Function to present one block of 10 stimuli
def present_block(block_num):
    sequence = generate_sequence()
    print(f"Block {block_num}: Sequence generated with {len(sequence)} stimuli: {sequence}")
    block_clock = core.Clock()
    log_data = []
    for i, stim_type in enumerate(sequence):
        print(f"Playing stimulus {i+1}/10: {'standard' if stim_type == 0 else 'deviant'}")
        onset = i * SOA
        while block_clock.getTime() < onset:
            core.wait(0.001)
        stim_types[stim_type].play()
        port.setData(trigger_values[stim_type])
        core.wait(TRIGGER_DURATION)
        port.setData(0)
        stim_name = 'std.wav' if stim_type == 0 else 'dev.wav'
        log_data.append([subject_code, stim_name])
        # Check for escape key during block
        if 'escape' in event.getKeys():
            return log_data, True  # True indicates early exit
    return log_data, False

# Function to show dialog box for manual sets
def show_manual_set_dialog(set_num):
    dlg = gui.Dlg(title=f"Start Manual Set {set_num}")
    dlg.addText(f"Click OK to start manual set {set_num}")
    dlg.show()
    return dlg.OK

# Main experiment flow
log_data = []

# Initial delay
print("Starting initial delay...")
core.wait(INITIAL_DELAY)

# Automatic blocks
for block in range(NUM_AUTO_BLOCKS):
    if 'escape' in event.getKeys():  # Check for escape before block
        print("Escape key pressed, stopping experiment.")
        break
    print(f"Presenting automatic block {block + 1} of {NUM_AUTO_BLOCKS}")
    block_log, early_exit = present_block(block + 1)
    log_data.extend(block_log)
    if early_exit:
        print("Escape key pressed during block, stopping experiment.")
        break
    if block < NUM_AUTO_BLOCKS - 1:
        core.wait(INTER_BLOCK_DELAY)

# Manual sets (only proceed if not already stopped by escape)
if not early_exit:
    for set_num in range(1, NUM_MANUAL_SETS + 1):
        if 'escape' in event.getKeys():  # Check for escape before manual set
            print("Escape key pressed, stopping experiment.")
            break
        if not show_manual_set_dialog(set_num):  # Show dialog and wait for OK
            print("Manual set canceled by user.")
            break
        for block in range(BLOCKS_PER_MANUAL_SET):
            if 'escape' in event.getKeys():  # Check for escape before block
                print("Escape key pressed, stopping experiment.")
                break
            print(f"Presenting manual set {set_num}, block {block + 1} of {BLOCKS_PER_MANUAL_SET}")
            block_log, early_exit = present_block(block + 1)
            log_data.extend(block_log)
            if early_exit:
                print("Escape key pressed during block, stopping experiment.")
                break
            if block < BLOCKS_PER_MANUAL_SET - 1:
                core.wait(INTER_BLOCK_DELAY)
        if early_exit:
            break

# Save log data
timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
res_filename = os.path.join(RES_PATH, f"{timestamp}_{subject_code}.csv")
df = pd.DataFrame(log_data, columns=['subject_code', 'stim_name'])
df.to_csv(res_filename, index=False)
print(f"Data saved to {res_filename}")

# Cleanup
win.close()
core.quit()