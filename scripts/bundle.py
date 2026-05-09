#!/usr/bin/env python3
"""
Bundles openapi/*.yaml files into a single openapi.yaml.

Usage:
    python3 scripts/bundle.py

Reads:
  openapi/base.yaml        — header, tags, security, shared schemas, securitySchemes
  openapi/<feature>.yaml   — paths + components.schemas per feature (in FEATURE_ORDER)

Writes:
  openapi.yaml             — merged spec (committed, served by Scalar)
"""

import yaml
import os
import sys
import copy

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(SCRIPT_DIR)
OPENAPI_DIR = os.path.join(ROOT_DIR, "openapi")
OUTPUT_FILE = os.path.join(ROOT_DIR, "openapi.yaml")

FEATURE_ORDER = [
    "auth",
    "business",
    "ai-commerce",
    "inventory-products",
    "inventory-pricing",
    "inventory-stock",
    "orders",
    "customer",
    "pricing",
    "crm",
    "compute",
    "gathering",
    "education",
    "workforce",
    "marketing",
    "notifications",
    "support",
    "finance",
    "media-social",
    "platform-admin",
]


def load_yaml(path):
    with open(path, "r") as f:
        return yaml.safe_load(f) or {}


def bundle():
    base_path = os.path.join(OPENAPI_DIR, "base.yaml")
    if not os.path.exists(base_path):
        print(f"ERROR: {base_path} not found", file=sys.stderr)
        sys.exit(1)

    spec = load_yaml(base_path)
    spec.setdefault("paths", {})
    spec.setdefault("components", {})
    spec["components"].setdefault("schemas", {})
    spec["components"].setdefault("securitySchemes", spec.get("components", {}).get("securitySchemes", {}))

    for feature in FEATURE_ORDER:
        feature_path = os.path.join(OPENAPI_DIR, f"{feature}.yaml")
        if not os.path.exists(feature_path):
            continue

        data = load_yaml(feature_path)

        # Merge paths
        for path, item in (data.get("paths") or {}).items():
            if path in spec["paths"]:
                print(f"WARNING: duplicate path {path} in {feature}.yaml", file=sys.stderr)
            spec["paths"][path] = item

        # Merge schemas
        for name, schema in (data.get("components", {}).get("schemas") or {}).items():
            if name in spec["components"]["schemas"]:
                print(f"WARNING: duplicate schema {name} in {feature}.yaml", file=sys.stderr)
            spec["components"]["schemas"][name] = schema

    with open(OUTPUT_FILE, "w") as f:
        yaml.dump(
            spec,
            f,
            default_flow_style=False,
            allow_unicode=True,
            sort_keys=False,
            width=120,
        )

    path_count = len(spec["paths"])
    schema_count = len(spec["components"]["schemas"])
    print(f"Bundled: {path_count} paths, {schema_count} schemas → {OUTPUT_FILE}")


if __name__ == "__main__":
    bundle()
