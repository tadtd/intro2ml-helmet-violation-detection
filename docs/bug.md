# Pending Tasks for Camera & WebSocket Module

To make the pipeline production-ready, the following tasks must be completed to replace the current mock implementations and finish the feature:

## 1. Real ML Inference & Frame Processing
- [ ] **JPEG Decoding & Error Handling:** Use OpenCV or PIL to decode the binary `frame_bytes` received from the WebSocket into an image matrix. Add `try/except` logic to handle corrupted frames gracefully without crashing the socket loop.
- [ ] **YOLO Integration:** Load the actual YOLO/object detection model weights into memory on server start.
- [ ] **Run Inference:** Replace the random mock bounding box generator in `routes/camera.py` with a real call to `model.predict(decoded_frame)`.

## 2. Image Cropping & Storage Saves
- [ ] **Image Cropping Utility:** Write a function that takes the decoded frame and the `violation.motorbike.box` (or `non_helmet.box`) coordinates, adds some padding, and slices out the cropped image array.
- [ ] **Re-encode Crop:** Convert the cropped image array back into a JPEG byte stream.
- [ ] **Supabase Storage Upload:** Write the logic inside the asynchronous `save_violation()` task to upload this specific crop to your Supabase storage bucket and return the public URL.

## 3. Database Integration
- [ ] **Supabase SQL Schema:** Define the `violations` table in your database. It should include fields like `id`, `user_id`/`camera_id`, `timestamp`, `crop_image_url`, and `confidence_score`.
- [ ] **Database Insert:** Inside `save_violation()`, insert a new row into the `violations` table with the violation data and the returned image URL using the Supabase Python client.

## 4. Authentication
- [ ] **JWT Verification:** Replace the mock authentication check in `routes/camera.py`. Use a proper JWT decoding logic to validate the token sent by the Next.js frontend against your auth provider.

## 5. Advanced Deduplication
- [ ] **Time-Based Window:** Replace the simple `seen_violation_ids` set with a `ViolationWindow` class. This should expire track IDs after a set time (e.g., 30 seconds) so that if the same physical rider leaves and re-enters the frame later, they are correctly flagged again.

## 6. Frontend Improvements (Optional but Recommended)
- [ ] **Auto-Reconnect Logic:** Update `app/(app)/camera/page.tsx` so that if the WebSocket connection drops unexpectedly, it automatically attempts to reconnect every 3-5 seconds instead of permanently leaving the user on a "Disconnected" state.