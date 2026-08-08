# 🚀 DocuMind AI - Deployment Guide

This guide will help you deploy DocuMind AI to [Render](https://render.com) or [Vercel](https://vercel.com).

## 📋 Prerequisites

Before deploying, you'll need:

1. **OpenRouter API Key** - Get a free key from [OpenRouter](https://openrouter.ai/)
2. **Qdrant Cloud Account** - Sign up for free tier at [Qdrant Cloud](https://qdrant.tech/cloud/)
3. **GitHub Repository** - Push your code to GitHub
4. **Render/Vercel Account** - Free accounts work fine

## 🔧 Environment Variables

You'll need to configure these environment variables:

### Required
- `OPENROUTER_API_KEY` - Your OpenRouter API key
- `QDRANT_URL` - Your Qdrant Cloud URL (e.g., `https://xxxxx.cloud.qdrant.io`)
- `QDRANT_API_KEY` - Your Qdrant Cloud API key

### Optional (defaults provided)
- `QDRANT_COLLECTION` - Default: `pdf_docs`
- `EMBEDDING_MODEL` - Default: `sentence-transformers/all-MiniLM-L6-v2`
- `CHUNK_SIZE` - Default: `800`
- `CHUNK_OVERLAP` - Default: `150`
- `TOP_K` - Default: `5`
- `PDF_DIR` - Default: `data/pdfs`
- `PORT` - Default: `5000`
- `DEBUG` - Default: `false`

## 🎯 Deploy to Render

### Step 1: Set Up Qdrant Cloud

1. Go to [Qdrant Cloud](https://qdrant.tech/cloud/)
2. Sign up and create a free cluster
3. Copy your cluster URL and API key

### Step 2: Push to GitHub

```bash
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/yourusername/documind-ai.git
git push -u origin main
```

### Step 3: Deploy on Render

1. Go to [Render Dashboard](https://dashboard.render.com/)
2. Click **"New +"** → **"Web Service"**
3. Connect your GitHub repository
4. Render will automatically detect the `render.yaml` configuration
5. Configure environment variables:
   - `OPENROUTER_API_KEY`: Your OpenRouter key
   - `QDRANT_URL`: Your Qdrant Cloud URL
   - `QDRANT_API_KEY`: Your Qdrant Cloud API key
6. Click **"Deploy Web Service"**

### Step 4: Monitor Deployment

- Render will build and deploy your application
- Monitor the logs in the Render dashboard
- Once deployed, you'll get a URL like `https://documind-ai.onrender.com`

## ☁️ Deploy to Vercel

### Step 1: Set Up Qdrant Cloud

Same as Render deployment above.

### Step 2: Push to GitHub

Same as Render deployment above.

### Step 3: Deploy on Vercel

1. Go to [Vercel Dashboard](https://vercel.com/dashboard)
2. Click **"Add New..."** → **"Project"**
3. Import your GitHub repository
4. Vercel will automatically detect the `vercel.json` configuration
5. Configure environment variables:
   - `OPENROUTER_API_KEY`: Your OpenRouter key
   - `QDRANT_URL`: Your Qdrant Cloud URL
   - `QDRANT_API_KEY`: Your Qdrant Cloud API key
6. Click **"Deploy"**

### Step 4: Monitor Deployment

- Vercel will build and deploy your application
- Monitor the deployment logs
- Once deployed, you'll get a URL like `https://documind-ai.vercel.app`

## 🔍 Troubleshooting

### Common Issues

**1. Build Fails**
- Check that all dependencies are in `requirements.txt`
- Ensure Python version is compatible (we use 3.9.16)
- Check build logs for specific errors

**2. Runtime Errors**
- Verify all environment variables are set correctly
- Check that Qdrant Cloud is accessible
- Ensure OpenRouter API key is valid

**3. File Upload Issues**
- Check file size limits (default 16MB)
- Verify storage permissions on the platform
- Monitor logs for upload errors

**4. Qdrant Connection Issues**
- Verify Qdrant Cloud URL is correct
- Check API key is valid
- Ensure Qdrant cluster is running

### Debug Mode

To enable debug mode for troubleshooting:
- Set `DEBUG=true` in environment variables
- Check the platform logs for detailed error messages

## 📊 Monitoring

### Render
- View logs in the Render dashboard
- Monitor metrics in the "Metrics" tab
- Set up alerts for downtime

### Vercel
- View logs in the Vercel dashboard
- Monitor performance in the "Analytics" tab
- Set up log drains for external monitoring

## 🔒 Security Considerations

1. **Never commit `.env` files** to your repository
2. **Use environment variables** for all sensitive data
3. **Enable HTTPS** - Both Render and Vercel provide this by default
4. **Monitor usage** - Watch for unusual API usage patterns
5. **Regular updates** - Keep dependencies updated

## 💰 Cost Optimization

### Free Tier Usage
- **Render**: Free tier available with limitations
- **Vercel**: Free tier with generous limits
- **Qdrant Cloud**: Free tier with 1GB storage
- **OpenRouter**: Pay per usage, but has free models

### Optimization Tips
- Use free OpenRouter models when possible
- Monitor Qdrant storage usage
- Clean up old PDF files regularly
- Consider implementing caching for frequent queries

## 🎨 Customization

### Branding
- Update the title and branding in `templates/index.html`
- Modify colors in the CSS variables
- Add your own logo and styling

### Features
- Add user authentication
- Implement document history
- Add export functionality
- Create multiple document collections

## 📈 Scaling

### When to Scale
- High traffic (>1000 requests/day)
- Large document collections (>1000 PDFs)
- Complex queries requiring more processing

### Scaling Options
- **Render**: Upgrade to paid plans for more resources
- **Vercel**: Upgrade to Pro plan for enhanced features
- **Qdrant**: Upgrade to larger clusters
- **Add CDN**: For static assets

## 🆚 Platform Comparison

| Feature | Render | Vercel |
|---------|--------|--------|
| Python Support | ✅ Native | ✅ Via Runtime |
| Free Tier | ✅ Yes | ✅ Yes |
| Easy Setup | ✅ Yes | ✅ Yes |
| Custom Domains | ✅ Yes | ✅ Yes |
| Build Time | ⚡ Fast | ⚡ Very Fast |
| Logs | ✅ Detailed | ✅ Detailed |
| Edge Functions | ❌ No | ✅ Yes |

## 📞 Support

If you encounter issues:
1. Check the platform logs first
2. Review this troubleshooting guide
3. Check platform documentation
4. Open an issue on GitHub

## 🎉 Success!

Your DocuMind AI application is now live! Users can:
- Upload PDF documents through the web interface
- Process documents with one click
- Ask questions and get AI-powered answers
- View citations and sources

Congratulations on deploying your AI-powered document analysis system!