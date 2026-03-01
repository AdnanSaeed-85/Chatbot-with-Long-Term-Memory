SELECT thread_id, metadata->>'step' as step, checkpoint->'channel_values'->>'response' as response
FROM checkpoints 
WHERE thread_id = '01' AND checkpoint->'channel_values'->>'response' != ''
ORDER BY checkpoint_id;