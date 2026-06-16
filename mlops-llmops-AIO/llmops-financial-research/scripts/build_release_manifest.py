import argparse
import json
import pathlib
import yaml


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--version", required=True)
    parser.add_argument("--output", default="release-manifest.json")
    args = parser.parse_args()

    cfg = yaml.safe_load(pathlib.Path(args.config).read_text())
    manifest = {
        "service_name": cfg["service_name"],
        "environment": cfg["environment"],
        "business_version": args.version,
        "base_model_id": cfg["base_model_id"],
        "prompt_version": cfg["prompt_version"],
        "embedding_model_version": cfg["embedding_model_version"],
        "retrieval_top_k": cfg["retrieval_top_k"],
        "rerank_top_k": cfg["rerank_top_k"],
        "rollback_target_prompt_version": cfg["rollback_target_prompt_version"],
        "rollback_target_model_version": cfg["rollback_target_model_version"],
    }
    pathlib.Path(args.output).write_text(json.dumps(manifest, indent=2))
    print(f"wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
