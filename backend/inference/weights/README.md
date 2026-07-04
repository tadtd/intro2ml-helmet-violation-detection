# Model Weights Storage

This folder holds the ONNX model files used by the inference microservice.

## Download Weights

You can obtain the trained ONNX models from Hugging Face:

👉 **[Hugging Face Model Repository](https://huggingface.co/dtdat1234/helmet-violation-detection-models)**

Download the following files and place them in this folder:

* `yolo_best.onnx`
* `rtdetr_best.onnx`
* `fasterrcnn_best.onnx`

## Verification

Ensure the filenames match exactly. When `USE_STUB_INFERENCE=false` is set in the configuration, the system loads these weights dynamically depending on the model selector chosen by the operator in the dashboard.
