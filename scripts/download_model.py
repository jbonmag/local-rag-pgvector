import argparse
from pathlib import Path

from dotenv import load_dotenv


def main() -> None:
    load_dotenv()
    parser = argparse.ArgumentParser(description="Download Hugging Face models into ./models.")
    parser.add_argument("--repo-id", required=True, help="Hugging Face repository id.")
    parser.add_argument("--target", required=True, help="Local target file or directory.")
    parser.add_argument("--filename", help="Single filename to download, for example a GGUF file.")
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
        snapshot_download(
            repo_id=args.repo_id,
            local_dir=str(target),
            local_dir_use_symlinks=False,
        )
        print(f"Downloaded {args.repo_id} to {target}")


if __name__ == "__main__":
    main()
