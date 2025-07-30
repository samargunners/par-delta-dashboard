# RAG (Retrieval-Augmented Generation) Implementation

## Overview
This document explains the enhanced RAG implementation in the Chat.py file for the business intelligence dashboard.

## What is RAG?
Retrieval-Augmented Generation (RAG) is an AI technique that combines:
1. **Information Retrieval**: Finding relevant documents/data
2. **Text Generation**: Using an LLM to generate responses based on retrieved context

## Our RAG Implementation

### Components

#### 1. Data Ingestion
- **Source**: Supabase database tables
- **Tables**: 11 business tables (labor, sales, employees, schedules, inventory)
- **Caching**: 1-hour TTL for performance optimization

#### 2. Document Processing
- **Enhanced Chunking**: Intelligent text splitting with context preservation
- **Metadata Enrichment**: Each document includes table name, type, and relevant metadata
- **Semantic Context**: Business-friendly formatting (e.g., "The labor_cost is $150")

#### 3. Vector Storage
- **Primary**: OpenAI text-embedding-3-small (cost-effective)
- **Fallback**: HuggingFace sentence-transformers/all-MiniLM-L6-v2 (free)
- **Storage**: FAISS vector database for fast similarity search
- **Retrieval**: Similarity score threshold (0.5) with top-5 results

#### 4. Query Processing
- **LLM**: OpenAI GPT-3.5 Turbo (cost-effective)
- **Custom Prompt**: Business-focused prompt template
- **Source Tracking**: Returns source documents for transparency

### Key Features

#### Enhanced Document Chunking
```python
def create_enhanced_documents(all_data):
    # Creates documents with rich metadata
    # Adds table summaries as context
    # Semantic formatting for better understanding
```

#### Intelligent Retrieval
- Similarity score threshold filtering
- Top-K retrieval (K=5)
- Metadata-aware search

#### Custom Business Prompt
- Focuses on business analysis
- Requests specific numbers and dates
- Professional formatting
- Source attribution

#### User Experience
- Sample questions sidebar
- Source document viewing option
- Performance monitoring
- Error handling with fallbacks

### Performance Optimizations

1. **Caching**: 1-hour TTL on data fetching
2. **Chunking**: Optimal chunk size (1000 chars) with overlap (200 chars)
3. **Embedding Model**: Cost-effective OpenAI model with free fallback
4. **Retrieval**: Threshold-based filtering to reduce noise

### Usage Examples

**Labor Questions:**
- "What is the total labor cost for this week?"
- "Which employees worked overtime recently?"
- "Show me variance in labor costs vs targets"

**Sales Questions:**
- "What are the top-selling donut flavors?"
- "What are the peak sales hours?"

**Employee Questions:**
- "How many employees are scheduled for tomorrow?"
- "What's the average hourly labor cost?"

**Inventory Questions:**
- "Which store locations have inventory issues?"

### Error Handling

1. **API Quota Exceeded**: Automatic fallback to HuggingFace embeddings
2. **Connection Issues**: Graceful error messages with debugging info
3. **Missing Data**: Clear indication when information isn't available
4. **Invalid Queries**: Helpful error messages

### Future Enhancements

1. **Query History**: Store and analyze common questions
2. **Advanced Filtering**: Date range, store location filters
3. **Multi-modal**: Add support for charts and graphs in responses
4. **Real-time Updates**: Live data streaming for up-to-date responses
5. **Custom Business Rules**: Industry-specific analysis patterns

## Technical Dependencies

- `langchain`: Core RAG framework
- `langchain-openai`: OpenAI integration
- `faiss-cpu`: Vector similarity search
- `sentence-transformers`: Fallback embeddings
- `streamlit`: User interface
- `supabase`: Data source

## Configuration

Required Streamlit secrets:
```toml
OPENAI_API_KEY = "your-openai-key"
SUPABASE_URL = "your-supabase-url"
SUPABASE_KEY = "your-supabase-key"
```
