#!/usr/bin/env python3
"""
Script to fix common indentation issues in app.py
"""

def fix_indentation():
    with open('app.py', 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    fixed_lines = []
    in_function = False
    in_with_block = False
    expected_indent = 0
    
    for i, line in enumerate(lines):
        # Skip empty lines
        if line.strip() == '':
            fixed_lines.append(line)
            continue
        
        # Count current indentation
        current_indent = len(line) - len(line.lstrip())
        
        # Check for common patterns that need fixing
        stripped = line.strip()
        
        # Fix common indentation issues
        if 'def ' in stripped and not stripped.startswith('#'):
            # Function definition
            if 'def toggle_tts_engine' in stripped or 'def update_edge_voices' in stripped:
                # These should be indented as nested functions
                fixed_lines.append('        ' + stripped + '\n')
            else:
                fixed_lines.append(line)
        elif stripped.startswith('gr.') and current_indent < 8:
            # Gradio components should be properly indented
            if 'with gr.' in lines[max(0, i-5):i]:
                # Inside a with block, should be indented more
                fixed_lines.append('                ' + stripped + '\n')
            else:
                fixed_lines.append('            ' + stripped + '\n')
        elif stripped.startswith('with gr.') and current_indent < 4:
            # with blocks should be properly indented
            fixed_lines.append('            ' + stripped + '\n')
        elif stripped.startswith('return (') or stripped.startswith('gr.update('):
            # Return statements in functions should be properly indented
            fixed_lines.append('            ' + stripped + '\n')
        else:
            fixed_lines.append(line)
    
    # Write the fixed file
    with open('app_fixed.py', 'w', encoding='utf-8') as f:
        f.writelines(fixed_lines)
    
    print("Fixed indentation issues. Check app_fixed.py")

if __name__ == "__main__":
    fix_indentation()