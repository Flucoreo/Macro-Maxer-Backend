# Start Redis in the background
# (redis-server --daemonize yes 2>&1 | sed 's/^/[REDIS] /') &

# Start FastAPI app
# fastapi dev &
uvicorn app.app:app --reload --host 0.0.0.0 --port 8000 &

# Start worker script
export OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES
(rq worker "task_queue" 2>&1 | sed 's/^/[WORKER] /') &

# Wait for all background processes to finish
wait