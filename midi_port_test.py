import mido

# Print available MIDI input ports
print("Available MIDI Input Ports:")
for port in mido.get_input_names():
    print(port)

# Print available MIDI output ports
print("\nAvailable MIDI Output Ports:")
for port in mido.get_output_names():
    print(port)
