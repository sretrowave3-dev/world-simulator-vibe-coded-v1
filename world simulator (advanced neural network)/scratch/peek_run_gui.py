import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
with open('world simulator (advanced neural network)/run_gui.py', 'r', encoding='utf-8') as f:
    text = f.read()

idx = text.find('def print_modern_help_menu(')
print(text[idx+1200:idx+2600])
