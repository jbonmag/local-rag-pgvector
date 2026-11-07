import argparse
from pathlib import Path

from dotenv import load_dotenv


def main() -> None:
    load_dotenv()
    parser = argparse.ArgumentParser(description="Download Hugging Face models into ./models.")
    parser.add_argument("--repo-id", required=True, help="Hugging Face repository id.")
    parser.add_argument("--target", required=True, help="Local target file or directory.")
    parser.add_argument("--filename", help="Single filename to download, for example a GGUF file.")
    parser.add_argument("--all", action="store_true",
                        help="Download every file, including ONNX/OpenVINO/TF copies of the weights.")
    args = parser.parse_args()

    try:
        from huggingface_hub import hf_hub_download, snapshot_download
    except ImportError as exc:
        raise SystemExit(
            "huggingface-hub is not installed. Run: pip install -e \".[local-llm]\""
        ) from exc

    target = Path(args.target)
    if args.filename:
        target.parent.mkdir(parents=True, exist_ok=True)
        downloaded = hf_hub_download(
            repo_id=args.repo_id,
            filename=args.filename,
            local_dir=str(target.parent),
            local_dir_use_symlinks=False,
        )
        downloaded_path = Path(downloaded)
        if downloaded_path.resolve() != target.resolve():
            downloaded_path.replace(target)
        print(f"Downloaded {args.repo_id}/{args.filename} to {target}")
    else:
        target.mkdir(parents=True, exist_ok=True)
        ignore = None if args.all else redundant_weight_patterns(args.repo_id)
        snapshot_download(
            repo_id=args.repo_id,
            local_dir=str(target),
            local_dir_use_symlinks=False,
            ignore_patterns=ignore,
        )
        print(f"Downloaded {args.repo_id} to {target}")
        if ignore:
            print(f"Skipped alternative weight formats: {', '.join(ignore)} (use --all to keep them)")


def redundant_weight_patterns(repo_id: str) -> list[str]:
    """Copies of the same weights that sentence-transformers and transformers never load.

    Many repositories ship the model several times (ONNX, OpenVINO, TensorFlow, Flax, and
    pytorch_model.bin next to model.safetensors). For intfloat/multilingual-e5-small that is
    2.2 GB instead of about 470 MB.
    """
    from huggingface_hub import HfApi

    patterns = ["onnx/*", "openvino/*", "*.onnx", "tf_model.h5", "flax_model.msgpack", "rust_model.ot"]
    files = HfApi().list_repo_files(repo_id)
    if any(name.endswith(".safetensors") for name in files):
        patterns += ["pytorch_model*.bin"]
    return patterns


if __name__ == "__main__":
    main()
