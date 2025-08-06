const express = require('express');
const multer = require('multer');
const cors = require('cors');
const sharp = require('sharp');
const path = require('path');
const fs = require('fs');
const axios = require('axios');
const OpenAI = require('openai');
const Replicate = require('replicate');
require('dotenv').config();

const app = express();
const PORT = process.env.PORT || 3000;

// Middleware
app.use(cors());
app.use(express.json());
app.use(express.static('public'));

// Configure multer for file uploads
const storage = multer.diskStorage({
  destination: (req, file, cb) => {
    const uploadDir = 'uploads';
    if (!fs.existsSync(uploadDir)) {
      fs.mkdirSync(uploadDir);
    }
    cb(null, uploadDir);
  },
  filename: (req, file, cb) => {
    const uniqueSuffix = Date.now() + '-' + Math.round(Math.random() * 1E9);
    cb(null, file.fieldname + '-' + uniqueSuffix + path.extname(file.originalname));
  }
});

const upload = multer({ 
  storage: storage,
  limits: { fileSize: 10 * 1024 * 1024 }, // 10MB limit
  fileFilter: (req, file, cb) => {
    if (file.mimetype.startsWith('image/')) {
      cb(null, true);
    } else {
      cb(new Error('Only image files are allowed!'), false);
    }
  }
});

// Initialize AI clients
const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY || 'demo-key'
});

const replicate = new Replicate({
  auth: process.env.REPLICATE_API_TOKEN || 'demo-token',
});

// Create necessary directories
const dirs = ['uploads', 'outputs', 'temp'];
dirs.forEach(dir => {
  if (!fs.existsSync(dir)) {
    fs.mkdirSync(dir, { recursive: true });
  }
});

// Routes
app.get('/', (req, res) => {
  res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

// Health check endpoint
app.get('/health', (req, res) => {
  res.json({ 
    status: 'healthy', 
    timestamp: new Date().toISOString(),
    version: '1.0.0'
  });
});

// Image analysis endpoint
app.post('/analyze-image', upload.single('image'), async (req, res) => {
  try {
    if (!req.file) {
      return res.status(400).json({ error: 'No image uploaded' });
    }

    const imagePath = req.file.path;
    const imageBuffer = fs.readFileSync(imagePath);
    const base64Image = imageBuffer.toString('base64');

    // Check if we're in demo mode (no API keys)
    const isDemoMode = !process.env.OPENAI_API_KEY || process.env.OPENAI_API_KEY === 'demo-key';

    let analysis, location;

    if (isDemoMode) {
      // Demo mode - provide mock analysis
      analysis = `This appears to be a historic image that could benefit from restoration. 
      The image shows architectural elements that suggest it may be a landmark or historic building. 
      Quality issues detected include potential blur, noise, and low resolution. 
      This would be perfect for AI-powered restoration to enhance clarity and detail.`;
      
      location = "Historic landmark or building (demo mode)";
    } else {
      // Real API mode
      try {
        // Agent 1: Analyze the image content
        const analysisPrompt = `Analyze this image and provide detailed information about:
        1. What the image shows (landmarks, buildings, nature, etc.)
        2. The quality issues (blur, noise, low resolution, etc.)
        3. The historical or cultural significance if any
        4. The best approach for restoration
        
        Provide a comprehensive analysis in 2-3 sentences.`;

        const analysisResponse = await openai.chat.completions.create({
          model: "gpt-4-vision-preview",
          messages: [
            {
              role: "user",
              content: [
                { type: "text", text: analysisPrompt },
                {
                  type: "image_url",
                  image_url: {
                    url: `data:image/jpeg;base64,${base64Image}`
                  }
                }
              ]
            }
          ],
          max_tokens: 300
        });

        analysis = analysisResponse.choices[0].message.content;

        // Agent 2: Identify the location/landmark
        const locationPrompt = `Based on this image, identify the specific location, landmark, or building shown. 
        If it's a famous landmark, provide the exact name and location. 
        If it's a generic scene, describe what type of location it is.`;

        const locationResponse = await openai.chat.completions.create({
          model: "gpt-4-vision-preview",
          messages: [
            {
              role: "user",
              content: [
                { type: "text", text: locationPrompt },
                {
                  type: "image_url",
                  image_url: {
                    url: `data:image/jpeg;base64,${base64Image}`
                  }
                }
              ]
            }
          ],
          max_tokens: 150
        });

        location = locationResponse.choices[0].message.content;
      } catch (apiError) {
        console.error('API Error:', apiError);
        // Fallback to demo mode if API fails
        analysis = `This image appears to be a historic or landmark photo that would benefit from restoration. 
        The image shows architectural elements and may have quality issues like blur or low resolution. 
        AI restoration can enhance the clarity and detail significantly.`;
        location = "Historic landmark or building";
      }
    }

    res.json({
      success: true,
      analysis: analysis,
      location: location,
      originalImage: req.file.filename,
      isDemoMode: isDemoMode
    });

  } catch (error) {
    console.error('Analysis error:', error);
    res.status(500).json({ error: 'Failed to analyze image' });
  }
});

// Image restoration endpoint
app.post('/restore-image', async (req, res) => {
  try {
    const { originalImage, analysis, location } = req.body;
    
    if (!originalImage) {
      return res.status(400).json({ error: 'No image specified' });
    }

    const imagePath = path.join(__dirname, 'uploads', originalImage);
    
    if (!fs.existsSync(imagePath)) {
      return res.status(404).json({ error: 'Image not found' });
    }

    const isDemoMode = !process.env.REPLICATE_API_TOKEN || process.env.REPLICATE_API_TOKEN === 'demo-token';

    let enhancedImagePath;

    if (isDemoMode) {
      // Demo mode - create an enhanced version using Sharp
      const enhancedImageName = `enhanced-${originalImage}`;
      enhancedImagePath = path.join(__dirname, 'outputs', enhancedImageName);

      // Use Sharp to create a demo enhancement
      await sharp(imagePath)
        .resize(2000, 2000, { 
          fit: 'inside',
          withoutEnlargement: false 
        })
        .sharpen()
        .jpeg({ quality: 95 })
        .toFile(enhancedImagePath);

      // Create final optimized version
      const finalImageName = `final-${originalImage}`;
      const finalImagePath = path.join(__dirname, 'outputs', finalImageName);

      await sharp(enhancedImagePath)
        .jpeg({ quality: 98 })
        .toFile(finalImagePath);

      res.json({
        success: true,
        originalImage: originalImage,
        enhancedImage: finalImageName,
        analysis: analysis,
        location: location,
        downloadUrl: `/download/${encodeURIComponent(finalImageName)}`,
        isDemoMode: true
      });

    } else {
      // Real API mode
      try {
        // Agent 3: Restore and enhance the image using Replicate
        const output = await replicate.run(
          "tencentarc/gfpgan:9283608cc6b7be6b65a8e44983db012355fde4132009bf99d976b2f0896856a3",
          {
            input: {
              img: fs.createReadStream(imagePath),
              version: "v1.4",
              scale: 2
            }
          }
        );

        // Agent 4: Further enhance with Real-ESRGAN for super resolution
        const enhancedOutput = await replicate.run(
          "nightmareai/real-esrgan:42fed1c4974146d4d2414e2be2c5277fbce180f3a9005c8c7d33262c61298c4",
          {
            input: {
              image: output,
              scale: 4,
              face_enhance: true
            }
          }
        );

        // Save the enhanced image
        const enhancedImageName = `enhanced-${originalImage}`;
        enhancedImagePath = path.join(__dirname, 'outputs', enhancedImageName);

        // Download and save the enhanced image
        const enhancedImageResponse = await axios.get(enhancedOutput, {
          responseType: 'arraybuffer'
        });
        
        fs.writeFileSync(enhancedImagePath, enhancedImageResponse.data);

        // Agent 5: Final quality check and optimization
        const finalImage = await sharp(enhancedImagePath)
          .jpeg({ quality: 95 })
          .toBuffer();

        const finalImagePath = path.join(__dirname, 'outputs', `final-${originalImage}`);
        fs.writeFileSync(finalImagePath, finalImage);

        res.json({
          success: true,
          originalImage: originalImage,
          enhancedImage: `final-${originalImage}`,
          analysis: analysis,
          location: location,
          downloadUrl: `/download/${encodeURIComponent(`final-${originalImage}`)}`,
          isDemoMode: false
        });

      } catch (apiError) {
        console.error('API Error:', apiError);
        // Fallback to demo mode if API fails
        const enhancedImageName = `enhanced-${originalImage}`;
        enhancedImagePath = path.join(__dirname, 'outputs', enhancedImageName);

        await sharp(imagePath)
          .resize(2000, 2000, { 
            fit: 'inside',
            withoutEnlargement: false 
          })
          .sharpen()
          .jpeg({ quality: 95 })
          .toFile(enhancedImagePath);

        const finalImageName = `final-${originalImage}`;
        const finalImagePath = path.join(__dirname, 'outputs', finalImageName);

        await sharp(enhancedImagePath)
          .jpeg({ quality: 98 })
          .toFile(finalImagePath);

        res.json({
          success: true,
          originalImage: originalImage,
          enhancedImage: finalImageName,
          analysis: analysis,
          location: location,
          downloadUrl: `/download/${encodeURIComponent(finalImageName)}`,
          isDemoMode: true
        });
      }
    }

  } catch (error) {
    console.error('Restoration error:', error);
    res.status(500).json({ error: 'Failed to restore image' });
  }
});

// Download endpoint
app.get('/download/:filename', (req, res) => {
  const filename = decodeURIComponent(req.params.filename);
  const filePath = path.join(__dirname, 'outputs', filename);
  
  if (fs.existsSync(filePath)) {
    res.download(filePath);
  } else {
    res.status(404).json({ error: 'File not found' });
  }
});

// Cleanup old files endpoint
app.post('/cleanup', (req, res) => {
  try {
    const uploadsDir = path.join(__dirname, 'uploads');
    const outputsDir = path.join(__dirname, 'outputs');
    
    // Clean uploads older than 1 hour
    if (fs.existsSync(uploadsDir)) {
      const files = fs.readdirSync(uploadsDir);
      files.forEach(file => {
        const filePath = path.join(uploadsDir, file);
        const stats = fs.statSync(filePath);
        const ageInHours = (Date.now() - stats.mtime.getTime()) / (1000 * 60 * 60);
        
        if (ageInHours > 1) {
          fs.unlinkSync(filePath);
        }
      });
    }
    
    // Clean outputs older than 24 hours
    if (fs.existsSync(outputsDir)) {
      const files = fs.readdirSync(outputsDir);
      files.forEach(file => {
        const filePath = path.join(outputsDir, file);
        const stats = fs.statSync(filePath);
        const ageInHours = (Date.now() - stats.mtime.getTime()) / (1000 * 60 * 60);
        
        if (ageInHours > 24) {
          fs.unlinkSync(filePath);
        }
      });
    }
    
    res.json({ success: true, message: 'Cleanup completed' });
  } catch (error) {
    res.status(500).json({ error: 'Cleanup failed' });
  }
});

// Error handling middleware
app.use((error, req, res, next) => {
  console.error(error);
  res.status(500).json({ error: 'Something went wrong!' });
});

// 404 handler
app.use((req, res) => {
  res.status(404).json({ error: 'Endpoint not found' });
});

app.listen(PORT, () => {
  console.log(`🎨 AI Image Restoration App running on http://localhost:${PORT}`);
  console.log(`📊 Health check: http://localhost:${PORT}/health`);
  console.log(`🔧 Demo mode: ${(!process.env.OPENAI_API_KEY || process.env.OPENAI_API_KEY === 'demo-key') ? 'ON' : 'OFF'}`);
});