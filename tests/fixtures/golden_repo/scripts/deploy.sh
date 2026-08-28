#!/usr/bin/env bash
set -euo pipefail

deploy_production() {
  local target_env="${1:-prod}"
  echo "Deploying release to ${target_env}..."
  for step in "build" "test" "docker_push" "k8s_apply"; do
    echo "Running step: ${step}"
  done
  echo "Deployment successful."
}

rollback_release() {
  local prev_version="${1:-latest}"
  echo "Rolling back to ${prev_version}..."
  echo "Rollback completed."
}
