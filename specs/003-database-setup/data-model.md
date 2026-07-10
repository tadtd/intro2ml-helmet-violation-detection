# Data Model: Database & Storage Schema

## Tables

### 1. `profiles`
Extension of `auth.users` containing role permissions and operational metadata.
- **id**: UUID (Primary Key, references `auth.users.id`)
- **role**: TEXT (Check constraint: IN ('admin', 'operator'))
- **display_name**: TEXT

### 2. `videos`
Tracker for uploaded video files and their processing state.
- **id**: UUID (Primary Key)
- **user_id**: UUID (References `profiles.id`)
- **status**: TEXT (e.g., 'pending', 'processing', 'done', 'failed')
- **error_message**: TEXT (Nullable)
- **progress_pct**: INTEGER (Check constraint: >= 0 AND <= 100)
- **processed_at**: TIMESTAMP WITH TIME ZONE (Nullable)
- **model_used**: TEXT (Check constraint: IN ('YOLO', 'RT-DETR', 'Faster R-CNN'))
- **created_at**: TIMESTAMP WITH TIME ZONE

### 3. `violations`
Record of detected non-helmet events and manual review decisions.
- **id**: UUID (Primary Key)
- **user_id**: UUID (References `profiles.id`)
- **video_id**: UUID (Nullable, references `videos.id` - allows live stream independence)
- **confidence**: NUMERIC (Check constraint: >= 0 AND <= 1)
- **reviewed**: BOOLEAN (Default: false)
- **reviewer_id**: UUID (Nullable, references `profiles.id`)
- **verdict**: TEXT (Nullable, Check constraint: IN ('confirmed', 'false positive', 'unclear'))
- **model_used**: TEXT
- **timestamp**: TIMESTAMP WITH TIME ZONE
- **created_at**: TIMESTAMP WITH TIME ZONE

## Storage Buckets

### 1. `videos` (Private)
- **Purpose**: Raw uploaded footage.
- **Path Convention**: `user_id/video_id/filename`
- **Lifecycle**: Files deleted after 3 days.

### 2. `violations` (Private)
- **Purpose**: High-resolution cropped images of violations.
- **Path Convention**: `video_id/violation_id/cropname` (or `live_stream/violation_id/cropname` if `video_id` is null)
- **Lifecycle**: Permanent retention.

## Row Level Security (RLS) Policies

All tables (`profiles`, `videos`, `violations`) have RLS enabled:
- **Operators**: `SELECT`, `UPDATE` where `user_id = auth.uid()`
- **Admins**: Bypass RLS (using role checks or direct boolean logic)
- **Backend Services**: Bypass RLS (implicitly handled via Supabase `service_role` key)
