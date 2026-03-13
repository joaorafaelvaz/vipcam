"""Convert HSEmotion PyTorch model to ONNX format.

This script runs in a clean Python environment (no CUDA needed).
It downloads the HSEmotion weights and exports to ONNX using timm.

Usage:
    python scripts/convert_emotion_onnx.py [model_name] [output_path]

Example:
    python scripts/convert_emotion_onnx.py enet_b2_8 /models/enet_b2_8.onnx
"""
import sys
from pathlib import Path

MODEL_CONFIG = {
    "enet_b0_8_best_afew": ("tf_efficientnet_b0", 8),
    "enet_b0_8_best_vgaf": ("tf_efficientnet_b0", 8),
    "enet_b2_8": ("tf_efficientnet_b2", 8),
    "enet_b2_7": ("tf_efficientnet_b2", 7),
}

MODEL_URLS = {
    "enet_b0_8_best_afew": "https://github.com/HSE-asavchenko/face-emotion-recognition/raw/main/models/affectnet_emotions/enet_b0_8_best_afew.pt",
    "enet_b0_8_best_vgaf": "https://github.com/HSE-asavchenko/face-emotion-recognition/raw/main/models/affectnet_emotions/enet_b0_8_best_vgaf.pt",
    "enet_b2_8": "https://github.com/HSE-asavchenko/face-emotion-recognition/raw/main/models/affectnet_emotions/enet_b2_8.pt",
    "enet_b2_7": "https://github.com/HSE-asavchenko/face-emotion-recognition/raw/main/models/affectnet_emotions/enet_b2_7.pt",
}


def convert(model_name: str, output_path: str):
    import timm
    import torch

    if model_name not in MODEL_CONFIG:
        print(f"Unknown model: {model_name}. Available: {list(MODEL_CONFIG.keys())}")
        sys.exit(1)

    backbone, num_classes = MODEL_CONFIG[model_name]

    # Download weights
    url = MODEL_URLS[model_name]
    cache_dir = Path.home() / ".cache" / "hsemotion"
    cache_dir.mkdir(parents=True, exist_ok=True)
    weights_path = cache_dir / f"{model_name}.pt"

    if not weights_path.exists():
        print(f"Downloading {url}...")
        torch.hub.download_url_to_file(url, str(weights_path))

    print(f"Loading {backbone} with {num_classes} classes...")
    model = timm.create_model(backbone, pretrained=False, num_classes=num_classes)

    state_dict = torch.load(str(weights_path), map_location="cpu", weights_only=False)
    if isinstance(state_dict, dict) and "state_dict" in state_dict:
        state_dict = state_dict["state_dict"]
    elif not isinstance(state_dict, dict) and hasattr(state_dict, "state_dict"):
        state_dict = state_dict.state_dict()

    model.load_state_dict(state_dict, strict=False)
    model.eval()

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

    # Verify
    import onnxruntime as ort
    sess = ort.InferenceSession(str(output_file), providers=["CPUExecutionProvider"])
    result = sess.run(None, {"input": dummy_input.numpy()})
    print(f"ONNX verification OK — output shape: {result[0].shape}")
    print(f"Model saved to: {output_file}")


if __name__ == "__main__":
    name = sys.argv[1] if len(sys.argv) > 1 else "enet_b2_8"
    output = sys.argv[2] if len(sys.argv) > 2 else f"/models/{name}.onnx"
    convert(name, output)
