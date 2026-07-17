#!/usr/bin/env python3
"""
Expose Ollama models to LM Studio by symlinking its model files.
NOTE: On Windows, you need to run this script with administrator privileges.
"""

import json
import os
from pathlib import Path


# The path where Ollama stores its models.
OLLAMA_MODEL_DIR = Path( "C:/Users/gsvas/.ollama/models/"
)

# The path where LM Studio stores its models.
LM_STUDIO_MODEL_DIR = Path("C:/Users/gsvas/.lmstudio/models")


def get_model_gguf_path(ollama_model_tag_manifest_path):
    """Parse Ollama's model tag manifest to extract its GGUF file path."""
    with open(ollama_model_tag_manifest_path) as mf:
        manifest = json.load(mf)

    model_layer = next(
        layer
        for layer in manifest["layers"]
        if layer["mediaType"] == "application/vnd.ollama.image.model"
    )
    gguf_hash = model_layer["digest"]
    gguf_filename = gguf_hash.replace(":", "-")
    gguf_path = OLLAMA_MODEL_DIR / "blobs" / gguf_filename

    return gguf_path


def main():
    ollama_library_path = OLLAMA_MODEL_DIR / "manifests" / "registry.ollama.ai" / "library"
    lmstudio_ollama_root_path = LM_STUDIO_MODEL_DIR / "ollama"

    print(f"Ensuring the target directory for LM Studio models exists: {lmstudio_ollama_root_path}")
    lmstudio_ollama_root_path.mkdir(parents=True, exist_ok=True)

    # Iterate through Ollama models.
    print(f"Scanning the Ollama model directory: {OLLAMA_MODEL_DIR}")
    for model_family_path in ollama_library_path.iterdir():
        # We're looking for subdirectories. Skip if it's a file.
        if not model_family_path.is_dir():
            continue

        model_family_name = model_family_path.name

        # Scan the model directory for tags.
        for model_tag_manifest_path in model_family_path.iterdir():
            if not model_tag_manifest_path.is_file():
                continue

            # If it's a tag manifest, extract the GGUF path.
            model_tag_name = model_tag_manifest_path.name
            try:
                gguf_path = get_model_gguf_path(model_tag_manifest_path)
                print(
                    f"Discovered Ollama model '{model_family_name}:{model_tag_name}' "
                    f"with GGUF at {gguf_path}"
                )
            except Exception:
                print(f"WARNING: Failed to parse the Ollama tag manifest at {model_tag_manifest_path}.")
                continue

            # Create a model in LM Studio, symlinking it to Ollama's GGUF file.
            lmstudio_model_dir_path = lmstudio_ollama_root_path / f"{model_family_name}-{model_tag_name}"
            print(f"Creating LM Studio model directory: {lmstudio_model_dir_path}")
            lmstudio_model_dir_path.mkdir(parents=True, exist_ok=True)

            symlink_path = lmstudio_model_dir_path / f"{model_family_name}-{model_tag_name}.gguf"
            if symlink_path.is_symlink():
                print(f"Skipping {model_family_name}:{model_tag_name}: already linked")
            else:
                print(f"Linking {model_family_name}:{model_tag_name} at {symlink_path}")
                os.symlink(gguf_path, symlink_path)


if __name__ == "__main__":
    main()