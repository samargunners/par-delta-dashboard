# Troubleshooting Guide for Streamlit App

## Common Issues and Solutions

### 1. Health Check Error
```
❗️ The service has encountered an error while checking the health of the Streamlit app
```

**Possible Causes:**
- Import errors
- Missing secrets/configuration
- Syntax errors
- Memory issues
- Package compatibility problems

### 2. Import Errors
If you see import errors, check:
1. All packages in requirements.txt are installed
2. Package versions are compatible
3. No circular imports

### 3. Missing Secrets
The app requires these secrets to be configured:
```toml
# .streamlit/secrets.toml
SUPABASE_URL = "your-supabase-url"
SUPABASE_KEY = "your-supabase-key"
OPENAI_API_KEY = "your-openai-api-key"  # Optional
```

### 4. Debugging Steps

1. **Check Dependencies**
   ```bash
   cd streamlit_app
   python test_dependencies.py
   ```

2. **Use Debug Mode**
   - Go to Chat_Debug.py page first
   - Check all configuration items
   - Test database connection

3. **Check Logs**
   - Look at Streamlit Cloud logs
   - Check for specific error messages

4. **Test Locally**
   ```bash
   cd streamlit_app
   streamlit run streamlit_app.py
   ```

### 5. Fallback Solutions

If the main Chat.py doesn't work:
1. Use Chat_Debug.py to identify issues
2. Fix configuration problems
3. Check database connectivity
4. Verify all secrets are set

### 6. Production Deployment

For Streamlit Cloud:
1. Ensure secrets are set in Streamlit Cloud dashboard
2. Check that all dependencies are in requirements.txt
3. Verify the repository structure is correct

### 7. Memory Issues

If running out of memory:
1. Reduce the number of documents processed
2. Increase chunk size to reduce document count
3. Use smaller embedding models
4. Add data pagination

### 8. API Key Issues

For OpenAI API:
- The app will fall back to HuggingFace if OpenAI key is missing
- Check API key format and validity
- Verify API quota/credits
