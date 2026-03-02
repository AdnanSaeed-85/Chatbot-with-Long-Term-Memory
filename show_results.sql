SELECT type, blob
FROM checkpoint_blobs
WHERE thread_id = 'A1'
LIMIT 5;