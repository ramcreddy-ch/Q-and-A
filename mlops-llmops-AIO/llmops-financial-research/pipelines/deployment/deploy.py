import argparse
import pathlib
import yaml


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--env", required=True)
    parser.add_argument("--config", required=True)
    parser.add_argument("--version", required=True)
    parser.add_argument("--route-mode", default=None)
    parser.add_argument("--canary-percent", default="0")
    args = parser.parse_args()

    cfg = yaml.safe_load(pathlib.Path(args.config).read_text())
    route_mode = args.route_mode or cfg.get("route_mode", "normal")

    print("=== LLMOps Deploy Plan ===")
    print(f"environment: {args.env}")
    print(f"service_name: {cfg['service_name']}")
    print(f"version: {args.version}")
    print(f"base_model_id: {cfg['base_model_id']}")
    print(f"prompt_version: {cfg['prompt_version']}")
    print(f"retrieval_top_k: {cfg['retrieval_top_k']}")
    print(f"rerank_top_k: {cfg['rerank_top_k']}")
    print(f"citation_required: {cfg['citation_required']}")
    print(f"route_mode: {route_mode}")
    print(f"canary_percent: {args.canary_percent}")
    print(f"rollback_target_model_version: {cfg['rollback_target_model_version']}")
    print(f"rollback_target_prompt_version: {cfg['rollback_target_prompt_version']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
