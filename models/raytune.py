"""Ray Tune hyperparameter search with train/val/test workflow.

Phase 1: Tune on validation (test never used).
Phase 2: Train from scratch with best hyperparameters, then evaluate on test.

Run on Kaggle:
    uv run python models/raytune.py --model fasterrcnn --num-samples 10
    uv run python models/raytune.py --model yolo --num-samples 10
    uv run python models/raytune.py --model rtdetr --num-samples 10
"""

from __future__ import annotations

import argparse
import copy
import json
import sys
from argparse import Namespace
from pathlib import Path

import ray
from ray import train as ray_train
from ray import tune
from ray.tune.schedulers import ASHAScheduler

sys.path.insert(0, str(Path(__file__).resolve().parent))

from train_fasterrcnn import parse_args as parse_fasterrcnn_args
from train_fasterrcnn import run as run_fasterrcnn
from train_rtdetr import parse_args as parse_rtdetr_args
from train_rtdetr import run as run_rtdetr
from train_yolo import parse_args as parse_yolo_args
from train_yolo import run as run_yolo
from utils import get_paths

MODELS = ("fasterrcnn", "yolo", "rtdetr")
HYPERPARAM_KEYS = {
    "fasterrcnn": ("lr", "batch_size", "weight_decay", "lr_step", "lr_gamma"),
    "yolo": ("lr0", "batch", "lrf", "weight_decay"),
    "rtdetr": ("lr0", "batch", "lrf", "weight_decay"),
}
FINAL_RESULTS = {
    "fasterrcnn": "fasterrcnn_final_results.json",
    "yolo": "yolo_final_results.json",
    "rtdetr": "rtdetr_final_results.json",
}


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Ray Tune: tune on val → train with best config → evaluate on test.",
    )
    parser.add_argument(
        "--model",
        required=True,
        choices=MODELS,
        help="Detector to tune and retrain.",
    )
    parser.add_argument("--num-samples", type=int, default=10, help="Number of Ray Tune trials.")
    parser.add_argument("--max-concurrent", type=int, default=1, help="Concurrent trials.")
    parser.add_argument("--epochs", type=int, default=50, help="Epochs for final retrain.")
    parser.add_argument(
        "--tune-epochs",
        type=int,
        default=None,
        help="Epochs per tune trial (defaults to --epochs).",
    )
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument(
        "--storage-path",
        type=str,
        default=None,
        help="Ray Tune storage directory (default: output/raytune/{model}).",
    )
    parser.add_argument(
        "--skip-retrain",
        action="store_true",
        help="Only run Phase 1 (tune on val); skip final train and test eval.",
    )
    return parser.parse_args(argv)


def default_train_args(model: str, seed: int, epochs: int) -> Namespace:
    if model == "fasterrcnn":
        return parse_fasterrcnn_args(["--seed", str(seed), "--epochs", str(epochs)])
    if model == "yolo":
        return parse_yolo_args(["--seed", str(seed), "--epochs", str(epochs)])
    return parse_rtdetr_args(["--seed", str(seed), "--epochs", str(epochs)])


def apply_config(model: str, base: Namespace, config: dict) -> Namespace:
    args = copy.copy(base)
    if model == "fasterrcnn":
        args.lr = config["lr"]
        args.batch_size = int(config["batch_size"])
        args.weight_decay = config["weight_decay"]
        args.lr_step = int(config["lr_step"])
        args.lr_gamma = config["lr_gamma"]
    elif model in ("yolo", "rtdetr"):
        args.lr0 = config["lr0"]
        args.batch = int(config["batch"])
        args.lrf = config["lrf"]
        args.weight_decay = config["weight_decay"]
    return args


def search_space(model: str) -> dict:
    if model == "fasterrcnn":
        return {
            "lr": tune.loguniform(1e-4, 1e-2),
            "batch_size": tune.choice([2, 4, 8]),
            "weight_decay": tune.loguniform(1e-5, 1e-3),
            "lr_step": tune.choice([5, 10, 15]),
            "lr_gamma": tune.choice([0.1, 0.5]),
        }
    if model == "yolo":
        return {
            "lr0": tune.loguniform(1e-4, 1e-2),
            "batch": tune.choice([8, 16, 32]),
            "lrf": tune.uniform(0.01, 0.2),
            "weight_decay": tune.loguniform(1e-5, 1e-3),
        }
    return {
        "lr0": tune.loguniform(1e-5, 1e-3),
        "batch": tune.choice([4, 8, 16]),
        "lrf": tune.uniform(0.01, 0.2),
        "weight_decay": tune.loguniform(1e-5, 1e-3),
    }


def config_to_dict(model: str, config: dict) -> dict:
    keys = HYPERPARAM_KEYS[model]
    return {k: config[k] for k in keys}


def make_trainable(model: str, seed: int, tune_epochs: int):
    base = default_train_args(model, seed, tune_epochs)

    def trainable(config: dict) -> None:
        args = apply_config(model, base, config)
        trial_id = ray_train.get_context().get_trial_id()

        if model == "fasterrcnn":

            def on_epoch_end(epoch: int, *, val_loss: float) -> None:
                ray_train.report({
                    "val_loss": val_loss,
                    "training_iteration": epoch,
                })

            metrics = run_fasterrcnn(
                args,
                on_epoch_end=on_epoch_end,
                eval_splits=("val",),
                save_checkpoint=False,
            )
        elif model == "yolo":
            metrics = run_yolo(
                args,
                eval_splits=("val",),
                save_checkpoint=False,
                run_name=f"yolo_tune_{trial_id}",
            )
        else:
            metrics = run_rtdetr(
                args,
                eval_splits=("val",),
                save_checkpoint=False,
                run_name=f"rtdetr_tune_{trial_id}",
            )

        ray_train.report({
            "val_mAP50_95": metrics["val_mAP50_95"],
            "val_mAP50": metrics["val_mAP50"],
            "training_iteration": tune_epochs,
        })

    return trainable


def run_tune_phase(args: argparse.Namespace, storage_path: Path) -> dict:
    tune_epochs = args.tune_epochs if args.tune_epochs is not None else args.epochs
    trainable = make_trainable(args.model, args.seed, tune_epochs)

    scheduler = ASHAScheduler(
        max_t=tune_epochs,
        grace_period=1,
        reduction_factor=2,
    )

    tuner = tune.Tuner(
        trainable,
        param_space=search_space(args.model),
        tune_config=tune.TuneConfig(
            metric="val_mAP50_95",
            mode="max",
            num_samples=args.num_samples,
            max_concurrent_trials=args.max_concurrent,
            scheduler=scheduler,
        ),
        run_config=tune.RunConfig(
            storage_path=str(storage_path / "ray_trials"),
            name=f"{args.model}_tune",
        ),
    )

    print(f"\n=== Phase 1: Ray Tune on validation ({args.num_samples} trials) ===")
    result = tuner.fit()
    best = result.get_best_result(metric="val_mAP50_95", mode="max")

    best_config = config_to_dict(args.model, best.config)
    best_config["val_mAP50_95"] = best.metrics["val_mAP50_95"]
    if "val_mAP50" in best.metrics:
        best_config["val_mAP50"] = best.metrics["val_mAP50"]

    config_path = storage_path / "best_config.json"
    config_path.write_text(json.dumps(best_config, indent=2))
    print(f"\nBest config (val mAP@0.5:0.95 = {best_config['val_mAP50_95']:.4f}):")
    print(json.dumps(best_config, indent=2))
    print(f"Saved → {config_path}")
    return best_config


def run_final_train_phase(args: argparse.Namespace, best_config: dict) -> dict:
    """Train from scratch with best hyperparams; test eval runs at end of training."""
    print(f"\n=== Phase 2: Final train + test eval ({args.epochs} epochs) ===")
    base = default_train_args(args.model, args.seed, args.epochs)
    train_args = apply_config(args.model, base, best_config)

    if args.model == "fasterrcnn":
        return run_fasterrcnn(train_args, eval_splits=("test",), save_checkpoint=True)
    if args.model == "yolo":
        return run_yolo(
            train_args,
            eval_splits=("test",),
            save_checkpoint=True,
            run_name="yolo_final",
        )
    return run_rtdetr(
        train_args,
        eval_splits=("test",),
        save_checkpoint=True,
        run_name="rtdetr_final",
    )


def main() -> None:
    args = parse_args()
    _, out_root = get_paths()
    storage_path = (
        Path(args.storage_path)
        if args.storage_path
        else out_root / "raytune" / args.model
    )
    storage_path.mkdir(parents=True, exist_ok=True)

    ray.init(ignore_reinit_error=True, include_dashboard=False)

    best_config = run_tune_phase(args, storage_path)

    if args.skip_retrain:
        print("\n--skip-retrain set; stopping after Phase 1.")
        return

    metrics = run_final_train_phase(args, best_config)

    hyperparams = {k: best_config[k] for k in HYPERPARAM_KEYS[args.model]}
    final_results = {
        "best_config": hyperparams,
        "test": {
            "mAP50": metrics["test_mAP50"],
            "mAP50_95": metrics["test_mAP50_95"],
            "AR100": metrics["test"].get("AR100") if metrics.get("test") else None,
        },
        "fps": metrics["fps"],
        "tune_val_mAP50_95": best_config.get("val_mAP50_95"),
    }

    out_json = out_root / FINAL_RESULTS[args.model]
    out_json.write_text(json.dumps(final_results, indent=2))

    print(f"\nTest  mAP@0.5:      {metrics['test_mAP50']:.4f}")
    print(f"Test  mAP@0.5:0.95: {metrics['test_mAP50_95']:.4f}")
    print(f"FPS:                {metrics['fps']:.1f}")
    print(f"\nFinal results → {out_json}")


if __name__ == "__main__":
    main()
