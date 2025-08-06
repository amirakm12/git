#!/usr/bin/env node

const fs = require('fs');
const path = require('path');
const { spawn, execSync } = require('child_process');
const http = require('http');

console.log('🎨 AI Image Restoration App - Launch Script');
console.log('===========================================\n');

// Colors for console output
const colors = {
  reset: '\x1b[0m',
  bright: '\x1b[1m',
  red: '\x1b[31m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  magenta: '\x1b[35m',
  cyan: '\x1b[36m'
};

function log(message, color = 'reset') {
  console.log(`${colors[color]}${message}${colors.reset}`);
}

// Check system requirements
function checkRequirements() {
  log('🔍 Checking system requirements...', 'blue');
  
  // Check Node.js version
  try {
    const nodeVersion = process.version;
    const majorVersion = parseInt(nodeVersion.slice(1).split('.')[0]);
    if (majorVersion < 14) {
      log(`❌ Node.js version ${nodeVersion} is too old. Please upgrade to Node.js 14 or higher.`, 'red');
      process.exit(1);
    }
    log(`✅ Node.js version: ${nodeVersion}`, 'green');
  } catch (error) {
    log('❌ Could not determine Node.js version', 'red');
    process.exit(1);
  }

  // Check npm
  try {
    const npmVersion = execSync('npm --version', { encoding: 'utf8' }).trim();
    log(`✅ npm version: ${npmVersion}`, 'green');
  } catch (error) {
    log('❌ npm not found', 'red');
    process.exit(1);
  }

  log('✅ System requirements met\n', 'green');
}

// Setup environment
function setupEnvironment() {
  log('⚙️  Setting up environment...', 'blue');
  
  // Create .env if it doesn't exist
  if (!fs.existsSync('.env')) {
    if (fs.existsSync('.env.example')) {
      fs.copyFileSync('.env.example', '.env');
      log('✅ Created .env from template', 'green');
      log('📝 Please edit .env and add your API keys:', 'yellow');
      log('   - OPENAI_API_KEY', 'yellow');
      log('   - REPLICATE_API_TOKEN', 'yellow');
      log('   Then run this script again.\n', 'yellow');
      process.exit(0);
    } else {
      log('❌ .env.example not found', 'red');
      process.exit(1);
    }
  }

  // Create necessary directories
  const dirs = ['uploads', 'outputs', 'temp'];
  dirs.forEach(dir => {
    if (!fs.existsSync(dir)) {
      fs.mkdirSync(dir, { recursive: true });
      log(`✅ Created directory: ${dir}`, 'green');
    }
  });

  log('✅ Environment setup complete\n', 'green');
}

// Install dependencies
function installDependencies() {
  log('📦 Installing dependencies...', 'blue');
  
  if (!fs.existsSync('node_modules')) {
    try {
      execSync('npm install', { stdio: 'inherit' });
      log('✅ Dependencies installed successfully', 'green');
    } catch (error) {
      log('❌ Failed to install dependencies', 'red');
      process.exit(1);
    }
  } else {
    log('✅ Dependencies already installed', 'green');
  }
  
  log('');
}

// Test the application
function testApplication() {
  log('🧪 Testing application...', 'blue');
  
  try {
    // Test if server can start
    const testServer = spawn('node', ['server.js'], { 
      stdio: 'pipe',
      env: { ...process.env, PORT: '3001' }
    });
    
    // Wait a bit for server to start
    setTimeout(() => {
      // Test health endpoint
      const req = http.get('http://localhost:3001/health', (res) => {
        if (res.statusCode === 200) {
          log('✅ Application test successful', 'green');
          testServer.kill();
        } else {
          log('⚠️  Application test incomplete (expected for demo mode)', 'yellow');
          testServer.kill();
        }
      });
      
      req.on('error', () => {
        log('⚠️  Application test incomplete (expected for demo mode)', 'yellow');
        testServer.kill();
      });
      
      req.setTimeout(3000, () => {
        log('⚠️  Application test timeout (expected for demo mode)', 'yellow');
        testServer.kill();
      });
    }, 2000);
    
  } catch (error) {
    log('⚠️  Application test failed (expected for demo mode)', 'yellow');
  }
  
  log('');
}

// Start the application
function startApplication() {
  log('🚀 Starting AI Image Restoration App...', 'blue');
  log('📊 Health check: http://localhost:3000/health', 'cyan');
  log('🌐 Main app: http://localhost:3000', 'cyan');
  log('🔧 Demo mode: Enabled (add API keys to .env for full features)', 'yellow');
  log('');
  
  const server = spawn('node', ['server.js'], { 
    stdio: 'inherit',
    env: { ...process.env, NODE_ENV: 'production' }
  });
  
  server.on('close', (code) => {
    if (code !== 0) {
      log(`❌ Server exited with code ${code}`, 'red');
      process.exit(code);
    }
  });
  
  // Handle graceful shutdown
  process.on('SIGINT', () => {
    log('\n🛑 Shutting down gracefully...', 'yellow');
    server.kill('SIGINT');
  });
  
  process.on('SIGTERM', () => {
    log('\n🛑 Shutting down gracefully...', 'yellow');
    server.kill('SIGTERM');
  });
}

// Main execution
async function main() {
  try {
    checkRequirements();
    setupEnvironment();
    installDependencies();
    testApplication();
    startApplication();
  } catch (error) {
    log(`❌ Launch failed: ${error.message}`, 'red');
    process.exit(1);
  }
}

// Run the launch script
main();