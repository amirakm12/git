# 🎨 AI Image Restoration App

A powerful web application that uses multiple AI agents to analyze, restore, and enhance low-quality images into high-resolution masterpieces. Perfect for restoring historic photos, landmarks, and any image that needs quality improvement.

## ✨ Features

- **Multi-Agent AI Processing**: Uses 5 different AI agents for comprehensive image analysis and restoration
- **Drag & Drop Interface**: Beautiful, modern UI with intuitive drag-and-drop functionality
- **Real-time Progress Tracking**: Visual progress indicators during processing
- **High-Resolution Output**: Produces print-ready, high-quality images
- **Landmark Recognition**: Automatically identifies famous locations and landmarks
- **Quality Analysis**: Detailed analysis of image issues and restoration approach
- **Download Ready**: Direct download of enhanced images

## 🤖 AI Agents Used

1. **Analysis Agent**: Analyzes image content, quality issues, and historical significance
2. **Location Agent**: Identifies specific landmarks, buildings, or locations
3. **Restoration Agent**: Uses GFPGAN for face and general image restoration
4. **Enhancement Agent**: Uses Real-ESRGAN for super-resolution enhancement
5. **Optimization Agent**: Final quality check and optimization

## 🚀 Quick Start

### Prerequisites

- Node.js (v14 or higher)
- npm or yarn
- OpenAI API key
- Replicate API token

### Installation

1. **Clone and navigate to the project**:
   ```bash
   cd image-restoration-app
   ```

2. **Install dependencies**:
   ```bash
   npm install
   ```

3. **Set up environment variables**:
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` and add your API keys:
   ```env
   OPENAI_API_KEY=your_openai_api_key_here
   REPLICATE_API_TOKEN=your_replicate_api_token_here
   PORT=3000
   ```

4. **Start the application**:
   ```bash
   npm start
   ```

5. **Open your browser** and go to `http://localhost:3000`

## 🔧 API Keys Setup

### OpenAI API Key
1. Go to [OpenAI Platform](https://platform.openai.com/)
2. Create an account or sign in
3. Navigate to API Keys section
4. Create a new API key
5. Add it to your `.env` file

### Replicate API Token
1. Go to [Replicate](https://replicate.com/)
2. Create an account or sign in
3. Navigate to your account settings
4. Generate an API token
5. Add it to your `.env` file

## 📖 Usage

1. **Upload Image**: Drag and drop or click to upload an image (JPG, PNG, up to 10MB)

2. **Analysis**: The app will automatically analyze your image and provide:
   - Location identification
   - Quality assessment
   - Restoration recommendations

3. **Restore**: Click the "Restore Image" button to begin the enhancement process

4. **Download**: Once complete, download your high-resolution restored image

## 🎯 Perfect For

- **Historic Photos**: Restore old family photos or historical images
- **Landmark Photos**: Enhance photos of famous buildings and monuments
- **Low-Quality Images**: Improve blurry or low-resolution images
- **Print Preparation**: Create high-quality images suitable for printing
- **Archival Work**: Preserve and enhance important historical images

## 🛠️ Technical Details

### Backend Technologies
- **Node.js**: Server runtime
- **Express.js**: Web framework
- **Multer**: File upload handling
- **Sharp**: Image processing
- **OpenAI API**: Image analysis and content recognition
- **Replicate**: AI model hosting and execution

### Frontend Technologies
- **HTML5**: Structure
- **CSS3**: Modern styling with gradients and animations
- **JavaScript**: Interactive functionality
- **Drag & Drop API**: File upload interface

### AI Models Used
- **GPT-4 Vision**: Image analysis and content recognition
- **GFPGAN**: Face and general image restoration
- **Real-ESRGAN**: Super-resolution enhancement

## 📁 Project Structure

```
image-restoration-app/
├── public/
│   └── index.html          # Frontend interface
├── uploads/                # Temporary uploaded images
├── outputs/                # Processed and enhanced images
├── server.js              # Main server file
├── package.json           # Dependencies and scripts
├── .env.example          # Environment variables template
└── README.md             # This file
```

## 🔒 Security Features

- File type validation (images only)
- File size limits (10MB max)
- Secure file handling
- Environment variable protection
- Input sanitization

## 🚀 Deployment

### Local Development
```bash
npm run dev
```

### Production
```bash
npm start
```

### Environment Variables for Production
Make sure to set these environment variables in your production environment:
- `OPENAI_API_KEY`
- `REPLICATE_API_TOKEN`
- `PORT` (optional)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

## 🆘 Support

If you encounter any issues:

1. Check that all API keys are correctly set
2. Ensure you have sufficient API credits
3. Verify file upload size limits
4. Check the console for error messages

## 🎉 Example Use Cases

- **Washington, D.C. Monuments**: Restore photos of the Lincoln Memorial, Capitol Building, etc.
- **Historic Buildings**: Enhance photos of old architecture
- **Family Photos**: Restore old family portraits
- **Landscape Photos**: Improve scenic photography
- **Document Preservation**: Enhance important historical documents

---

**Built with ❤️ using cutting-edge AI technology**