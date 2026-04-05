# intro2ml-helmet-violation-detection

Pipeline thu thap video giao thong, tach frame, loc frame theo huong uu tien anh co kha nang "khong doi mu bao hiem", va chuan bi bo anh train/val/test cho annotate.

## 1) Cau truc thu muc

```
traffic_data_pipeline/
|- bot_collect_video_links.py
|- download_videos.py
|- extract_frames.py
|- filter_frames.py
|- prepare_dataset_for_annotation.py
|- pseudo_label_with_grounding_dino.py
|- data/
|  |- videos.csv
|  |- videos/
|  |- frames_raw/
|  |- frames_clean/
|  |- frames_metadata.csv
|- dataset/
|  |- images/
|  |  |- train/
|  |  |- val/
|  |  |- test/
|  |- images_metadata.csv
```

## 2) Cai dat bang uv

Neu may da co `uv`, chay theo thu tu sau:

```bash
uv venv --python 3.13
source .venv/bin/activate
uv pip install playwright yt-dlp opencv-python pandas
uv run playwright install chromium
```

Neu muon dung pseudo-labeling bang Grounding DINO, cai them:

```bash
uv pip install torch transformers pillow
```

Ghi chu:
- Can chay `playwright install` (hoac `playwright install chromium`) de tai browser binaries.
- Neu bo qua buoc nay, script crawl se bao loi `Executable doesn't exist`.

## 3) Thu tu chay pipeline

### Buoc 1: Crawl link video YouTube

```bash
uv run bot_collect_video_links.py
```

Ket qua:
- Ghi danh sach link vao `data/videos.csv`.
- Da uu tien query lien quan vi pham "khong doi mu".

### Buoc 2: Tai video

```bash
uv run download_videos.py
```

Ket qua:
- Tai video vao thu muc `data/videos/`.
- Cap nhat cot `download_status`, `local_video_path` trong `data/videos.csv`.

### Buoc 3: Tach frame

```bash
uv run extract_frames.py
```

Ket qua:
- Luu frame goc vao `data/frames_raw/`.
- Luu metadata vao `data/frames_metadata.csv`.

### Buoc 4: Loc frame clean (uu tien no-helmet)

```bash
uv run filter_frames.py
```

Ket qua:
- Luu frame clean vao `data/frames_clean/` voi ten on dinh, vi du: `video2f6ca9d1_t000120.jpg`.
- Cap nhat `is_kept`, `clean_frame_path`, `filter_reason`, `no_helmet_score`, `stable_file_name`, `source_video`, `timestamp`, `image_id` trong `data/frames_metadata.csv`.

### Buoc 5: Chuan bi dataset de annotate

```bash
uv run prepare_dataset_for_annotation.py
```

Ket qua:
- Copy anh tu `data/frames_clean/` sang:
	- `dataset/images/train/`
	- `dataset/images/val/`
	- `dataset/images/test/`
- Sinh `dataset/images_metadata.csv` voi cac cot chinh:
	- `image_id`, `file_name`, `width`, `height`, `source_video`, `timestamp`, `split`

## 4) Co che uu tien anh "khong doi mu"

Script `filter_frames.py` dang loc theo 2 tang:

1. Loc chat luong: bo anh mo, qua toi, qua sang, frame trung gan nhau.
2. Cham diem no-helmet heuristic: uu tien frame co diem `no_helmet_score` cao (dua tren vung dau/than tren, ti le mau da, dac trung texture), sau do chi giu top frame moi video.

Ngoai ra script se gan ten file on dinh theo quy tac:
- `{stable_video_id}_t{timestamp_ms}.jpg`
- Vi du: `video2f6ca9d1_t000120.jpg`

`stable_video_id` duoc tao tu hash cua `video_url` (hoac `video_path` fallback), nen on dinh qua cac lan chay va khong bi doi khi them video moi.

Ban co the tinh chinh cac tham so trong `filter_frames.py`:
- `TOP_SCORE_KEEP_RATIO`
- `MIN_KEEP_PER_VIDEO`
- `MAX_KEEP_PER_VIDEO`
- `MIN_BLUR_SCORE`
- `SIMILARITY_THRESHOLD`

## 5) Chay lai toan bo nhanh

```bash
uv run bot_collect_video_links.py && \
uv run download_videos.py && \
uv run extract_frames.py && \
uv run filter_frames.py && \
uv run prepare_dataset_for_annotation.py
```

## 6) Kiem tra nhanh ket qua loc

```bash
uv run python - <<'PY'
import pandas as pd
df = pd.read_csv('data/frames_metadata.csv')
print('Total frames:', len(df))
print('Kept frames:', int(df['is_kept'].sum()))
if 'no_helmet_score' in df.columns:
	print(df[df['is_kept'] == 1]['no_helmet_score'].describe())
print(df['filter_reason'].value_counts().head(10))
PY
```

## 7) Luu y ve COCO annotations

COCO can bbox, trong khi cac script tren chi chuan bi anh + metadata. Vi vay can tach 2 phan:

1. Phan chuan bi anh:
- `extract_frames.py`
- `filter_frames.py`
- `prepare_dataset_for_annotation.py`

2. Phan annotations/COCO:
- Import `dataset/images/*` vao tool annotate.
- Gan nhan bbox cho cac class (vi du: `motorbike`, `helmet`, `no_helmet`).
- Export COCO truc tiep tu tool neu ho tro.

Chi can viet script convert sang COCO khi tool annotate cua ban khong export COCO san.

## 8) Loc thu cong sau khi script chay xong

Sau khi chay xong `filter_frames.py` va `prepare_dataset_for_annotation.py`, nen loc thu cong theo quy trinh nhanh sau:

1. Loc ung vien uu tien cao
```bash
uv run python - <<'PY'
import pandas as pd
df = pd.read_csv('data/frames_metadata.csv')
keep = df[df['is_kept'] == 1].copy()
keep = keep.sort_values('no_helmet_score', ascending=False)
keep[['stable_file_name', 'no_helmet_score', 'source_video', 'timestamp']].head(300).to_csv('data/manual_review_top300.csv', index=False, encoding='utf-8-sig')
print('Saved data/manual_review_top300.csv')
PY
```

2. Mo va ra soat thu cong
- Mo `data/manual_review_top300.csv` de uu tien review cac anh diem cao.
- Xoa cac anh sai/noise trong `dataset/images/*`.
- Danh dau nhom anh kho (che dau, blur nhe, nhieu nguoi) de annotate ky hon.

3. Dong bo lai metadata sau khi xoa tay
```bash
uv run python - <<'PY'
from pathlib import Path
import pandas as pd

meta = pd.read_csv('dataset/images_metadata.csv')
meta['exists'] = meta['image_path'].apply(lambda p: Path(p).exists())
clean = meta[meta['exists']].drop(columns=['exists']).copy().reset_index(drop=True)
clean['image_id'] = range(1, len(clean) + 1)
clean.to_csv('dataset/images_metadata.csv', index=False, encoding='utf-8-sig')
print('Updated dataset/images_metadata.csv:', len(clean), 'images')
PY
```

4. Kiem tra leakage theo video
- Script da chia split theo `stable_video_id` nen frame cung video se vao cung 1 split.
- De check nhanh:
```bash
uv run python - <<'PY'
import pandas as pd
df = pd.read_csv('dataset/images_metadata.csv')
print(df.groupby('source_video')['split'].nunique().value_counts().to_dict())
PY
```
- Ket qua tot nhat la tat ca source_video chi xuat hien 1 split.

## 9) Giam loc tay bang Grounding DINO pseudo-labeling

Script moi: pseudo_label_with_grounding_dino.py

Muc tieu:
- Quet toan bo anh trong dataset/images.
- Tu phat hien box cho motorbike, helmet, no_helmet.
- Tu tao tap anh ung vien no_helmet de ban review nhanh.
- Xuat pseudo COCO JSON de ban tham khao truoc khi annotate that.

Chay co ban:

```bash
uv run pseudo_label_with_grounding_dino.py
```

Ket qua:
- data/pseudo_labels/pseudo_image_scores.csv
- data/pseudo_labels/pseudo_instances_all.json
- data/pseudo_labels/pseudo_instances_no_helmet.json
- dataset/pseudo_review/no_helmet/train
- dataset/pseudo_review/no_helmet/val
- dataset/pseudo_review/no_helmet/test

Vi du chay chat hon de giam false positive:

```bash
uv run pseudo_label_with_grounding_dino.py \
	--box-threshold 0.33 \
	--text-threshold 0.28 \
	--no-helmet-min-score 0.48 \
	--motorbike-min-score 0.35 \
	--no-helmet-vs-helmet-ratio 1.15
```

Goi y su dung:
- Review truoc thu muc dataset/pseudo_review/no_helmet (nhanh nhat).
- Anh nao on thi giu lai de annotate.
- Anh nao sai thi xoa bo trong pseudo_review, khong anh huong den dataset goc.
- Dung pseudo JSON chi de tham khao, khong thay the nhan tay hoan toan.