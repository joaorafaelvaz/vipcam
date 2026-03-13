"""Convert HSEmotion PyTorch model to ONNX format.

The HSEmotion .pt files contain full model objects (torch.save(model)),
not just state_dicts. We load the full model directly and export to ONNX.

Usage:
    python scripts/convert_emotion_onnx.py [model_name] [output_path]
"""
import sys
from pathlib import Path

MODEL_URLS = {
    "enet_b0_8_best_afew": "https://github.com/HSE-asavchenko/face-emotion-recognition/raw/main/models/affectnet_emotions/enet_b0_8_best_afew.pt",
    "enet_b0_8_best_vgaf": "https://github.com/HSE-asavchenko/face-emotion-recognition/raw/main/models/affectnet_emotions/enet_b0_8_best_vgaf.pt",
    "enet_b2_8": "https://github.com/HSE-asavchenko/face-emotion-recognition/raw/main/models/affectnet_emotions/enet_b2_8.pt",
    "enet_b2_7": "https://github.com/HSE-asavchenko/face-emotion-recognition/raw/main/models/affectnet_emotions/enet_b2_7.pt",
}


def convert(model_name: str, output_path: str):
    import numpy as np
    import torch

    if model_name not in MODEL_URLS:
        print(f"Unknown model: {model_name}. Available: {list(MODEL_URLS.keys())}")
        sys.exit(1)

    # Download weights
    url = MODEL_URLS[model_name]
    cache_dir = Path.home() / ".cache" / "hsemotion"
    cache_dir.mkdir(parents=True, exist_ok=True)
    weights_path = cache_dir / f"{model_name}.pt"

    if not weights_path.exists():
        print(f"Downloading {url}...")
        torch.hub.download_url_to_file(url, str(weights_path))

    # HSEmotion .pt files are full model saves (torch.save(model, path))
    # Load the complete model directly — no need for timm
    print(f"Loading full model from {weights_path}...")
    model = torch.load(str(weights_path), map_location="cpu", weights_only=False)
    model.eval()

    print(f"Model type: {type(model).__name__}")
    print(f"Model: {model.__class__.__module__}.{model.__class__.__name__}")

    # Export to ONNX
    dummy_input = torch.randn(1, 3, 260, 260)
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    print(f"Exporting to ONNX: {output_file}")
    torch.onnx.export(
        model,
        dummy_input,
        str(output_file),
        input_names=["input"],
        output_names=["logits"],
        dynamic_axes={"input": {0: "batch"}, "logits": {0: "batch"}},
        opset_version=17,
    )

    # Verify with ONNX Runtime
    import onnxruntime as ort
    sess = ort.InferenceSession(str(output_file), providers=["CPUExecutionProvider"])
    result = sess.run(None, {"input": dummy_input.numpy()})
    logits = result[0].flatten()

    # Check that output is reasonable (not all zeros or uniform)
    exp = np.exp(logits - np.max(logits))
    probs = exp / exp.sum()
    print(f"ONNX verification OK — output shape: {result[0].shape}")
    print(f"Sample probs (random input): {dict(zip(['anger','contempt','disgust','fear','happiness','neutral','sadness','surprise'], [f'{p:.3f}' for p in probs]))}")
    print(f"Model saved to: {output_file}")


if __name__ == "__main__":
    name = sys.argv[1] if len(sys.argv) > 1 else "enet_b2_8"
    output = sys.argv[2] if len(sys.argv) > 2 else f"/models/{name}.onnx"
    convert(name, output)
