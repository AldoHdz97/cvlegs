# CV Assistant Frontend - Backend Integration

This directory contains the frontend integration files to connect your Streamlit CV Assistant to your FastAPI backend running on Railway.

## 🚀 Quick Setup

### 1. **Add Files to Your Streamlit App**

Place these files in the same directory as your existing `app.py`:

```
your-streamlit-app/
├── app.py (your existing file)
├── api_client.py (NEW)
├── response_formatter.py (NEW)
├── config.py (NEW)
├── requirements.txt (UPDATED)
└── README.md (this file)
```

### 2. **Install Dependencies**

```bash
pip install -r requirements.txt
```

### 3. **Replace Your App File**

1. **Backup your current app.py:**
   ```bash
   cp app.py app_backup.py
   ```

### 4. **Run the App**

```bash
streamlit run app.py
```

## 🔧 Configuration

### Backend URL Configuration

The app is pre-configured to connect to your Railway backend:
- **Production URL:** `https://cvbrain-production.up.railway.app`

If you need to change the backend URL, update it in `config.py`:

```python
BACKEND_URL: str = "https://your-backend.railway.app"
```

### Environment Variables (Optional)

You can also set environment variables:

```bash
export BACKEND_URL="https://your-backend.railway.app"
export API_TIMEOUT="60.0"
export ENVIRONMENT="development"
```

### Streamlit Secrets (For Railway Deployment)

In your Streamlit Cloud/Railway deployment, add these secrets:

```toml
# .streamlit/secrets.toml
BACKEND_URL = "https://cvbrain-production.up.railway.app"
```

## 🎯 Features

### ✅ **What's New**

1. **Real Backend Integration**
   - Connects to your CV-AI backend on Railway
   - Uses httpx for modern async HTTP requests
   - Intelligent query classification

2. **Streaming Responses**
   - Maintains Streamlit's native chat streaming
   - Real-time response processing
   - Smart loading indicators

3. **Advanced Error Handling**
   - Circuit breaker pattern for resilience
   - Retry logic with exponential backoff
   - Graceful fallback when backend is offline

4. **Response Enhancement**
   - Intelligent content formatting
   - Confidence score visualization
   - Source attribution and metadata display

5. **Performance Optimization**
   - Response caching (5-minute TTL)
   - Connection pooling
   - Query type classification

### 🎨 **UI Enhancements**

- **Backend Status Indicator:** Green/red indicator showing connection status
- **Advanced Options:** Toggle metadata and confidence scores
- **Error Messages:** User-friendly error formatting
- **Performance Metrics:** Response time and confidence tracking

## 🛠️ Backend API Integration

### Query Processing Flow

1. **User Input** → Query classification (skills, experience, etc.)
2. **API Request** → POST to `/v1/query` with structured payload
3. **Response Processing** → Format and enhance content
4. **Streaming Display** → Word-by-word streaming effect

### Request Format

```json
{
  "question": "What are your main technical skills?",
  "k": 3,
  "query_type": "technical",
  "response_format": "detailed",
  "include_sources": true,
  "language": "en"
}
```

### Response Format

```json
{
  "answer": "Enhanced response content...",
  "confidence_score": 0.89,
  "query_type": "technical",
  "relevant_chunks": 3,
  "processing_time": 2.34,
  "sources": ["source1", "source2"]
}
```

## 📊 Monitoring & Debugging

### Backend Status

The app includes real-time backend monitoring:
- **Green indicator:** Backend is healthy and responding
- **Red indicator:** Backend is offline or experiencing issues

### Debug Information

Enable debug mode in the sidebar to see:
- Response metadata
- Confidence scores
- Processing times
- Source attribution
- Cache hit/miss status

### Logs

Check the browser console for detailed logs:
- API request/response details
- Error messages
- Performance metrics

## 🚨 Troubleshooting

### Common Issues

1. **Backend Offline**
   - Check if `cvbrain-production.up.railway.app` is accessible
   - Look for Railway service status
   - Try the reconnect button in the sidebar

2. **CORS Errors**
   - Ensure your backend has proper CORS configuration
   - Check browser console for CORS-related errors

3. **Timeout Issues**
   - Increase `API_TIMEOUT` in `config.py`
   - Check backend response times

4. **Import Errors**
   - Ensure all files are in the same directory
   - Check that `requirements.txt` dependencies are installed

### Test Backend Connection

```python
import httpx
import asyncio

async def test_backend():
    async with httpx.AsyncClient() as client:
        response = await client.get("https://cvbrain-production.up.railway.app/health")
        print(f"Status: {response.status_code}")
        
asyncio.run(test_backend())
```

## 🔄 Development Workflow

### Local Development

1. **Start your backend locally:**
   ```bash
   cd cv_ai_backend
   uvicorn app.main:app --reload --port 8000
   ```

2. **Update backend URL:**
   ```python
   # In config.py
   BACKEND_URL: str = "http://localhost:8000"
   ```

3. **Run Streamlit:**
   ```bash
   streamlit run app.py
   ```

### Deployment to Railway

1. **Deploy backend first** (your existing Railway deployment)
2. **Deploy frontend** with the integrated files
3. **Set environment variables** in Railway dashboard

## 📝 Notes

- The app maintains backward compatibility with your existing UI design
- All streaming effects and animations are preserved
- Interview scheduling functionality remains unchanged
- The backend integration is completely modular and can be easily modified

## 🆘 Support

If you encounter issues:

1. Check the backend status at: `https://cvbrain-production.up.railway.app/health`
2. Review browser console logs
3. Test backend connectivity independently
4. Ensure all dependencies are properly installed

## 🎉 Next Steps

Once this integration is working:

1. **Add Authentication** (if needed)
2. **Implement Interview Scheduling Backend**
3. **Add File Upload Features**
4. **Enhanced Analytics and Monitoring**
5. **Performance Optimization**
