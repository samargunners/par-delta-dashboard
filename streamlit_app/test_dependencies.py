#!/usr/bin/env python3
"""
Simple test script to check if all dependencies are working
Run this before starting the Streamlit app to verify everything is set up correctly
"""

import sys

def test_imports():
    """Test all required imports"""
    print("Testing imports...")
    
    try:
        import streamlit as st
        print("✅ streamlit imported successfully")
    except ImportError as e:
        print(f"❌ streamlit import failed: {e}")
        return False
    
    try:
        import pandas as pd
        print("✅ pandas imported successfully")
    except ImportError as e:
        print(f"❌ pandas import failed: {e}")
        return False
    
    try:
        from supabase import create_client
        print("✅ supabase imported successfully")
    except ImportError as e:
        print(f"❌ supabase import failed: {e}")
        return False
    
    try:
        from langchain_openai import ChatOpenAI, OpenAIEmbeddings
        print("✅ langchain_openai imported successfully")
    except ImportError as e:
        print(f"❌ langchain_openai import failed: {e}")
        return False
    
    try:
        from langchain.chains import RetrievalQA
        print("✅ langchain.chains imported successfully")
    except ImportError as e:
        print(f"❌ langchain.chains import failed: {e}")
        return False
    
    try:
        from langchain_community.vectorstores import FAISS
        print("✅ langchain_community.vectorstores imported successfully")
    except ImportError as e:
        print(f"❌ langchain_community.vectorstores import failed: {e}")
        return False
    
    try:
        from langchain.text_splitter import RecursiveCharacterTextSplitter
        print("✅ langchain.text_splitter imported successfully")
    except ImportError as e:
        print(f"❌ langchain.text_splitter import failed: {e}")
        return False
    
    try:
        from langchain.prompts import PromptTemplate
        print("✅ langchain.prompts imported successfully")
    except ImportError as e:
        print(f"❌ langchain.prompts import failed: {e}")
        return False
    
    try:
        from langchain.schema import Document
        print("✅ langchain.schema imported successfully")
    except ImportError as e:
        print(f"❌ langchain.schema import failed: {e}")
        return False
    
    try:
        from langchain_community.embeddings import HuggingFaceEmbeddings
        print("✅ langchain_community.embeddings imported successfully")
    except ImportError as e:
        print(f"❌ langchain_community.embeddings import failed: {e}")
        return False
    
    return True

def test_basic_functionality():
    """Test basic functionality"""
    print("\nTesting basic functionality...")
    
    try:
        import pandas as pd
        df = pd.DataFrame({"test": [1, 2, 3]})
        print("✅ pandas DataFrame creation works")
    except Exception as e:
        print(f"❌ pandas DataFrame test failed: {e}")
        return False
    
    try:
        from langchain.schema import Document
        doc = Document(page_content="test", metadata={"test": True})
        print("✅ LangChain Document creation works")
    except Exception as e:
        print(f"❌ LangChain Document test failed: {e}")
        return False
    
    try:
        from langchain.text_splitter import RecursiveCharacterTextSplitter
        splitter = RecursiveCharacterTextSplitter(chunk_size=100, chunk_overlap=20)
        print("✅ Text splitter creation works")
    except Exception as e:
        print(f"❌ Text splitter test failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("=== Dependency Test Script ===")
    
    import_success = test_imports()
    functionality_success = test_basic_functionality()
    
    if import_success and functionality_success:
        print("\n🎉 All tests passed! Your dependencies are working correctly.")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed. Please check the error messages above.")
        sys.exit(1)
