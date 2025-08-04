# Pinokio Dubbing Pipeline Troubleshooting

## Problem: "Dubbing pipeline is not available" message

If you see this warning in the Gradio interface, it means the dubbing pipeline dependencies are not properly installed.

### Quick Fix Steps

#### Option 1: Use the Fix Script
1. Open terminal in the project directory
2. Run: `python fix_dubbing.py`
3. Follow the instructions
4. Restart the application

#### Option 2: Manual Installation
1. Open terminal in the project directory
2. Activate the virtual environment:
   ```bash
   # Windows
   env\Scripts\activate
   
   # Linux/Mac
   source env/bin/activate
   ```
3. Install the missing dependency:
   ```bash
   pip install google-generativeai>=0.8.0
   ```
4. Restart the application

#### Option 3: Reinstall Everything
1. In Pinokio, click "Reset" to clean the installation
2. Click "Install" to reinstall everything
3. Wait for installation to complete
4. Click "Start" to launch the application

### Diagnostic Steps

#### Check What's Missing
Run the diagnostic script:
```bash
python diagnose_dubbing.py
```

This will tell you exactly what's missing.

#### Test the Installation
Run the simple test:
```bash
python test_dubbing_simple.py
```

### Common Issues and Solutions

#### Issue 1: Google Generative AI Not Installed
**Symptoms:** Import error for `google.generativeai`

**Solution:**
```bash
pip install google-generativeai>=0.8.0
```

#### Issue 2: Virtual Environment Issues
**Symptoms:** Dependencies installed but still not working

**Solution:**
1. Check if you're in the right virtual environment
2. Reinstall in the correct environment:
   ```bash
   # Activate the env first
   source env/bin/activate  # Linux/Mac
   env\Scripts\activate     # Windows
   
   # Then install
   pip install google-generativeai
   ```

#### Issue 3: Network/Firewall Issues
**Symptoms:** Installation fails with network errors

**Solution:**
1. Check internet connection
2. Try with different network
3. Use pip with trusted hosts:
   ```bash
   pip install --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org google-generativeai
   ```

#### Issue 4: Permission Issues
**Symptoms:** Permission denied errors during installation

**Solution:**
```bash
# Try with user flag
pip install --user google-generativeai

# Or run as administrator (Windows)
# Or use sudo (Linux/Mac) - not recommended in virtual env
```

#### Issue 5: Conflicting Dependencies
**Symptoms:** Installation succeeds but imports still fail

**Solution:**
```bash
# Uninstall and reinstall
pip uninstall google-generativeai
pip install google-generativeai>=0.8.0

# Or upgrade all dependencies
pip install --upgrade -r requirements.txt
```

### Verification Steps

After fixing, verify the installation:

1. **Check imports work:**
   ```bash
   python -c "import google.generativeai; print('✅ Working')"
   ```

2. **Check pipeline components:**
   ```bash
   python -c "from pipeline_controller import PipelineController; print('✅ Working')"
   ```

3. **Run full diagnostic:**
   ```bash
   python diagnose_dubbing.py
   ```

4. **Restart the application** and check if the dubbing tab is now available

### Still Not Working?

If you're still having issues:

1. **Check the console output** when starting the application for specific error messages
2. **Look at the terminal** where Pinokio is running for detailed error logs
3. **Try the manual installation** outside of Pinokio:
   ```bash
   cd /path/to/your/project
   pip install google-generativeai tiktoken
   python app.py
   ```

### Getting Help

If none of these solutions work:

1. Run `python diagnose_dubbing.py` and save the output
2. Check the error messages in the terminal
3. Note your operating system and Python version
4. Create an issue with all this information

### Success Indicators

You'll know it's working when:
- ✅ No warning message in the Gradio interface
- ✅ "Dubbing Pipeline" tab is fully functional
- ✅ You can see automatic/manual mode options
- ✅ Template generation works
- ✅ No import errors in the console

### API Keys

Once the pipeline is working, you'll need:
- **Gemini API keys** from [Google AI Studio](https://makersuite.google.com/app/apikey)
- Multiple keys recommended for better reliability

The dubbing pipeline will guide you through the API key setup once it's properly installed.