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
  apiKey: process.env.OPENAI_API_KEY
});

const replicate = new Replicate({
  auth: process.env.REPLICATE_API_TOKEN,
});

// Create output directory
const outputDir = 'outputs';
if (!fs.existsSync(outputDir)) {
  fs.mkdirSync(outputDir);
}

// Routes
app.get('/', (req, res) => {
  res.sendFile(path.join(__dirname, 'public', 'index.html'));
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

    // Agent 1: Analyze the image content
    const analysisPrompt = `Analyze this image and provide detailed information about:
    1. What the image shows (landmarks, buildings, nature, etc.)
    2. The quality issues (blur, noise, low resolution, etc.)
    3. The historical or cultural significance if any
    4. The best approach for restoration
    
    Image: [base64 encoded]`;

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
      max_tokens: 500
    });

    const analysis = analysisResponse.choices[0].message.content;

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
      max_tokens: 200
    });

    const location = locationResponse.choices[0].message.content;

    res.json({
      success: true,
      analysis: analysis,
      location: location,
      originalImage: req.file.filename
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
    const enhancedImagePath = path.join(__dirname, 'outputs', enhancedImageName);

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
      downloadUrl: `/download/${encodeURIComponent(`final-${originalImage}`)}`
    });

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

// Error handling middleware
app.use((error, req, res, next) => {
  console.error(error);
  res.status(500).json({ error: 'Something went wrong!' });
});

app.listen(PORT, () => {
  console.log(`Image Restoration App running on http://localhost:${PORT}`);
});