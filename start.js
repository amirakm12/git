#!/usr/bin/env node

const fs = require('fs');
const path = require('path');
const { spawn } = require('child_process');

console.log('🎨 AI Image Restoration App - Startup');
console.log('=====================================\n');

// Check if .env exists
if (!fs.existsSync('.env')) {
  console.log('⚠️  .env file not found. Creating from template...');
  if (fs.existsSync('.env.example')) {
    fs.copyFileSync('.env.example', '.env');
    console.log('✅ .env file created from template');
    console.log('📝 Please edit .env and add your API keys:');
    console.log('   - OPENAI_API_KEY');
    console.log('   - REPLICATE_API_TOKEN');
  } else {
    console.log('❌ .env.example not found');
    process.exit(1);
  }
}

// Check required directories
const requiredDirs = ['uploads', 'outputs', 'temp'];
requiredDirs.forEach(dir => {
  if (!fs.existsSync(dir)) {
    fs.mkdirSync(dir, { recursive: true });
    console.log(`✅ Created directory: ${dir}`);
  }
});

// Check if node_modules exists
if (!fs.existsSync('node_modules')) {
  console.log('📦 Installing dependencies...');
  const install = spawn('npm', ['install'], { stdio: 'inherit' });
  
  install.on('close', (code) => {
    if (code === 0) {
      console.log('✅ Dependencies installed successfully');
      startServer();
    } else {
      console.log('❌ Failed to install dependencies');
      process.exit(1);
    }
  });
} else {
  startServer();
}

function startServer() {
  console.log('🚀 Starting AI Image Restoration App...\n');
  
  const server = spawn('node', ['server.js'], { stdio: 'inherit' });
  
  server.on('close', (code) => {
    if (code !== 0) {
      console.log(`❌ Server exited with code ${code}`);
      process.exit(code);
    }
  });
  
  // Handle graceful shutdown
  process.on('SIGINT', () => {
    console.log('\n🛑 Shutting down gracefully...');
    server.kill('SIGINT');
  });
  
  process.on('SIGTERM', () => {
    console.log('\n🛑 Shutting down gracefully...');
    server.kill('SIGTERM');
  });
}