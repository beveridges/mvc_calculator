#!/bin/bash
set -e

echo "======================================"
echo "  🔧 FULL WSL MVC Calculator REBUILD"
echo "======================================"

echo "📦 Updating Ubuntu..."
sudo apt update
sudo apt upgrade -y

echo "📦 Installing core tools..."
sudo apt install -y \
    curl wget git unzip \
    build-essential \
    libxkbcommon-x11-0 \
    libxcb-xinerama0 \
    libxcb-util1 \
    libxcb-cursor0 \
    libxcb-keysyms1 \
    libglu1-mesa

echo "📥 Downloading Miniconda..."
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O miniconda.sh

echo "📦 Installing Miniconda..."
bash miniconda.sh -b -p $HOME/miniconda3
rm miniconda.sh

echo "🔁 Initializing Conda..."
eval "$($HOME/miniconda3/bin/conda shell.bash hook)"

echo "📁 Cloning MVC_Calculator repo..."
cd ~
git clone https://github.com/beveridges/mvc_calculator.git MVC_Calculator

echo "📄 Copying environment file..."
cp MVC_Calculator/mvccalculator-linux.yml ~/mvccalculator-linux.yml

echo "🐍 Creating Conda environment..."
conda env create -f ~/mvccalculator-linux.yml

echo "🔐 Activating environment..."
conda activate mvccalculator

echo "🧪 Testing key libraries..."
python - <<EOF
import PyQt5, numpy, matplotlib, pandas
print('✅ PyQt5 OK')
print('✅ NumPy OK')
print('✅ Matplotlib OK')
print('✅ pandas OK')
EOF

echo "🚀 Running MVC Calculator test..."
python ~/MVC_Calculator/main.py || true

echo ""
echo "======================================"
echo "  🎉 WSL MVC Calculator Rebuild Done!"
echo "======================================"
echo "You can now run:"
echo "   conda activate mvccalculator"
echo "   python ~/MVC_Calculator/main.py"
