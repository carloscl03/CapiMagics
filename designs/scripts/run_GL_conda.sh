#!/bin/bash
set -e  # Exit on error

# === Step 1: Basic environment setup ===
unset PYTHONPATH
unset LD_LIBRARY_PATH

# Define base directory for conda installation
BASE_DIR="$HOME/conda-env"
MINICONDA_DIR="$BASE_DIR/miniconda3"
ENV_NAME="GLdev"

export PATH="$MINICONDA_DIR/bin:$PATH"

# === Step 2: Check if environment is already set up ===
if [ -d "$MINICONDA_DIR/envs/$ENV_NAME" ]; then
    echo "Existing $ENV_NAME environment detected. Skipping setup."
else
    echo "$ENV_NAME environment not found. Starting setup..."

    # Create base directory
    mkdir -p "$BASE_DIR"
    cd "$BASE_DIR"

    # Download and install Miniforge
    wget -O miniforge.sh "https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-$(uname)-$(uname -m).sh"
    bash miniforge.sh -b -p "$MINICONDA_DIR"

    # Source Conda
    source "$MINICONDA_DIR/etc/profile.d/conda.sh"

    # Create the environment
    conda create -y -n "$ENV_NAME" python=3.10

    # Activate the environment
    conda activate "$ENV_NAME"

    # Install packages
    conda install -y jupyter jupyterlab notebook nbclassic \
        jupyter_server_ydoc jupyter_server_fileid \
        numpy=1.24 matplotlib pip \
        -c litex-hub -c conda-forge

    # Register the kernel
    python -m ipykernel install --user --name="$ENV_NAME"

    # Pip packages
    #modified to pull latest version of glayout, but using the conda enviroment
    #seems that conda-forge provides pre-compiled aarch64 binaries for both gdstk and klayout, skipping compilation entirely.
    #easier way, pre-clone the repository of glayout and modify the code
    #by alejandro juarez lora

    # pip install glayout
    if [ -d /foss/designs/${GLAYOUT_PATH}/${GLAYOUT_FOLDER} ]; then
        echo "gLayout folder found under /foss/designs/${GLAYOUT_PATH}/${GLAYOUT_FOLDER}"
        pip install -e /foss/designs/${GLAYOUT_PATH}/${GLAYOUT_FOLDER}
    else
        echo "gLayout repo not found, please make sure you have cloned it under designs/${GLAYOUT_PATH} foler"
    fi 

    pip install "klayout>=0.28,<0.29"
    pip install svgutils

    echo "Setup complete!"
fi

# === Step 3: Launch Jupyter ===
echo "Launching Jupyter Lab..."
source "$MINICONDA_DIR/etc/profile.d/conda.sh"
conda activate "$ENV_NAME"
jupyter lab --ip=0.0.0.0 --no-browser --port=8888

