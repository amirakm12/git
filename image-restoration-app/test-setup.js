const fs = require('fs');
const path = require('path');

console.log('🔍 Testing Image Restoration App Setup...\n');

// Check if required directories exist
const requiredDirs = ['public', 'uploads', 'outputs'];
requiredDirs.forEach(dir => {
  if (!fs.existsSync(dir)) {
    console.log(`❌ Directory '${dir}' not found. Creating...`);
    fs.mkdirSync(dir, { recursive: true });
  } else {
    console.log(`✅ Directory '${dir}' exists`);
  }
});

// Check if required files exist
const requiredFiles = [
  'server.js',
  'package.json',
  'public/index.html',
  '.env.example'
];

requiredFiles.forEach(file => {
  if (fs.existsSync(file)) {
    console.log(`✅ File '${file}' exists`);
  } else {
    console.log(`❌ File '${file}' not found`);
  }
});

// Check if .env file exists
if (fs.existsSync('.env')) {
  console.log('✅ .env file exists');
} else {
  console.log('⚠️  .env file not found. Please copy .env.example to .env and add your API keys');
}

// Check package.json dependencies
try {
  const packageJson = JSON.parse(fs.readFileSync('package.json', 'utf8'));
  const requiredDeps = ['express', 'multer', 'cors', 'sharp', 'axios', 'dotenv', 'openai', 'replicate'];
  
  console.log('\n📦 Checking dependencies...');
  requiredDeps.forEach(dep => {
    if (packageJson.dependencies && packageJson.dependencies[dep]) {
      console.log(`✅ ${dep} is listed in dependencies`);
    } else {
      console.log(`❌ ${dep} is missing from dependencies`);
    }
  });
} catch (error) {
  console.log('❌ Error reading package.json');
}

console.log('\n🎯 Setup Test Complete!');
console.log('\n📋 Next Steps:');
console.log('1. Copy .env.example to .env');
console.log('2. Add your OpenAI API key to .env');
console.log('3. Add your Replicate API token to .env');
console.log('4. Run: npm start');
console.log('5. Open http://localhost:3000 in your browser');