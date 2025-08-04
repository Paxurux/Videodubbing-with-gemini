#!/usr/bin/env python3
"""
Comprehensive script to fix all indentation issues in app.py
"""

import re

def fix_all_indentation():
    with open('app.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    lines = content.split('\n')
    fixed_lines = []
    
    # Track indentation context
    indent_stack = [0]  # Stack to track indentation levels
    in_multiline_string = False
    string_delimiter = None
    
    for i, line in enumerate(lines):
        original_line = line
        stripped = line.strip()
        
        # Skip empty lines
        if not stripped:
            fixed_lines.append('')
            continue
        
        # Handle multiline strings
        if '"""' in stripped or "'''" in stripped:
            if not in_multiline_string:
                in_multiline_string = True
                string_delimiter = '"""' if '"""' in stripped else "'''"
            elif string_delimiter in stripped:
                in_multiline_string = False
                string_delimiter = None
        
        if in_multiline_string:
            fixed_lines.append(original_line)
            continue
        
        # Skip comments that are not indented code
        if stripped.startswith('#') and not any(keyword in stripped.lower() for keyword in ['import', 'def', 'class', 'if', 'for', 'while', 'with', 'try']):
            # Keep comment at current indentation level
            current_indent = indent_stack[-1]
            fixed_lines.append(' ' * current_indent + stripped)
            continue
        
        # Determine correct indentation based on context
        current_indent = 0
        
        # Check for dedenting keywords
        if any(stripped.startswith(keyword) for keyword in ['except', 'elif', 'else', 'finally']):
            if len(indent_stack) > 1:
                indent_stack.pop()
            current_indent = indent_stack[-1]
        
        # Check for blocks that increase indentation
        elif any(keyword in stripped for keyword in ['def ', 'class ', 'if ', 'elif ', 'else:', 'for ', 'while ', 'with ', 'try:', 'except', 'finally:']):
            if stripped.endswith(':'):
                current_indent = indent_stack[-1]
                indent_stack.append(current_indent + 4)
            else:
                current_indent = indent_stack[-1]
        
        # Special handling for Gradio components
        elif stripped.startswith('gr.') or 'gr.' in stripped:
            # Gradio components should be indented based on context
            if any('with gr.' in lines[max(0, j)] for j in range(max(0, i-5), i)):
                current_indent = indent_stack[-1]
            else:
                current_indent = indent_stack[-1]
        
        # Handle return statements and other regular statements
        else:
            current_indent = indent_stack[-1]
        
        # Check for closing blocks
        if stripped in [')', '}', ']'] or (stripped.startswith(')') and len(stripped) == 1):
            if len(indent_stack) > 1:
                indent_stack.pop()
            current_indent = indent_stack[-1]
        
        # Apply the indentation
        fixed_lines.append(' ' * current_indent + stripped)
    
    # Write the fixed content
    fixed_content = '\n'.join(fixed_lines)
    
    with open('app_indentation_fixed.py', 'w', encoding='utf-8') as f:
        f.write(fixed_content)
    
    print("Fixed all indentation issues. Check app_indentation_fixed.py")

if __name__ == "__main__":
    fix_all_indentation()