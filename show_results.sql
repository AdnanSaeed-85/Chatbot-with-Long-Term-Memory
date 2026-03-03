SELECT 
    thread_id,
    type,
    channel
FROM checkpoint_blobs
WHERE channel = 'messages'
ORDER BY thread_id;